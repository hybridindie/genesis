#!/bin/bash
set -euo pipefail

# Fail on unconditional skip/xfail in the test suites. A deliberate,
# environment-dependent skip is allowed when its line carries
# `skip-ok: <reason>` (see .claude/rules/testing.md).

ERRORS=0
ALLOW='skip-ok:'

check() {  # label, extended regex, paths...
  local label="$1" pattern="$2"; shift 2
  local roots=()
  for p in "$@"; do [[ -d $p ]] && roots+=("$p"); done
  (( ${#roots[@]} )) || return 0
  local hits
  hits=$(grep -rnE "$pattern" "${roots[@]}" 2>/dev/null | grep -v "$ALLOW" || true)
  if [[ -n $hits ]]; then
    printf '%s\n' "$hits"
    echo "ERROR: $label"
    ERRORS=$((ERRORS + 1))
  fi
}

{{#STACK_PYTHON}}
# pytest: skip/xfail markers and calls (skipif is conditional and allowed)
check "unconditional skip/xfail in Python tests" \
  'pytest\.mark\.(skip|xfail)\b|pytest\.(skip|xfail)\(' \
  "{{BACKEND_PATH}}/tests"
{{/STACK_PYTHON}}
{{#STACK_FRONTEND}}
# Jest/Vitest/Playwright: .skip, .todo, xit, xdescribe
check "skip/todo in frontend tests" \
  '\b(it|test|describe)\.(skip|todo)\(|\bx(it|describe|test)\(' \
  "{{FRONTEND_PATH}}/src" "{{FRONTEND_PATH}}/tests" "{{FRONTEND_PATH}}/e2e"
{{/STACK_FRONTEND}}
{{#STACK_GODOT}}
# GDScript test runners (GUT pending(), gdUnit skip)
check "skipped GDScript tests" '^\s*pending\(|skip_test\(' "{{GODOT_PATH}}/tests" "{{GODOT_PATH}}/test"
{{/STACK_GODOT}}
{{#STACK_RUST}}
check "#[ignore] in Rust tests" '#\[ignore' "{{RUST_PATH}}/src" "{{RUST_PATH}}/tests"
{{/STACK_RUST}}

if [[ $ERRORS -gt 0 ]]; then
  echo "FAIL: $ERRORS skip/xfail violation(s). Fix the test, or mark a genuine environment skip with 'skip-ok: <reason>'."
  exit 1
fi
echo "PASS: No forbidden skip patterns found."
