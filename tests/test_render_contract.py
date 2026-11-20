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
    rendered = (tmp_path / ".claude" / rel).read_text()
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
