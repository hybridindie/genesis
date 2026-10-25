# What It Does / Install / Key Flags

On-demand section — read when installing or bootstrapping a harness.

`templates/scripts/bootstrap.sh` reads `templates/_shared/` (canonical source) and renders three equivalent harnesses into a target project:

> There is also a **system layer** for the machine itself: `bash system/install.sh`
> renders the zsh config, the user-level `AGENTS.md`, and shared git settings into
> `$HOME`. See [`SYSTEM.md`](../../SYSTEM.md).

| Platform | Entry point | Rules location |
|----------|-------------|----------------|
| Claude Code | `CLAUDE.md` | `.claude/rules/`, `.claude/agents/`, `.claude/commands/` |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/instructions/`, `.github/agents/`, `.github/prompts/` |
| Opencode | `CLAUDE.md` | `.opencode/` |

## Install a harness into a project

```bash
# Auto-detect (recommended) — probes the target project and infers the right flags
bash templates/scripts/bootstrap.sh --auto-detect --output-dir /path/to/target/project

# Manual — supply values explicitly
bash templates/scripts/bootstrap.sh \
  --project-name "MyApp" \
  --project-slug "myapp" \
  --output-dir /path/to/target/project
```

When a project has no frontend, the bootstrap script automatically omits frontend rules, stores, and commands (`--mode backend-only`). When a project is an MCP server, it sets `--profile mcp`.

## Key flags

| Flag | Purpose |
|------|---------|
| `--auto-detect` | Inspect `--output-dir` for stack, versions, dependencies |
| `--mode backend-only` | Skip all frontend rules and placeholders |
| `--profile mcp` | MCP server profile (strips React/Vite/state-manager) |
| `--has-mlflow yes/no` | Include MLflow Prompt Registry rules |
| `--has-langgraph yes/no` | Include LangGraph agent rules |