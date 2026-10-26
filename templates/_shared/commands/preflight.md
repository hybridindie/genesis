---
description: Run local CI checks (lint, format, types, tests, gates) before pushing
---

Run the project's CI-equivalent checks locally and report the result.

## Steps

1. **Suite-health gate** — run `bash .claude/hooks/check-no-skipped-tests.sh`.
   If it reports a forbidden skip/xfail, fix that before anything else.

{{#PROFILE_WEB}}
2. **Backend lint/type** — `cd {{BACKEND_PATH}} && {{LINT_BACKEND_CMD}}` and
   `{{TYPE_BACKEND_CMD}}`. Report new errors only.
3. **Backend tests (quick)** — `cd {{BACKEND_PATH}} && {{TEST_BACKEND_CMD}} tests/contract tests/unit -x -q`.
4. **Frontend lint/type** — `cd {{FRONTEND_PATH}} && {{LINT_FRONTEND_CMD}}` and
   `{{TYPE_FRONTEND_CMD}}`. Report new errors only.
5. **Frontend tests (quick)** — `cd {{FRONTEND_PATH}} && {{TEST_FRONTEND_CMD}}`.
{{/PROFILE_WEB}}
{{#PROFILE_MCP}}
2. **Lint/type** — `uv run ruff check .` and `uv run mypy src/`. Report new errors only.
3. **Tests (quick)** — `uv run pytest tests/contract tests/unit -x -q`.
4. **Server smoke** — import the server module and list tools; confirm the
   expected core tools are registered and no import-time side effects occur.
{{/PROFILE_MCP}}
{{#PROFILE_PYTHON}}
2. **Lint/type** — `uv run ruff check .` and `uv run mypy src/`. Report new errors only.
3. **Tests (quick)** — `uv run pytest tests/unit -x -q`.
4. **CLI smoke** — `uv run {{PROJECT_SLUG}} --help` and one `--json` invocation.
{{/PROFILE_PYTHON}}
{{#PROFILE_AGENT}}
2. **Lint/type** — `uv run ruff check .` and `uv run mypy src/`. Report new errors only.
3. **Tests (quick)** — `uv run pytest tests/unit -x -q -m "not slow and not integration"`.
4. **Eval smoke** — run the smallest eval suite if one exists; report pass count
   and threshold.
{{/PROFILE_AGENT}}
{{#PROFILE_GODOT}}
2. **Format/lint** — `gdformat --check .` and `gdlint .` if gdtoolkit is installed.
3. **Headless tests** — `godot --headless --script res://tests/run_tests.gd`.
4. **Plugin smoke** — enable and disable the addon headlessly; confirm no errors
   and a clean exit.
{{/PROFILE_GODOT}}

## Harness gate

- `python3 .claude/hooks/check-project-drift.py --quiet` — AGENTS.md, rule index,
  command/skill lists, mirrors and versions still match the tree.
- `python3 .claude/hooks/check-secrets.py --all --quiet` — no credentials in the
  tracked or untracked tree.

## Output

| Check | Status | Details |
|-------|--------|---------|
| Suite health | PASS/FAIL | violation count |
| Harness | PASS/FAIL | drift/secret findings |
| Lint | PASS/FAIL | error count |
| Types | PASS/FAIL | new errors |
| Tests | PASS/FAIL | first failure |
| Smoke | PASS/FAIL | what failed |

If a check fails, list the exact errors and the fix. If all pass, say the tree
is ready to push.

**Hard stop:** a failing suite-health gate blocks the other checks; fix the
skip/xfail first.
