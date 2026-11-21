#!/usr/bin/env python3
"""Lint skill files for the deterministic execution contract.

Checks skill bodies (genesis `.agents/skills/<name>/SKILL.md` and shipped
`templates/_shared/`) for frontmatter, the required sections and token limits;
checks the `.claude/skills` pointers for frontmatter and a pointer to a shared
body; and fails when a generated pointer is stale (scripts/sync-skill-wrappers.py).

Usage:
  python3 scripts/lint-skills.py [paths...]

Exits 1 with a grouped report on violations.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BODY_GLOBS = [
    ".agents/skills/*/SKILL.md",
    "templates/_shared/skills/*/SKILL.md",
    "templates/_shared/stacks/*/skills/*/SKILL.md",
    "templates/_shared/packs/*/skills/*/SKILL.md",
]
WRAPPER_GLOBS = [
    ".claude/skills/*/SKILL.md",
]
REQUIRED = [
    "## Inputs",
    "## Deterministic Steps",
    "## LLM Judgment",
    "## Output",
    "## Stop Conditions",
    "## Token Budget",
]
MAX_BODY_LINES = 180
MAX_WRAPPER_LINES = 35
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SECTION = re.compile(r"^## (.+)$", re.MULTILINE)


def section_map(text: str) -> dict[str, str]:
    matches = list(SECTION.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[f"## {match.group(1)}"] = text[match.end():end].strip()
    return result


def check_body(path: Path, rel: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    if lines > MAX_BODY_LINES:
        errors.append(f"{rel}: {lines} lines > {MAX_BODY_LINES}")
    front = FRONTMATTER.match(text)
    if not front:
        errors.append(f"{rel}: missing frontmatter (name, description)")
    else:
        for key in ("name:", "description:"):
            if key not in front.group(1):
                errors.append(f"{rel}: frontmatter missing {key}")
    sections = section_map(text)
    for heading in REQUIRED:
        if heading not in sections:
            errors.append(f"{rel}: missing {heading}")
        elif not sections[heading]:
            errors.append(f"{rel}: empty {heading}")
    steps = sections.get("## Deterministic Steps", "")
    if steps and "`" not in steps:
        errors.append(f"{rel}: Deterministic Steps must name a command/path in backticks")
    command = re.compile(
        r"\b(?:python3|python|bash|sh|git|gh|jq|yq|rg|fd|uv|make|node|npm|pnpm|pytest|docker|kubectl)\b"
    )
    if steps and not command.search(steps):
        errors.append(f"{rel}: Deterministic Steps must invoke a script or CLI command")
    budget = sections.get("## Token Budget", "")
    if budget and not re.search(r"\d", budget):
        errors.append(f"{rel}: Token Budget must state a numeric limit")
    return errors


def check_wrapper(path: Path, rel: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    if lines > MAX_WRAPPER_LINES:
        errors.append(f"{rel}: {lines} lines > {MAX_WRAPPER_LINES}")
    front = FRONTMATTER.match(text)
    if not front:
        errors.append(f"{rel}: missing frontmatter")
    else:
        for key in ("name:", "description:"):
            if key not in front.group(1):
                errors.append(f"{rel}: frontmatter missing {key}")
    if ".agents/skills/" not in text and "templates/_shared/skills/" not in text:
        errors.append(f"{rel}: wrapper does not point at a shared skill body")
    return errors


def main() -> int:
    explicit = [Path(arg) for arg in sys.argv[1:]]
    if explicit:
        bodies = explicit
        wrappers: list[Path] = []
    else:
        bodies = [p for pattern in BODY_GLOBS for p in ROOT.glob(pattern)]
        wrappers = [p for pattern in WRAPPER_GLOBS for p in ROOT.glob(pattern)]

    errors: list[str] = []
    for path in sorted(bodies):
        rel = path.relative_to(ROOT)
        errors.extend(check_body(path, rel))
    for path in sorted(wrappers):
        rel = path.relative_to(ROOT)
        errors.extend(check_wrapper(path, rel))

    if not explicit:
        import subprocess
        sync = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync-skill-wrappers.py"), "--check"],
                              capture_output=True, text=True)
        if sync.returncode:
            errors.extend(line.removeprefix("STALE: ") for line in sync.stderr.splitlines() if line)
    for error in errors:
        print(f"SKILL-LINT: {error}", file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} skill contract issue(s).", file=sys.stderr)
        return 1
    print(f"PASS: {len(bodies)} skill bodies, {len(wrappers)} wrappers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
