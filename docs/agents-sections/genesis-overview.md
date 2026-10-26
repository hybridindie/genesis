# What It Does / Install / Key Flags

On-demand section — read when installing or bootstrapping a harness.

`templates/scripts/bootstrap.sh` renders a project harness from
`templates/_shared/`: one canonical `AGENTS.md`, a thin `CLAUDE.md`, the core
rules, and one profile's rules. OpenCode is the primary harness; Claude Code
imports the same context.

> There is also a **system layer** for the machine itself: `bash system/install.sh`
> renders the zsh config, the user-level `AGENTS.md`, and shared git settings into
> `$HOME`. See [`SYSTEM.md`](../../SYSTEM.md).

| Platform | Entry point | Rules location |
|----------|-------------|----------------|
| OpenCode | `AGENTS.md` | `.claude/rules/` (read via the generated index) |
| Claude Code | `CLAUDE.md` (`@AGENTS.md`) | `.claude/rules/` (path-scoped) |

## Profiles

| Profile | For | Adds |
|---------|-----|------|
| `mcp` | FastMCP / MCP SDK servers | MCP contract, safety classes, transport, fake-peer tests |
| `python` | CLIs and libraries | Exit codes, `--json`/`--dry-run`, uv packaging |
| `agent` | LangGraph / MLflow systems | Graph/state, prompt versions, evals, run budgets |
| `web` | FastAPI + React + Postgres/Supabase | API, SQL, frontend, auth, operational articles |
| `godot` | Godot 4.4+ addons | `@tool` plugin, router, UndoRedo, JSON-safe values, headless tests |

Detection: `project.godot` → `godot`; `langgraph`/`mlflow` deps → `agent`;
`package.json` + `pyproject.toml` → `web`; `fastmcp`/`mcp` deps → `mcp`; else
`python`. An explicit `--profile` always wins.

## Install

```bash
# Auto-detect from the target project
bash templates/scripts/bootstrap.sh --auto-detect --output-dir /path/to/project

# Explicit profile
bash templates/scripts/bootstrap.sh --profile mcp --project-name MyServer \
  --project-slug my-server --output-dir /path/to/project
```

## Key flags

| Flag | Purpose |
|------|---------|
| `--profile mcp\|python\|agent\|web\|godot` | Choose the archetype (explicit wins over detection) |
| `--auto-detect` | Infer profile, names, versions, and tooling from the target |
| `--project-name`, `--project-slug` | Names used in the context files |
| `--backend-path`, `--frontend-path` | Directory layout (web; defaults `backend`/`frontend`) |
| `--has-mlflow`, `--has-langgraph` | Agent/web conditionals |
| `--db-provider`, `--state-manager`, versions | Web stack placeholders |
| `--custom-instructions`, `--custom-tech-stack` | Project-specific additions |
| `--output-dir` | Where to render (required) |

Web-only flags (`--db-provider`, frontend versions, `--tailwind`, …) are ignored
by the other profiles; MCP/CLI/Godot harnesses do not inherit frontend rules.
