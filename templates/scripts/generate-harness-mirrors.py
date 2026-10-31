#!/usr/bin/env python3
"""
Mirror the rendered Claude agents and commands into `.opencode/`.

Single source: `.claude/{agents,commands}/*.md`. Each OpenCode mirror has the
same body with OpenCode frontmatter.

Local edits are kept, using the same rules as the renderer:
- a missing mirror is created, unless harness.json records it (it was deleted
  on purpose);
- an existing mirror keeps its own frontmatter (OpenCode-only keys such as
  `agent:` or a bash allowlist survive); only its body is synced, and only if
  the file still matches its recorded hash or already has the same body;
- anything else is a local edit and is left alone (and reported).

Usage: python generate-harness-mirrors.py <output_dir>
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)", re.DOTALL)


def split(text: str) -> tuple[str | None, str]:
    m = FRONTMATTER.match(text)
    return (m.group(1), m.group(2)) if m else (None, text)


def field(fm: str | None, name: str) -> str:
    for line in (fm or "").splitlines():
        if line.startswith(f"{name}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def opencode_frontmatter(kind: str, claude_fm: str | None) -> str:
    description = field(claude_fm, "description").replace('"', '\\"')
    fm = "---\n"
    if description:
        fm += f'description: "{description}"\n'
    if kind == "agents":
        # OpenCode v2 ordered permissions: read-only subagent (edits and shell denied).
        fm += (
            "mode: subagent\n"
            "permissions:\n"
            "  - action: edit\n"
            '    resource: "*"\n'
            "    effect: deny\n"
            "  - action: shell\n"
            '    resource: "*"\n'
            "    effect: deny\n"
        )
    return fm + "---\n"


def mirror(out: Path, recorded: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    """Returns (written, kept, unchanged) mirror paths."""
    written: list[str] = []
    kept: list[str] = []
    unchanged: list[str] = []
    for kind in ("agents", "commands"):
        src_dir = out / ".claude" / kind
        if not src_dir.is_dir():
            continue
        for src in sorted(src_dir.glob("*.md")):
            rel = f".opencode/{kind}/{src.name}"
            dst = out / rel
            claude_fm, body = split(src.read_text(encoding="utf-8"))
            if not dst.exists():
                if rel in recorded:
                    kept.append(rel)  # deleted on purpose
                    continue
                content = opencode_frontmatter(kind, claude_fm) + body
            else:
                existing = dst.read_text(encoding="utf-8")
                fm, old_body = split(existing)
                if old_body == body:
                    unchanged.append(rel)
                    continue
                if recorded.get(rel) != hashlib.sha256(existing.encode()).hexdigest():
                    kept.append(rel)
                    continue
                content = (f"---\n{fm}\n---\n" if fm is not None else opencode_frontmatter(kind, claude_fm)) + body
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
            written.append(rel)
    return written, kept, unchanged


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate-harness-mirrors.py <output_dir>", file=sys.stderr)
        return 1
    out = Path(sys.argv[1])
    manifest = out / ".claude" / "harness.json"
    recorded = {}
    if manifest.is_file():
        recorded = json.loads(manifest.read_text(encoding="utf-8")).get("files") or {}
    written, kept, _ = mirror(out, recorded)
    print(f"OpenCode mirrors: {len(written)} written, {len(kept)} kept")
    for rel in kept:
        print(f"  kept {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
