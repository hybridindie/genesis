"""Render-level contracts: idempotence, untouched output, and the review marker."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import ROOT

RENDER = ROOT / "templates/scripts/render.py"


def run_render(out: Path, *args: str) -> None:
    subprocess.run(
        [sys.executable, str(RENDER), "--output-dir", str(out),
         "--project-name", "Contract", *args],
        check=True, capture_output=True, text=True,
    )


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_second_render_changes_nothing(tmp_path):
    run_render(tmp_path, "--stacks", "python,fastapi")
    first = tree_hashes(tmp_path)
    run_render(tmp_path, "--stacks", "python,fastapi")
    assert tree_hashes(tmp_path) == first


def test_rendered_python_matches_its_source(tmp_path):
    run_render(tmp_path, "--stacks", "python,fastapi")
    rel = "skills/create-migration/scripts/new_migration.py"
    rendered = (tmp_path / ".agents" / rel).read_text()
    source = (ROOT / "templates/_shared/stacks/fastapi" / rel).read_text()
    assert rendered == source


def test_render_leaves_no_unresolved_tags(tmp_path):
    run_render(tmp_path, "--stacks", "mcp,agent,fastapi,frontend", "--packs", "production")
    unresolved = re.compile(r"\{\{[#/]?[A-Z0-9_]+\}\}")
    for path in tmp_path.rglob("*"):
        if path.suffix in {".md", ".json", ".sh", ".py", ".yml", ".yaml"} and path.is_file():
            assert not unresolved.search(path.read_text(errors="ignore")), path.relative_to(tmp_path)


def test_review_marker_is_rendered_and_valid(tmp_path):
    run_render(tmp_path, "--stacks", "python")
    marker = tmp_path / ".opencodereview" / "rule.json"
    assert marker.is_file()
    data = json.loads(marker.read_text())
    paths = {rule["path"] for rule in data["rules"]}
    assert "**/.claude/**" in paths and "**/.opencode/**" in paths


def test_root_opencode_config_keeps_the_rest_of_the_directory(tmp_path):
    (tmp_path / "opencode.json").write_text(
        json.dumps({"instructions": ["AGENTS.md", "my-workflows.md"]})
    )
    run_render(tmp_path, "--stacks", "python")
    assert not (tmp_path / ".opencode" / "opencode.json").exists()
    assert (tmp_path / ".opencode" / "ruff.toml").is_file()
    assert (tmp_path / ".opencodereview" / "rule.json").is_file()


def _install_old_workflows(out: Path, body: bytes, recorded: bytes) -> None:
    """Simulate a pre-#66 install: my-workflows.md rendered and recorded."""
    (out / "my-workflows.md").write_bytes(body)
    with (out / ".claude" / "harness.sums").open("a", encoding="utf-8") as sums:
        sums.write(f"{hashlib.sha256(recorded).hexdigest()}  my-workflows.md\n")


def test_nothing_loads_my_workflows(tmp_path):
    run_render(tmp_path, "--stacks", "python")
    assert not (tmp_path / "my-workflows.md").exists()
    assert "my-workflows" not in (tmp_path / "CLAUDE.md").read_text()
    assert "my-workflows" not in (tmp_path / ".opencode" / "opencode.json").read_text()


def test_rerender_removes_an_unmodified_my_workflows(tmp_path):
    run_render(tmp_path, "--stacks", "python")
    _install_old_workflows(tmp_path, b"# My Workflows\n", b"# My Workflows\n")
    run_render(tmp_path, "--stacks", "python")
    assert not (tmp_path / "my-workflows.md").exists()


def test_rerender_keeps_an_edited_my_workflows(tmp_path):
    run_render(tmp_path, "--stacks", "python")
    _install_old_workflows(tmp_path, b"# My Workflows\nmine\n", b"# My Workflows\n")
    result = subprocess.run(
        [sys.executable, str(RENDER), "--output-dir", str(tmp_path), "--stacks", "python"],
        check=True, capture_output=True, text=True,
    )
    assert (tmp_path / "my-workflows.md").read_text() == "# My Workflows\nmine\n"
    assert "Kept my-workflows.md (edited)" in result.stderr


ALWAYS_ON_WORD_BUDGET = 1600  # core rules without `paths:` load in every session


def test_always_loaded_core_rules_stay_within_budget():
    words = 0
    for rule in sorted((ROOT / "templates/_shared/core/articles").glob("*.md")):
        text = rule.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        if "\npaths:" not in frontmatter:
            words += len(text.split())
    assert words <= ALWAYS_ON_WORD_BUDGET, f"{words} words load in every session"


def test_every_stack_and_pack_rule_is_path_scoped():
    """Stack rules load with the files they govern, not in every session."""
    unscoped = []
    for base in ("stacks", "packs"):
        for rule in sorted((ROOT / "templates/_shared" / base).glob("*/articles/**/*.md")):
            if "\npaths:" not in rule.read_text(encoding="utf-8").split("---", 2)[1]:
                unscoped.append(rule.relative_to(ROOT).as_posix())
    assert not unscoped, f"rules without paths: {unscoped}"
