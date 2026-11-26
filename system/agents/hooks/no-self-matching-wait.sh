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

# Newlines become `;` so a loop split over lines reads like a one-liner.
flat=$(printf '%s' "$cmd" | tr '\n' ';')

# The loop keyword must start a command (line start, or after ; & | ( or a
# quote), so prose that only mentions the construct is let through.
start="(^|[;&|({'\"])[[:space:]]*(while|until)[[:space:]]"
# pgrep with the f flag anywhere in its options: -f, -af, -fa, -u me -f, ...
pgrep_f='pgrep[^;]*[[:space:]]-[[:alpha:]]*f'
# 1. pgrep -f is the loop's condition (before the first `;`).
cond="${start}[^;]*${pgrep_f}"
# 2. pgrep -f in the body, breaking out on its status: `while :; do pgrep -f x || break; ...`.
body="${start}[^;]*;[[:space:]]*do[[:space:]].*${pgrep_f}[^;]*(\|\||&&)[[:space:]]*break"
if printf '%s\n' "$flat" | grep -Eq -e "$cond" -e "$body"; then
  jq -n '{hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "Blocked: a wait loop on `pgrep -f` matches its own shell (the pattern is in this command line), so it never exits. Wait on a PID instead (`tail --pid=$PID -f /dev/null`, or `while kill -0 $PID; do sleep 10; done`), use `pgrep -x <name>`, or run the long command itself in the background and wait for its notification. Bound any wait with `timeout`."
  }}'
fi
exit 0
