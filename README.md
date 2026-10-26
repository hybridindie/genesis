# AI Harness Genesis

Constitutional AI instruction templates for **MCP servers, Python CLIs/libraries,
agent systems, FastAPI + React web apps, and Godot addons** — plus a machine setup
layer for the shell and the user-level agent rules.

OpenCode is the primary harness; Claude Code is supported through a thin import.

## Two layers

| Layer | Entry point | Installs into |
|-------|-------------|---------------|
| **System** (this machine) | `system/install.sh` | `~/.config/zsh`, `~/.config/opencode/AGENTS.md`, `~/.claude/{CLAUDE.md,settings.json}`, shared git config, optional Herdr/Zed |
| **Project** (one repo) | `install.sh`, `new-project.sh`, `/bootstrap-harness` | the target project's `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.opencode/`, `my-workflows.md` |

The end-to-end flow (new machine → new project → tailoring) is in
[`SYSTEM.md`](SYSTEM.md); the system layer's flags are in
[`system/README.md`](system/README.md).

## Archetypes

Each generated harness gets the nine core rules plus one profile's rules. The
profile is selected with `--profile` or inferred from the project.

| Profile | Selected for | Adds |
|---------|--------------|------|
| `mcp` | FastMCP / MCP SDK servers | Tool/resource/prompt contract, safety classes (`dry_run`/`confirm`), transport envelope/timeouts/reconnect, fake-peer contract tests |
| `python` | CLIs and libraries | Exit codes and stdout/stderr discipline, `--json`/`--dry-run`, uv packaging and entry points |
| `agent` | LangGraph / MLflow agent systems | Explicit graph/state, versioned prompts, executable evals, run budgets and reproducibility |
| `web` | FastAPI + React/TS + Postgres/Supabase | API/Pydantic contracts, SQL/migrations, React conventions, auth/input rules, plus the operational articles (rate limiting, GDPR, health, caching, budgets, production safety) |
| `godot` | Godot 4.4+ addons | `@tool` EditorPlugin lifecycle, command router, UndoRedo, JSON-safe serialization, headless tests, no editor blocking |

Auto-detection: `project.godot` → `godot`; `langgraph`/`mlflow` deps → `agent`;
`package.json` + `pyproject.toml` → `web`; `fastmcp`/`mcp` deps → `mcp`;
otherwise `python`.

## Install a project harness

From inside the project:

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/genesis/main/install.sh | bash
```

Or from a clone:

```bash
# new project: git init + auto-detect + render + next steps
./new-project.sh ../my-service

# existing project with an explicit profile
bash templates/scripts/bootstrap.sh --profile mcp --output-dir .
```

The interactive path is `/bootstrap-harness` in Claude Code or OpenCode.

### Post-bootstrap

```
bootstrap.sh     → render: placeholders, profile rules, generated rule index
      ↓
/harness-eval    → trim rules that do not fit, suggest missing ones,
                   keep the AGENTS.md rule index accurate
      ↓
/customize-harness → weave the project's domain and my-workflows.md into AGENTS.md
```

Both commands are idempotent and edit the rendered harness in place.

## What a project gets

- `AGENTS.md` — canonical project context with a **generated rule index**
- `CLAUDE.md` — thin `@AGENTS.md` + `@my-workflows.md` import, Claude-only notes
- `.claude/rules/` — core rules + the selected profile's rules
- `.claude/{commands,agents,skills,hooks}/` — profile-appropriate set
- `.opencode/{commands,agents,skills}/` — mirrored from the Claude sources
- `my-workflows.md` — your cross-project conventions (loaded automatically)
- `docs/harness-eval.md` — the evaluation prompt
- **no `.github/`** — projects own their CI workflows

## Context, not a rule dump

- OpenCode loads `AGENTS.md` + `my-workflows.md` and reads rules **on demand**
  through the rule index. It never globs `.claude/rules/`.
- Claude Code loads the thin `CLAUDE.md` and path-scoped rules.
- The rule index is generated from each rule's `read_when:` frontmatter, so a
  trimmed or added rule cannot leave a stale pointer. CI fails if the index and
  the rendered rules disagree.
- The web-only operational articles ship only for `web`; MCP, CLI, agent and
  Godot harnesses stay lean.

## Repository layout

```
system/                 machine layer (shell, global agent rules, git)
templates/
  _shared/
    AGENTS.md           canonical project context template (rule-index marker)
    core/articles/      rules shipped for every profile
    agents/ commands/ skills/ doctrine/
    profiles/
      mcp/ python/ agent/ web/ godot/
        articles/ commands/ agents/ skills/
    mirror-pairs.json   routing for agent/command/doctrine mirrors
    my-workflows.md
  claude-code/          Claude harness assets (hooks, thin CLAUDE.md)
  opencode/             OpenCode config (instructions + v2 permissions)
  scripts/              bootstrap, rule index, mirrors, detection, conditionals
new-project.sh          create a repo + render the harness
SYSTEM.md               machine → project flow
```

## Editing contract

- Edit shared content in `templates/_shared/core/` or the relevant
  `profiles/<profile>/` directory — never the generated OpenCode mirrors.
- Every rule needs `read_when:` frontmatter; the index and CI depend on it.
- Re-render and run the checks after changes:

```bash
for p in mcp python agent web godot; do
  bash templates/scripts/bootstrap.sh --profile "$p" --project-name Test --project-slug test --output-dir "/tmp/render-$p"
  python3 templates/scripts/check-harness-sync.py templates "/tmp/render-$p"
done
```

- Deeper reference: [`docs/agents-sections/`](docs/agents-sections/),
  [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md),
  [`INSTALL.md`](INSTALL.md), [`prompts-skills.md`](prompts-skills.md).

## License

MIT — see [`LICENSE`](LICENSE).
