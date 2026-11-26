"""The wait-loop guard refuses self-matching `pgrep -f` loops and nothing else.

`system/agents/hooks/no-self-matching-wait.sh` is the shared check behind the
Claude Code PreToolUse hook and the OpenCode plugin.
"""

from __future__ import annotations

import json
import os
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
        "while :; do pgrep -f app >/dev/null || break; sleep 1; done",
        "timeout 60 bash -c 'until ! pgrep -f probe >/dev/null; do sleep 1; done'",
        'if [ -d "$d" ]; then while pgrep -f \'cargo build\' >/dev/null; do sleep 10; done; fi',
        "while :; do if ! pgrep -f x; then break; fi; sleep 1; done",
        "while :; do pgrep -f x || exit 1; done",
        "while :; do\n  pgrep -f app >/dev/null || break\n  sleep 1\ndone",
        "while :; do\n  pgrep -f app >/dev/null\n  || break\ndone",
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
        'git commit -m "guard until pgrep -f stalls"',
        'echo "watch: until pgrep -f build ends"',
        "while :; do pgrep -f app; sleep 1; done",
        "git status",
    ],
)
def test_allows_everything_else(command):
    assert decision(command) == "allow"


HARNESS = r"""
const { default: plugin } = await import(process.argv[2]);
let hook;
await plugin.setup({ tool: { hook: async (name, fn) => { if (name === "execute.before") hook = fn; } } });
const out = [];
for (const [tool, command] of JSON.parse(process.argv[3])) {
  const input = { command, description: "d" };
  const event = { tool, input };
  hook(event);
  out.push({ same: event.input === input, command: event.input.command });
}
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_the_opencode_plugin_rewrites_only_refused_shell_calls(tmp_path):
    hooks = tmp_path / ".agents/hooks"
    hooks.mkdir(parents=True)
    shutil.copy(HOOK, hooks / HOOK.name)
    harness = tmp_path / "harness.mjs"
    harness.write_text(HARNESS)
    loop = "until ! pgrep -f zz >/dev/null; do sleep 1; done"
    cases = [["shell", loop], ["bash", loop], ["shell", "git status"], ["read", loop]]
    run = subprocess.run(
        ["node", str(harness), PLUGIN.as_uri(), json.dumps(cases)],
        capture_output=True,
        text=True,
        check=True,
        env={"HOME": str(tmp_path), "PATH": os.environ["PATH"]},
    )
    out = json.loads(run.stdout)
    assert all(o["same"] for o in out), "the plugin must change event.input in place"
    changed = [o["command"] != command for (_, command), o in zip(cases, out)]
    assert changed == [True, True, False, False]
    refused = subprocess.run(["bash", "-c", out[0]["command"]], capture_output=True, text=True)
    assert refused.returncode == 1 and "pgrep -f" in refused.stderr
