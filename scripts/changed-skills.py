#!/usr/bin/env python3
"""Report which skills a branch changes, so their behavioural evals can run.

Behavioural evals are not scheduled: they run when a skill body actually
changes. This script answers "which ones?" from the diff.

Usage:
  python3 scripts/changed-skills.py --base origin/main
  python3 scripts/changed-skills.py --base origin/main --strict   # exit 2 on a gap

Exit codes: 0 report printed, 2 a changed skill has no eval case (--strict).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def skill_from_path(path: str) -> str | None:
    """The skill a changed path belongs to, or None when it is not a skill body."""
    if path.startswith((".claude/", ".opencode/")):
        return None  # generated wrappers, not the source body
    if path.startswith(".agents/skills/") and path.endswith(".md"):
        return Path(path).name.removesuffix(".md")
    if "/skills/" in path and (path.endswith("/SKILL.md") or "/scripts/" in path):
        tail = path.split("/skills/", 1)[1]
        return tail.split("/", 1)[0] or None
    return None


def changed_skills(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    found = {skill_from_path(line.strip()) for line in result.stdout.splitlines()}
    return sorted(skill for skill in found if skill)


def eval_cases(skill: str) -> list[Path]:
    case_dir = ROOT / "tests/evals" / "behaviour" / skill
    return sorted(case_dir.glob("*.md")) if case_dir.is_dir() else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--strict", action="store_true", help="exit 2 when a changed skill has no case")
    args = parser.parse_args()

    skills = changed_skills(args.base)
    if not skills:
        print("no skill bodies changed")
        return 0

    gaps = 0
    for skill in skills:
        cases = eval_cases(skill)
        print(f"{skill}: {len(cases)} behavioural case(s)")
        for case in cases:
            print(f"  - {case.relative_to(ROOT)}")
        if not cases:
            gaps += 1
    print(f"\n{len(skills)} skill(s) changed, {gaps} without cases")
    return 2 if args.strict and gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
