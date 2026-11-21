#!/usr/bin/env python3
"""
Measure a branch against the PR size budget (`.claude/rules/workflow.md`).

The budget counts what a reviewer reads: lines added + deleted in reviewable
files. Lockfiles, fixtures, snapshots, golden files, vendored and built output
are listed but not counted. An automated reviewer stops at a token budget, so
a PR past this size gets a partial review.

Usage:
  python3 pr_size.py [--base origin/main] [--max-lines 400] [--max-files 25]
                     [--exclude 'docs/api/**' ...]

Prints JSON. Exits 0 within budget, 1 over budget, 2 on a git error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fnmatch import fnmatch

MAX_LINES = 400
MAX_FILES = 25

EXCLUDE = (
    # lockfiles
    "*.lock", "*package-lock.json", "*pnpm-lock.yaml", "*npm-shrinkwrap.json", "*go.sum",
    # fixtures, snapshots, golden output, eval case copies
    "*/fixtures/*", "fixtures/*", "*__snapshots__/*", "*.snap", "*/golden/*", "golden/*",
    "*/evals/cases/*/files/*",
    # vendored and built output
    "vendor/*", "*/vendor/*", "*node_modules/*", "*/dist/*", "dist/*", "*.min.js", "*.min.css",
)


def excluded(path: str, extra: list[str] | None = None) -> bool:
    patterns = EXCLUDE + tuple(p.replace("**", "*") for p in extra or ())
    return any(fnmatch(path, p) for p in patterns)


def measure(numstat: str, max_lines: int = MAX_LINES, max_files: int = MAX_FILES,
            extra: list[str] | None = None) -> dict:
    counted: list[dict] = []
    skipped: list[str] = []
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if added == "-" or excluded(path, extra):  # binary, or not read line by line
            skipped.append(path)
            continue
        counted.append({"path": path, "lines": int(added) + int(deleted)})
    lines = sum(c["lines"] for c in counted)
    return {
        "lines": lines,
        "files": len(counted),
        "max_lines": max_lines,
        "max_files": max_files,
        "within_budget": lines <= max_lines and len(counted) <= max_files,
        "largest": sorted(counted, key=lambda c: -c["lines"])[:5],
        "excluded_files": len(skipped),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--max-lines", type=int, default=MAX_LINES)
    ap.add_argument("--max-files", type=int, default=MAX_FILES)
    ap.add_argument("--exclude", action="append", default=[], help="extra glob not counted")
    args = ap.parse_args()
    run = subprocess.run(["git", "diff", "--numstat", f"{args.base}...HEAD"], capture_output=True, text=True)
    if run.returncode != 0:
        print(json.dumps({"error": run.stderr.strip()}))
        return 2
    result = measure(run.stdout, args.max_lines, args.max_files, args.exclude)
    print(json.dumps(result, indent=2))
    return 0 if result["within_budget"] else 1


if __name__ == "__main__":
    sys.exit(main())
