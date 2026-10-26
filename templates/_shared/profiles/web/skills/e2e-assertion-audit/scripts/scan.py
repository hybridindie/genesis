#!/usr/bin/env python3
"""Deterministic E2E assertion scan. The model only triages the hits."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PATTERNS = {
    "no-op": re.compile(r"expect\(true\)\.toBe\(true\)|assert\s+1\s*==\s*1|toBeDefined\(\)|toBeTruthy\(\)"),
    "permissive": re.compile(r"toBeLessThan\(500\)|toBeGreaterThanOrEqual\(200\)|toContain\(\"a\"\)"),
    "fragile-selector": re.compile(r"click\(\"button\"\)|fill\(\"input\"|locator\(\"text=|getByText\("),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="tests/e2e")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    hits: list[dict[str, object]] = []
    files = 0
    if root.exists():
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx", ".py"}:
                continue
            files += 1
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(lines, 1):
                for category, pattern in PATTERNS.items():
                    if pattern.search(line):
                        hits.append({"category": category, "file": str(path), "line": lineno, "text": line.strip()})
    if args.json:
        print(json.dumps(hits, indent=2))
    else:
        for hit in hits:
            print(f"{hit['category']}\t{hit['file']}:{hit['line']}\t{hit['text']}")
    print(f"files={files} hits={len(hits)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
