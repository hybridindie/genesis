#!/bin/bash
# Warns (not blocks) when editing harness pointer files instead of .agents/,
# and when editing .agents/doctrine/ (load-bearing, referenced by many skills).
# Editable content should live in .agents/ (epic skills) or templates/_shared/
# (genesis). Pointer files in .opencode/ and .claude/ should stay thin.
#
# Input arrives on stdin as JSON with tool_input.file_path.
# Exit 0 with no output = no decision; normal flow continues.
# To surface a system reminder to Claude, print JSON with hookSpecificOutput.
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Skip if no file path (e.g. Write to a new file may still have one)
[ -z "$FILE" ] && exit 0

# Check if the file is in a harness pointer directory or is a doctrine module
CASE=$(echo "$FILE" | tr 'A-Z' 'a-z')
WARN=0
CONTEXT=""
case "$CASE" in
  */templates/claude-code/*|*/templates/opencode/*)
    WARN=1
    CONTEXT="Reminder: templates/claude-code/ and templates/opencode/ hold harness-specific template files. If the content is shared by both harnesses, edit templates/_shared/ instead. If it is genuinely harness-specific, proceed."
    ;;
  */.opencode/*|*/.claude/*)
    WARN=1
    CONTEXT="Reminder: editable content lives in .agents/. The file you are editing is a harness pointer. If you are changing canonical content, edit the corresponding file in .agents/ instead. If you are intentionally updating the pointer, proceed."
    ;;
  */.agents/doctrine/*)
    WARN=1
    CONTEXT="Reminder: .agents/doctrine/ files are load-bearing — multiple skills and rubrics reference them by path, so edits here propagate everywhere. Confirm the change is intended for all callers; if a rule needs to diverge per skill, it does not belong in shared doctrine."
    ;;
  */templates/_shared/doctrine/*)
    WARN=1
    CONTEXT="Reminder: templates/_shared/doctrine/ files are load-bearing — multiple articles and agents reference them by path, and they render into target projects at .claude/rules/doctrine/. Edits here propagate everywhere. Confirm the change is intended for all callers; if a rule needs to diverge per article, it does not belong in shared doctrine."
    ;;
esac

if [ "$WARN" -eq 1 ]; then
  jq -n --arg ctx "$CONTEXT" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: $ctx
    }
  }'
fi
exit 0