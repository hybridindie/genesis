"""stage_skills.py: the user-level install's path rewriting and file modes."""

from __future__ import annotations

import os
import subprocess
import sys

from conftest import ROOT

STAGE = ROOT / "system/agents/stage_skills.py"


def stage(tmp_path, *extra):
    out = tmp_path / "stage"
    subprocess.run([sys.executable, str(STAGE), str(ROOT), str(out), "/home/u", *extra],
                   check=True, capture_output=True, text=True)
    return out


def test_skill_references_point_at_the_same_harness_copy(tmp_path):
    out = stage(tmp_path)
    for harness, skills in (("claude", "/home/u/.claude/skills/"), ("opencode", "/home/u/.config/opencode/skills/")):
        text = (out / harness / "story-decomposer" / "SKILL.md").read_text()
        assert skills in text
        assert "/home/u/.agents/scripts/plan.py" in text
        assert " .agents/" not in text and "`.agents/" not in text


def test_shared_files_point_at_the_installed_harness(tmp_path):
    shell = ".agents/templates/epic/epic-shell.md"
    assert ".agents/skills/" in (ROOT / shell).read_text()     # the case this guards
    claude = (stage(tmp_path) / "agents/templates/epic/epic-shell.md").read_text()
    opencode = (stage(tmp_path / "o", "--shared-harness", "opencode")
                / "agents/templates/epic/epic-shell.md").read_text()
    assert "/home/u/.claude/skills/" in claude
    assert "/home/u/.config/opencode/skills/" in opencode and ".claude/skills" not in opencode


def test_scripts_keep_their_executable_bit(tmp_path):
    out = stage(tmp_path)
    for name in ("plan.py", "dispatch.py", "tracker.py", "validate_artifact.py"):
        assert os.access(ROOT / ".agents/scripts" / name, os.X_OK), f"{name} should be executable in the repo"
        assert os.access(out / "agents/scripts" / name, os.X_OK), f"staged {name} lost its exec bit"


def test_tests_fixtures_and_eval_cases_are_not_installed(tmp_path):
    out = stage(tmp_path)
    assert not list(out.rglob("tests")) and not list(out.rglob("fixtures")) and not list(out.rglob("cases"))
