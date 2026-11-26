"""The wait-loop guard refuses self-matching `pgrep -f` loops and nothing else.

`system/agents/hooks/no-self-matching-wait.sh` is the shared check behind the
Claude Code PreToolUse hook and the OpenCode plugin.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from conftest import ROOT

HOOK = ROOT / "system/agents/hooks/no-self-matching-wait.sh"
PLUGIN = ROOT / "system/agents/opencode-plugins/no-self-matching-wait/server.js"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="the hook needs jq")


def decision(command: str) -> str:
    out = subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if not out.strip():
        return "allow"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "command",
    [
        "until ! pgrep -f '/home/runner/.*(godot|cargo)' >/dev/null; do sleep 20; done",
        "while pgrep -af f10_bench.sh >/dev/null; do sleep 10; done",
        "cd x && until ! pgrep -f \"walk_falls.gd\" >/dev/null; do sleep 5; done; echo done",
        "x=1\nwhile pgrep -u me -f thing; do sleep 1; done",
        "while pgrep -fl thing\ndo sleep 1; done",
    ],
)
def test_refuses_a_self_matching_wait(command):
    assert decision(command) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "pgrep -af walk_falls | head",
        "while kill -0 123; do sleep 5; done",
        "until ! pgrep -x cargo; do sleep 5; done",
        "while true; do sleep 1; done; pgrep -f a",
        'gh issue create --body "loops like until x; then pgrep -f y"',
        "for i in 1 2; do pgrep -f a; done",
        "git status",
    ],
)
def test_allows_everything_else(command):
    assert decision(command) == "allow"


def test_the_opencode_plugin_shares_the_script():
    text = PLUGIN.read_text()
    assert "no-self-matching-wait.sh" in text
    assert '"execute.before"' in text
