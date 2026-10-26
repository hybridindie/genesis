#!/usr/bin/env python3
"""Scaffold a contract test from the skill's asset, without overwriting."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def pascal(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", value) if part)


def snake(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", choices=("backend", "frontend"), required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--path", required=True, help="HTTP path or module path")
    parser.add_argument("--method", default="get")
    parser.add_argument("--status", default="200")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        print(f"refusing to overwrite {out}", file=sys.stderr)
        return 1
    asset = ASSETS / ("backend_contract.py" if args.stack == "backend" else "frontend_contract.ts")
    text = asset.read_text(encoding="utf-8")
    replacements = {
        "__TARGET__": args.target,
        "__TARGET_PASCAL__": pascal(args.target),
        "__TARGET_SNAKE__": snake(args.target),
        "__TARGET_KEBAB__": snake(args.target).replace("_", "-"),
        "__PATH__": args.path,
        "__METHOD__": args.method.lower(),
        "__STATUS__": args.status,
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
