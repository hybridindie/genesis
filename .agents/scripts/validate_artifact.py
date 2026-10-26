#!/usr/bin/env python3
"""Validate the deterministic shape of Epic, story, task and AC artifacts.

Usage:
  python3 .agents/scripts/validate_artifact.py --kind epic <file>
  python3 .agents/scripts/validate_artifact.py --kind story <file>
  python3 .agents/scripts/validate_artifact.py --kind task <file>
  python3 .agents/scripts/validate_artifact.py --kind acceptance <file>
  ... --summary      print counts instead of the full report

Exit 0 on a valid shape. Semantic quality remains the skill's LLM judgment.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AC = re.compile(r"^\s*[-*]\s*(?:\*\*)?(AC\d+)(?:\*\*)?[:\s]", re.MULTILINE)
AC_BOX = re.compile(r"^\s*-\s*\[[ xX]\]\s*\*\*Given", re.MULTILINE)
EPIC_LABELS = [
    "**Why**",
    "**Outcome**",
    "**Scope**",
    "**Acceptance criteria**",
    "**Stories",
    "**Parallelization map**",
    "**Constraints",
    "**Risks",
    "**Success measures**",
    "**Definition of done**",
]
STORY_LABELS = [
    "**Acceptance criteria**",
    "**Parallelization**",
    "**Files**",
    "**Tasks**",
    "**Done when**",
]


def read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def count_ac(text: str) -> int:
    return len(AC.findall(text)) + len(AC_BOX.findall(text))


def check_epic(text: str) -> list[str]:
    errors = [f"missing {label}" for label in EPIC_LABELS if label not in text]
    acs = count_ac(text)
    if not 3 <= acs <= 8:
        errors.append(f"acceptance criteria count {acs} is outside 3–8")
    story_rows = [
        line for line in text.splitlines()
        if re.match(r"^\|\s*(?:#\d+|#TBD)\b", line)
    ]
    if not story_rows:
        errors.append("no story table rows")
    if "Shared contract" not in text:
        errors.append("parallelization map has no Shared contract")
    if "Wave 1" not in text:
        errors.append("parallelization map has no Wave 1")
    return errors


def check_story(text: str) -> list[str]:
    errors = [f"missing {label}" for label in STORY_LABELS if label not in text]
    if "**As a**" not in text and "**What**" not in text:
        errors.append("missing user-story frame (As a / What)")
    if "Part of #" not in text:
        errors.append("missing Part of #<epic>")
    if "Estimate:" not in text or "Wave:" not in text:
        errors.append("missing Estimate/Wave metadata")
    if count_ac(text) < 1:
        errors.append("no acceptance criteria")
    if "owns" not in text.lower():
        errors.append("no ownership scope")
    return errors


def check_task(text: str) -> list[str]:
    errors = []
    for heading in ("### Parallelization", "### Tasks", "### Dispatch notes"):
        if heading not in text:
            errors.append(f"missing {heading}")
    tasks = re.findall(r"^\s*-\s*\[[ xX]\]\s*\*\*T\d+", text, re.MULTILINE)
    if not tasks:
        errors.append("no T-numbered task checklist")
    if "verify" not in text.lower():
        errors.append("no verify step")
    if "owns" not in text.lower():
        errors.append("no ownership")
    return errors


def extract_acceptance(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s*(?:\*\*)?(AC\d+)(?:\*\*)?[:\s-]+(.*)$", line)
        if match:
            found.append((match.group(1), match.group(2).lstrip("*: -").strip()))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("epic", "story", "task", "acceptance"), required=True)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("path", help="artifact path, or - for stdin")
    args = parser.parse_args()
    text = read(args.path)

    if args.kind == "acceptance":
        criteria = extract_acceptance(text)
        if not criteria:
            print("FAIL: no AC-labelled criteria found", file=sys.stderr)
            return 1
        for label, body in criteria:
            weak = "" if re.search(r"\bwhen\b.*\bthen\b", body, re.I) else " (weak: no when/then)"
            print(f"{label}\t{body}{weak}")
        print(f"PASS: {len(criteria)} acceptance criteria extracted")
        return 0

    if args.kind == "epic":
        errors = check_epic(text)
        summary = f"ACs={count_ac(text)}"
    elif args.kind == "story":
        errors = check_story(text)
        summary = f"ACs={count_ac(text)}"
    else:
        errors = check_task(text)
        summary = f"tasks={len(re.findall(r'^\s*-\s*\[[ xX]\]\s*\*\*T\d+', text, re.MULTILINE))}"

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {args.kind} shape ({summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
