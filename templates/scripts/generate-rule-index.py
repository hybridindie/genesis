#!/usr/bin/env python3
"""
Build the AGENTS.md rule index from the rendered rule files.

Every rule article declares a `read_when:` field in its frontmatter. This script
reads the rendered `.claude/rules/**/*.md` (skipping doctrine), validates that
each file has one, and replaces the `<!-- RULE_INDEX -->` marker in AGENTS.md
with a table pointing at the files. OpenCode reads rules on demand through this
index; nothing globs the directory eagerly. It also fills `<!-- COMMAND_LIST -->`
and `<!-- SKILL_LIST -->` from the rendered commands and skills.

Usage: python generate-rule-index.py <output_dir>
"""

import re
import sys
from pathlib import Path

MARKER = "<!-- RULE_INDEX -->"


def frontmatter_field(text, field):
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    fm = m.group(1)
    for line in fm.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: generate-rule-index.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    out = Path(sys.argv[1])
    rules_dir = out / ".claude" / "rules"
    agents = out / "AGENTS.md"
    if not rules_dir.is_dir():
        print(f"ERROR: {rules_dir} not found", file=sys.stderr)
        sys.exit(1)
    if not agents.is_file():
        print(f"ERROR: {agents} not found", file=sys.stderr)
        sys.exit(1)

    rows = []
    missing = []
    for path in sorted(rules_dir.rglob("*.md")):
        rel = path.relative_to(rules_dir).as_posix()
        if rel.startswith("doctrine/"):
            continue
        read_when = frontmatter_field(path.read_text(encoding="utf-8"), "read_when")
        if not read_when:
            missing.append(rel)
            continue
        rows.append((rel, read_when))

    if missing:
        print("ERROR: rules missing read_when frontmatter:", file=sys.stderr)
        for rel in missing:
            print(f"  .claude/rules/{rel}", file=sys.stderr)
        sys.exit(1)

    table = ["| Rule file | Read when |", "|---|---|"]
    table += [f"| `.claude/rules/{rel}` | {read_when} |" for rel, read_when in rows]

    text = agents.read_text(encoding="utf-8")
    if MARKER not in text:
        print(f"ERROR: {agents} has no {MARKER} marker", file=sys.stderr)
        sys.exit(1)
    commands = sorted(p.stem for p in (out / ".claude" / "commands").glob("*.md"))
    skills = sorted(p.parent.name for p in (out / ".claude" / "skills").glob("*/SKILL.md"))
    text = text.replace(MARKER, "\n".join(table))
    text = text.replace("<!-- COMMAND_LIST -->", ", ".join(f"`/{c}`" for c in commands) or "none")
    text = text.replace("<!-- SKILL_LIST -->", ", ".join(f"`{s}`" for s in skills) or "none")
    agents.write_text(text, encoding="utf-8")
    print(f"Rule index: {len(rows)} rules, {len(commands)} commands, {len(skills)} skills")


if __name__ == "__main__":
    main()
