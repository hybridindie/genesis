---
description: Run the local equivalent of CI (lint, types, tests, harness gates) before pushing
---

Run the project's CI-equivalent checks locally and report the result. Run each
check even if an earlier one fails, except where noted.

## Checks

1. **Skips** — `bash .claude/hooks/check-no-skipped-tests.sh`. A forbidden
   skip/xfail is fixed first; the test results below don't count until it is.
2. **Harness** — `python3 .claude/hooks/check-project-drift.py --quiet` and
   `python3 .claude/hooks/check-secrets.py --all --quiet`.
{{#STACK_PYTHON}}
3. **Python**{{#PY_IN_SUBDIR}} (in `{{BACKEND_PATH}}/`){{/PY_IN_SUBDIR}} —
   `{{LINT_BACKEND_CMD}}`, `{{TYPE_BACKEND_CMD}}`, then
   `{{TEST_BACKEND_CMD}} -x -q{{#STACK_AGENT}} -m "not slow and not integration"{{/STACK_AGENT}}`.
{{#STACK_MCP}}
   MCP smoke: import the server module and list its tools; confirm the core
   tools register with no import-time side effects.
{{/STACK_MCP}}
{{#STACK_AGENT}}
   Eval smoke: run the smallest eval suite if one exists; report the pass
   count against its threshold.
{{/STACK_AGENT}}
{{/STACK_PYTHON}}
{{#STACK_FRONTEND}}
4. **Frontend** (in `{{FRONTEND_PATH}}/`) — `{{LINT_FRONTEND_CMD}}`,
   `{{TYPE_FRONTEND_CMD}}`, `{{TEST_FRONTEND_CMD}}`.
{{/STACK_FRONTEND}}
{{#STACK_GODOT}}
5. **Godot**{{#GODOT_IN_SUBDIR}} (in `{{GODOT_PATH}}/`){{/GODOT_IN_SUBDIR}} — `gdlint .`, then
   `{{GODOT_TEST_CMD}}`.
{{/STACK_GODOT}}
{{#STACK_RUST}}
6. **Rust**{{#RUST_IN_SUBDIR}} (in `{{RUST_PATH}}/`){{/RUST_IN_SUBDIR}} — `cargo fmt --check`,
   `cargo clippy --all-targets -- -D warnings`, `cargo test`.
{{/STACK_RUST}}

Report new lint/type errors only; pre-existing ones are listed once as a note.

## Output

| Check | Status | Details |
|-------|--------|---------|

For each failure give the exact error and the fix. If everything passes, say
the branch is ready to push.
