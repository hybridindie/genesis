# {{PROJECT_NAME}} — Agent Context

Canonical project context for every AI harness in this repo. OpenCode reads
this file natively; Claude Code imports it from `CLAUDE.md`. Don't duplicate it
elsewhere.

## How to use this harness

- **Rules load on demand.** `.claude/rules/**` is the single rule store; the
  [rule index](#rule-index) says which file to read for which task.
- **This harness is yours.** It was rendered for this project and is edited in
  place. `/harness-eval` trims rules that don't fit and suggests missing ones;
  `/customize-harness` adds the domain and `my-workflows.md` conventions here.
- **`my-workflows.md`** holds personal cross-project conventions and is
  loaded with this file.

## Project Overview

{{PROJECT_NAME}} — see `README.md` for scope, users, and non-goals.

## Invariants

Each line names the rule that defines it.

- Red test first; every bug fix ships a regression test; no unconditional
  skips (`testing.md`).
- Errors carry a code and a hint; no trace crosses a boundary
  (`error-handling.md`).
- Never bypass a gate (`--no-verify`, `|| true`); report what was skipped or
  unverified (`workflow.md`).

## Rule Index

<!-- RULE_INDEX -->

## Stack

{{#STACK_PYTHON}}
- **Python {{PYTHON_VERSION}}** with {{PY_PKG_MANAGER}}{{#PY_IN_SUBDIR}} in `{{BACKEND_PATH}}/`{{/PY_IN_SUBDIR}}; ruff, {{PY_TYPE_CHECKER}}, pytest.
{{/STACK_PYTHON}}
{{#STACK_MCP}}
- **MCP server** (FastMCP): typed tools/resources/prompts; server-side safety; one transport to the controlled process.
{{/STACK_MCP}}
{{#STACK_AGENT}}
- **Agent system**: explicit graph with typed state{{#HAS_LANGGRAPH}} (LangGraph){{/HAS_LANGGRAPH}}; versioned prompts; executable evals{{#HAS_MLFLOW}}; MLflow for runs and prompts{{/HAS_MLFLOW}}.
{{/STACK_AGENT}}
{{#STACK_FASTAPI}}
- **API**: FastAPI + Pydantic; data via {{DB_PROVIDER}}.
{{/STACK_FASTAPI}}
{{#STACK_FRONTEND}}
- **Frontend** in `{{FRONTEND_PATH}}/`: {{FRONTEND_STACK}}.
{{/STACK_FRONTEND}}
{{#STACK_GODOT}}
- **Godot {{GODOT_VERSION}}** project{{#GODOT_IN_SUBDIR}} in `{{GODOT_PATH}}/`{{/GODOT_IN_SUBDIR}}, GDScript; gdlint.
{{/STACK_GODOT}}
{{#STACK_GODOT_ADDON}}
- **Editor addon**: `@tool` `EditorPlugin`; one command router; every mutation through `EditorUndoRedoManager`.
{{/STACK_GODOT_ADDON}}
{{#STACK_RUST}}
- **Rust**{{#RUST_IN_SUBDIR}} in `{{RUST_PATH}}/`{{/RUST_IN_SUBDIR}}: cargo fmt, clippy, test.
{{/STACK_RUST}}

{{CUSTOM_TECH_STACK}}

## Key Commands

```bash
{{#STACK_PYTHON}}
# Python{{#PY_IN_SUBDIR}} (from {{BACKEND_PATH}}/){{/PY_IN_SUBDIR}}
{{PY_SYNC_CMD}}
{{LINT_BACKEND_CMD}}
{{TYPE_BACKEND_CMD}}
{{TEST_BACKEND_CMD}}
{{/STACK_PYTHON}}
{{#STACK_FRONTEND}}

# Frontend (from {{FRONTEND_PATH}}/)
{{LINT_FRONTEND_CMD}}
{{TYPE_FRONTEND_CMD}}
{{TEST_FRONTEND_CMD}}
{{/STACK_FRONTEND}}
{{#STACK_GODOT}}

# Godot{{#GODOT_IN_SUBDIR}} (from {{GODOT_PATH}}/){{/GODOT_IN_SUBDIR}}
gdlint .
{{GODOT_TEST_CMD}}
{{/STACK_GODOT}}
{{#STACK_RUST}}

# Rust{{#RUST_IN_SUBDIR}} (from {{RUST_PATH}}/){{/RUST_IN_SUBDIR}}
cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test
{{/STACK_RUST}}
```

## Workflow

Issue → red → green → `/preflight` → PR → review → merge. Details in
`.claude/rules/workflow.md`.

## Harness Map

| Capability | Claude Code | OpenCode |
|---|---|---|
| Project context | `CLAUDE.md` (`@AGENTS.md`) | `AGENTS.md` (this file) |
| Rules | `.claude/rules/**` (path-scoped) | `.claude/rules/**` (read via the index) |
| Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` |
| Subagents | `.claude/agents/*.md` | `.opencode/agents/*.md` (read-only) |
| Skills | `.claude/skills/*/SKILL.md` | `.opencode/skills/*/SKILL.md` |
| Gates | `.githooks/*` + `.claude/hooks/*` | CI + `/preflight` |

### Commands

<!-- COMMAND_LIST -->

### Skills

<!-- SKILL_LIST -->

## Project Constraints

{{CUSTOM_INSTRUCTIONS}}
