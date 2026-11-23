#!/usr/bin/env python3
"""Stage the epic-scoping skills for a user-level install.

  stage_skills.py <genesis-root> <stage-dir> <home> [--shared-harness claude|opencode]

Stages the plan-and-dispatch pipeline that genesis's scripts/pipeline.py
lists (the same skills and files every rendered project gets). Writes three
trees under <stage-dir>, which install.sh copies into place:

  agents/    .agents/{doctrine,templates,evals,scripts} -> <home>/.agents/
  claude/    full skills for ~/.claude/skills/<name>/
  opencode/  full skills for ~/.config/opencode/skills/<name>/

In the repo each skill lives once, in `.agents/skills/<name>/`, and its paths
are repo-relative (`.agents/...`). An installed skill runs from whatever repo
the user is in, so paths become absolute: skill-to-skill references point at
the copy for the same harness, everything else at <home>/.agents/. install.sh
writes each harness's copy only when that harness is installed, so a machine
with one harness gets one copy. Shared files (doctrine, templates) that name a
skill point at the copy of the harness given by --shared-harness, which
install.sh sets to an installed one. File modes are kept, so scripts stay
executable.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
from pathlib import Path

REPO_SKILLS = re.compile(r"(?<![\w./~-])\.agents/skills/")
REPO_PATH = re.compile(r"(?<![\w./~-])\.agents/")
HARNESS_DIRS = {"claude": ".claude/skills", "opencode": ".config/opencode/skills"}


def load_pipeline(root: Path):
    """genesis's scripts/pipeline.py: the one list of skills and files that ship."""
    path = root / "scripts" / "pipeline.py"
    spec = importlib.util.spec_from_file_location("pipeline", path) if path.is_file() else None
    if spec is None or spec.loader is None:
        sys.exit(f"stage_skills: {path} is missing; is {root} a genesis checkout?")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rewrite(text: str, home: str, skills_dir: str) -> str:
    text = REPO_SKILLS.sub(f"{home}/{skills_dir}/", text)
    return REPO_PATH.sub(f"{home}/.agents/", text)


def copy(src: Path, dst: Path, home: str, skills_dir: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.write_text(rewrite(src.read_text(encoding="utf-8"), home, skills_dir), encoding="utf-8")
    except UnicodeDecodeError:
        shutil.copyfile(src, dst)
    shutil.copymode(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root"); ap.add_argument("stage"); ap.add_argument("home")
    ap.add_argument("--shared-harness", choices=sorted(HARNESS_DIRS), default="claude",
                    help="whose skills folder shared files point at (an installed harness)")
    args = ap.parse_args()
    root, stage, home = Path(args.root), Path(args.stage), args.home.rstrip("/")
    src = root / ".agents"
    if stage.exists():
        shutil.rmtree(stage)
    pipeline = load_pipeline(root)
    for rel in pipeline.shared_files(root):
        copy(src / rel, stage / "agents" / rel, home, HARNESS_DIRS[args.shared_harness])
    for name in pipeline.skills(root):
        skill = src / "skills" / name
        if not (skill / "SKILL.md").is_file():
            print(f"error: {skill}/SKILL.md is missing", file=sys.stderr)
            return 1
        for harness, skills_dir in HARNESS_DIRS.items():
            for rel in pipeline.skill_files(root, name):
                copy(skill / rel, stage / harness / name / rel, home, skills_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
