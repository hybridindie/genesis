#!/usr/bin/env python3
"""Validate one rendered project with the shipped checkers and shell syntax."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], label: str) -> list[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        return [f"{label}: FAIL\n{detail}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genesis", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    genesis = Path(args.genesis).resolve()
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"target missing: {target}", file=sys.stderr)
        return 1

    errors: list[str] = []
    required = [
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/harness.json",
        ".claude/hooks/check-project-drift.py",
        ".githooks/pre-commit",
        ".githooks/pre-push",
    ]
    for rel in required:
        if not (target / rel).exists():
            errors.append(f"missing {rel}")

    errors += run(
        ["python3", str(target / ".claude/hooks/check-project-drift.py"), "--root", str(target)],
        "project drift",
    )
    errors += run(
        ["python3", str(genesis / "templates/scripts/check-harness-sync.py"), str(genesis / "templates"), str(target)],
        "harness sync",
    )
    for hook in sorted((target / ".claude/hooks").glob("*.sh")):
        errors += run(["bash", "-n", str(hook)], f"hook syntax {hook.name}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"PASS: rendered harness valid ({target})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
