"""Every skill genesis exposes to Claude Code has an OpenCode command too.

OpenCode skills have no slash path of their own, so a skill missing from
`.opencode/opencode.json` can only be reached by the model choosing it.
"""

from __future__ import annotations

import json

from conftest import ROOT


def test_every_claude_skill_has_an_opencode_command():
    skills = {p.parent.name for p in (ROOT / ".claude/skills").glob("*/SKILL.md")}
    commands = set(json.loads((ROOT / ".opencode/opencode.json").read_text())["commands"])
    assert skills - commands == set(), f"no OpenCode command for: {sorted(skills - commands)}"
