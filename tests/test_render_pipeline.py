"""Every rendered project carries the plan-and-dispatch pipeline from `.agents/`."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT

RENDER = ROOT / "templates/scripts/render.py"
AGENTS = ROOT / ".agents"
PIPELINE = sorted(p.name for p in (AGENTS / "skills").iterdir()
                  if p.is_dir() and p.name != "bootstrap-harness")
SCRIPTS = sorted(p.name for p in (AGENTS / "scripts").glob("*.py"))


def run_render(out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RENDER), "--output-dir", str(out), "--project-name", "Pipe",
         "--stacks", "python", "--packs", ""],
        check=True, capture_output=True, text=True,
    )


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("render")
    run_render(out)
    return out


def test_pipeline_list_includes_the_newer_skills():
    assert {"plan-reviewer", "factory", "wave-dispatcher"} <= set(PIPELINE)


def test_render_contains_the_pipeline(rendered):
    for name in PIPELINE:
        assert (rendered / f".agents/skills/{name}/SKILL.md").is_file(), name
        pointer = (rendered / f".claude/skills/{name}/SKILL.md").read_text()
        assert f".agents/skills/{name}/SKILL.md" in pointer
    for name in SCRIPTS:
        assert (rendered / ".agents/scripts" / name).is_file(), name
    for src in (AGENTS / "doctrine").glob("*.md"):
        assert (rendered / ".agents/doctrine" / src.name).is_file(), src.name
    for src in (AGENTS / "templates").rglob("*"):
        if src.is_file():
            assert (rendered / ".agents" / src.relative_to(AGENTS)).is_file(), src
    for src in (AGENTS / "evals").glob("*.md"):
        assert (rendered / ".agents/evals" / src.name).is_file(), src.name


def test_test_and_genesis_only_files_are_not_rendered(rendered):
    assert not (rendered / ".agents/skills/bootstrap-harness").exists()
    assert not (rendered / ".claude/skills/bootstrap-harness").exists()
    for name in ("tests", "fixtures", "cases", "__pycache__"):
        assert not list((rendered / ".agents").rglob(name)), name
    assert not (rendered / ".agents/plan-constraints.yaml").exists()


def test_scripts_are_copied_byte_for_byte_and_stay_executable(rendered):
    assert "{{" in (AGENTS / "scripts/plan.py").read_text()  # the case this guards
    for name in SCRIPTS:
        dst = rendered / ".agents/scripts" / name
        assert dst.read_bytes() == (AGENTS / "scripts" / name).read_bytes(), name
        assert os.access(dst, os.X_OK), f"{name} lost its exec bit"


@pytest.mark.parametrize("script", ["dispatch.py", "plan.py"])
def test_scripts_run_inside_the_render(rendered, script):
    result = subprocess.run([sys.executable, f".agents/scripts/{script}", "--help"],
                            cwd=rendered, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower()


def test_rerender_keeps_edits_and_the_projects_constraints(tmp_path):
    run_render(tmp_path)
    edited = tmp_path / ".agents/doctrine/escalation.md"
    edited.write_text(edited.read_text() + "\nlocal note\n")
    constraints = tmp_path / ".agents/plan-constraints.yaml"
    constraints.write_text("constraints: []\n")
    result = run_render(tmp_path)
    assert edited.read_text().endswith("local note\n")
    assert ".agents/doctrine/escalation.md" in result.stdout  # reported as kept
    assert constraints.read_text() == "constraints: []\n"
    assert "plan-constraints" not in (tmp_path / ".claude/harness.sums").read_text()


def test_rerender_removes_a_pipeline_file_genesis_dropped(tmp_path):
    run_render(tmp_path)
    old = tmp_path / ".agents/scripts/retired.py"
    old.write_bytes(b"print('old')\n")
    with (tmp_path / ".claude/harness.sums").open("a", encoding="utf-8") as sums:
        sums.write(f"{hashlib.sha256(old.read_bytes()).hexdigest()}  .agents/scripts/retired.py\n")
    run_render(tmp_path)
    assert not old.exists()


def test_render_passes_the_checks_and_they_catch_a_broken_pipeline(tmp_path):
    run_render(tmp_path)
    drift = [sys.executable, str(tmp_path / ".claude/hooks/check-project-drift.py"), "--root", str(tmp_path)]
    sync = [sys.executable, str(ROOT / "templates/scripts/check-harness-sync.py"),
            str(ROOT / "templates"), str(tmp_path)]
    assert subprocess.run(drift, capture_output=True).returncode == 0
    assert subprocess.run(sync, capture_output=True).returncode == 0
    (tmp_path / ".agents/doctrine/escalation.md").unlink()
    (tmp_path / ".agents/scripts/plan.py").chmod(0o644)
    result = subprocess.run(drift, capture_output=True, text=True)
    assert result.returncode == 1
    assert "escalation.md, which is missing" in result.stderr and "plan.py is not executable" in result.stderr
    result = subprocess.run(sync, capture_output=True, text=True)
    assert result.returncode == 1 and "pipeline file not rendered: .agents/doctrine/escalation.md" in result.stderr
