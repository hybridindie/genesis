#!/usr/bin/env bash
# Refuse wait loops whose condition is `pgrep -f`. Shared by both harnesses:
# Claude Code runs it as a PreToolUse hook on Bash; the OpenCode plugin
# plugins/no-self-matching-wait/server.js pipes it the same JSON for the shell tool.
#
# Agents run each command as `<shell> -c '<the whole command>'`, so the
# pattern given to `pgrep -f` is also in the waiting shell's own command line.
# pgrep skips itself but not its parent shell: the loop always finds a match
# and never exits, and the agent waiting on it stalls (2026-11-25: two factory
# agents stuck about 6 hours on `until ! pgrep -f ...`).
#
# Input: {"tool_input":{"command":"..."}} on stdin.
# Output: a PreToolUse deny decision on stdout when the command is refused,
# nothing otherwise. Exit 0 either way; without jq it allows (exit 0).
set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0

cmd=$(jq -r '.tool_input.command // empty')
[ -n "$cmd" ] || exit 0

# `while`/`until` whose condition (up to the first `;` or newline) calls
# pgrep with the f flag anywhere in its options: -f, -af, -fa, -u me -f, ...
loop='(^|[^[:alnum:]_])(while|until)[[:space:]][^;]*pgrep[^;]*[[:space:]]-[[:alpha:]]*f'
if printf '%s\n' "$cmd" | grep -Eq "$loop"; then
  jq -n '{hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "Blocked: a wait loop on `pgrep -f` matches its own shell (the pattern is in this command line), so it never exits. Wait on a PID instead (`tail --pid=$PID -f /dev/null`, or `while kill -0 $PID; do sleep 10; done`), use `pgrep -x <name>`, or run the long command itself in the background and wait for its notification. Bound any wait with `timeout`."
  }}'
fi
exit 0
