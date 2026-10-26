# {{PROJECT_NAME}} — Agent Context

Canonical project context for every AI harness in this repo. OpenCode reads this
file natively; Claude Code imports it from `CLAUDE.md` (`@AGENTS.md`). Do not
duplicate this content elsewhere.

## How to use this harness

- **Rules are on demand.** `.claude/rules/**` is the single rule store. The
  [rule index](#rule-index) says which file to read for which task — open that
  file instead of guessing or loading the directory.
- **This harness is yours.** It was rendered for this project and is edited in
  place. There is no `templates/` directory here.
- **Customize with** `/harness-eval` (trim rules that do not fit, suggest missing
  ones) and then `/customize-harness` (weave the domain and `my-workflows.md`
  into this file). Both are idempotent.
- **`my-workflows.md`** holds cross-project conventions (commits, tooling,
  direnv, permissions). It is loaded automatically and is the source of truth
  for those conventions.

## Project Overview

{{PROJECT_NAME}} — see `README.md` for scope, users, and non-goals.

## Invariants

- **Tests are a binary signal.** The suite is green and trusted, or it is a
  liar. Zero failing tests, zero unchecked skips, deterministic runs.
- **Every bug fix ships a regression test.**
- **Structured errors only.** Stable codes, actionable hints, no stack traces
  across a boundary.
- **Report honestly.** Name what was skipped, aborted, or left unverified.
- **Never bypass a gate** (`--no-verify`, `|| true`, disabled checks).

## Rule Index

<!-- RULE_INDEX -->

## Stack

{{#PROFILE_WEB}}
- Backend: Python {{PYTHON_VERSION}}, FastAPI {{FASTAPI_VERSION}}, Pydantic
- Database: PostgreSQL 17 ({{DB_EXTENSIONS}}), {{DB_PROVIDER}} client (no SQLAlchemy)
- Frontend: React {{REACT_VERSION}}, TypeScript {{TYPESCRIPT_VERSION}}, Vite {{VITE_VERSION}}, {{STATE_MANAGER}}
- Tests: pytest + httpx; Vitest + MSW; {{E2E_TOOL}} for E2E
{{#HAS_MLFLOW}}- MLflow for experiment tracking and the prompt registry{{/HAS_MLFLOW}}
{{#HAS_LANGGRAPH}}- LangGraph for agent orchestration{{/HAS_LANGGRAPH}}
{{/PROFILE_WEB}}
{{#PROFILE_MCP}}
- Python {{PYTHON_VERSION}} + FastMCP; async tools/resources/prompts
- Transport: stdio and/or Streamable HTTP; one controlled process behind a
  single bridge
- Tests: pytest (contract tests against a fake peer)
{{/PROFILE_MCP}}
{{#PROFILE_PYTHON}}
- Python {{PYTHON_VERSION}} + uv; `src/` layout with console entry points
- Tests: pytest; fakes and golden files for external systems
{{/PROFILE_PYTHON}}
{{#PROFILE_AGENT}}
- Python {{PYTHON_VERSION}} + uv; explicit graph/flow with a typed state schema
- Prompt registry + executable evals; bounded steps, tokens, and wall clock
{{#HAS_MLFLOW}}- MLflow for experiment tracking and prompt versioning{{/HAS_MLFLOW}}
{{#HAS_LANGGRAPH}}- LangGraph for orchestration and checkpointing{{/HAS_LANGGRAPH}}
{{/PROFILE_AGENT}}
{{#PROFILE_GODOT}}
- Godot 4.4+ addon in GDScript (`@tool`), installed via Project Settings → Plugins
- Every mutation goes through `EditorUndoRedoManager`; the dock is read-only
- Tests: headless Godot (`godot --headless`) with fixture scenes
{{/PROFILE_GODOT}}

## Key Commands

{{#PROFILE_WEB}}
```bash
# Backend
cd {{BACKEND_PATH}} && uv run pytest
cd {{BACKEND_PATH}} && uv run ruff check .
cd {{BACKEND_PATH}} && uv run mypy src/

# Frontend
cd {{FRONTEND_PATH}} && {{TEST_FRONTEND_CMD}}
cd {{FRONTEND_PATH}} && npm run lint && npm run type-check
```
{{/PROFILE_WEB}}
{{#PROFILE_MCP}}
```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
uv run python -m {{PROJECT_SLUG}}
```
{{/PROFILE_MCP}}
{{#PROFILE_PYTHON}}
```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
uv run {{PROJECT_SLUG}} --help
```
{{/PROFILE_PYTHON}}
{{#PROFILE_AGENT}}
```bash
uv sync --all-extras
uv run pytest -m "not slow and not integration"
uv run ruff check .
uv run mypy src/
```
{{/PROFILE_AGENT}}
{{#PROFILE_GODOT}}
```bash
# Headless test run (adjust the script path to the project layout)
godot --headless --script res://tests/run_tests.gd

# Lint/format if the project ships gdtoolkit
gdformat . && gdlint .
```
{{/PROFILE_GODOT}}

{{CUSTOM_TECH_STACK}}

## Workflow

Issue → failing test → minimal green → local preflight → PR → review → merge.
One concern per PR; link the issue; do not bundle refactors or dependency bumps.
Run `/preflight` before pushing; never bypass a hook.

## Harness Map

| Capability | Claude Code | OpenCode |
|---|---|---|
| Project context | `CLAUDE.md` (`@AGENTS.md`) | `AGENTS.md` (this file) |
| Rules | `.claude/rules/**` (path-scoped) | `.claude/rules/**` (read via the index) |
| Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` |
| Subagents | `.claude/agents/*.md` | `.opencode/agents/*.md` (read-only) |
| Skills | `.claude/skills/*/SKILL.md` | `.opencode/skills/*/SKILL.md` |
| Gates | `.claude/hooks/*.sh` | CI + `/preflight` |

### Commands

`/preflight`, `/start-session`, `/end-session`, `/fix`, `/migration-check`,
`/harness-eval`, `/graphify`, `/ship-pr`.

### Skills

`customize-harness`, `gen-contract-test`, `create-migration`,
`test-hygiene-scanner`, `e2e-assertion-audit`.

## Agent Notes

{{#PROFILE_MCP}}
- The tool surface is the product: typed input/output, stable names, and
  agent-facing descriptions. Read `.claude/rules/mcp-contract.md` before adding
  a tool.
- Safety is server-side: `dry_run` for mutations, `confirm=True` for destructive
  actions, preconditions before side effects.
- The transport is the only path to the controlled process; every request has a
  timeout and a correlated `id`.
{{/PROFILE_MCP}}
{{#PROFILE_GODOT}}
- `@tool` on every script; set up and tear down cleanly in `_enter_tree` /
  `_exit_tree`.
- One command router, one handler per command, UndoRedo on every mutation.
- Never block the editor thread; JSON-safe values only, converted in one
  `type_coerce` helper.
{{/PROFILE_GODOT}}
{{#PROFILE_AGENT}}
- Prompts are versioned and loaded by name; runs record seed/model/prompt/tool
  versions.
- Enforce step, token/cost, and wall-clock budgets. Evals are executable, not
  prose.
{{/PROFILE_AGENT}}
{{#PROFILE_WEB}}
- Routes delegate; services decide; repositories own persistence.
- Validate input, return typed models, and authenticate before side effects.
{{/PROFILE_WEB}}
{{#PROFILE_PYTHON}}
- Data on stdout, logs on stderr, documented exit codes, `--json` for machines.
- One version source in `pyproject.toml`; keep the lockfile committed.
{{/PROFILE_PYTHON}}

## Project Constraints

{{CUSTOM_INSTRUCTIONS}}

## Glossary

- **Contract test**: validates an externally visible interface, schema, or protocol
- **Deterministic**: same input → same output (time and randomness controlled)
- **Idempotent**: repeated identical invocations produce the same final state
- **Envelope**: structured wrapper for a result or a structured error
