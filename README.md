# AI Harness Genesis

AI instruction templates for the projects I build: Python MCP servers, LLM
agent systems, FastAPI + React/Next web apps, Godot games and addons, and Rust
native code. Any mix in one repo. There is also a machine setup layer for the
shell and the user-level agent rules.

OpenCode and Claude Code are both first-class: `AGENTS.md` is canonical and
`CLAUDE.md` imports it.

## Two layers

| Layer | Entry point | Installs into |
|-------|-------------|---------------|
| **System** (this machine) | `system/install.sh` | `~/.config/zsh`, `~/.config/opencode/AGENTS.md`, `~/.claude/{CLAUDE.md,settings.json}`, shared git config, optional Herdr/Zed |
| **Project** (one repo) | `install.sh`, `new-project.sh`, `/bootstrap-harness` | the target project's `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.opencode/`, `my-workflows.md` |

The end-to-end flow (new machine → new project → tailoring) is in
[`SYSTEM.md`](SYSTEM.md); the system layer's flags are in
[`system/README.md`](system/README.md).

## Stacks and packs

Every project gets the core rules (architecture, testing, workflow, errors,
security, dependencies, CI, async, logging, docs). On top of that it gets
**every stack it uses**, detected from its manifests, plus any **opt-in
packs**.

| Stack | Detected from | Adds |
|---|---|---|
| `python` | `pyproject.toml` / `requirements.txt` | uv packaging, CLI behaviour |
| `mcp` | `mcp` / `fastmcp` dependency | tool contract, safety classes, transport, fake-peer tests |
| `agent` | LangGraph / LangChain / MLflow, or an LLM SDK plus `evals/` | explicit graph, versioned prompts, executable evals, budgets |
| `fastapi` | `fastapi` dependency | API contract, routes/services/repositories, SQL and migrations, web input security, backend architect, `/migration-check` |
| `frontend` | React / Next / Vue / Svelte in a `package.json` | frontend conventions, frontend architect, E2E assertion audit |
| `godot` | `project.godot` | GDScript conventions, main-thread async, headless tests |
| `godot-addon` | the project's own `addons/*/plugin.cfg` | `EditorPlugin` lifecycle, command router, UndoRedo, JSON-safe serialization |
| `rust` | `Cargo.toml` | fmt/clippy/test, no panics across FFI, `unsafe` justification |

`mcp`, `agent` and `fastapi` imply `python`; `godot-addon` implies `godot`.
Each stack's paths (e.g. `backend/`, `frontend/`, `godot/`) are detected and
used in path-scoped rules, commands and CI.

| Pack | For | Adds |
|---|---|---|
| `production` | services deployed with Docker/compose/k8s | deploy safety (health, shutdown, migrations, rollback), service limits (rate, cache, timeouts), privacy |
| `acd` | strict agent-generated delivery | spec artifacts, one-scenario sessions, `/start-session`, `/end-session`, `/fix` |

## Install a project harness

From inside the project:

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/genesis/main/install.sh | bash
```

Or from a clone:

```bash
# new project: git init + detect + render + next steps
./new-project.sh ../my-service --stacks mcp --scaffold

# existing project: detect everything
bash templates/scripts/bootstrap.sh --output-dir . --auto-detect

# see the plan without writing anything
python3 templates/scripts/render.py --output-dir . --auto-detect --plan

# extend or trim an installed harness later
bash templates/scripts/bootstrap.sh --output-dir . --add-stacks rust
bash templates/scripts/bootstrap.sh --output-dir . --remove-stacks frontend --packs production
```

The interactive path is `/bootstrap-harness` in Claude Code or OpenCode. It
shows the detected plan, lets you add or drop stacks and packs, renders and
validates.

Re-rendering never clobbers tailoring. `harness.json` records a hash for
every file the renderer writes. On the next render, a file that no longer
matches its hash is a local edit: it is kept and listed (`--force-overwrite`
replaces it). New rules are still added to the AGENTS.md index.

### After install

```
render           → core + stacks + packs, placeholders, generated rule index
      ↓
/harness-eval    → verify stacks against the code, trim rules that don't fit,
                   suggest missing ones
      ↓
/customize-harness → weave the project's domain and my-workflows.md into AGENTS.md
```

## What a project gets

- `AGENTS.md`: canonical context with the stack summary, the real commands,
  and a **generated rule index**.
- `CLAUDE.md`: a thin `@AGENTS.md` + `@my-workflows.md` import.
- `.claude/rules/`: core, stack and pack rules, read on demand.
- `.claude/{commands,agents,skills,hooks}/`, with mirrors in
  `.opencode/{commands,agents,skills}/`.
- `.claude/harness.json`: stacks, packs, paths and tooling, which the drift
  gate checks.
- `.githooks/`: tracked pre-commit/pre-push guardrails, installed once per
  clone.
- `.github/workflows/ci.yml` (or `.gitea/workflows/ci.yml`): one job per stack,
  only written when the project has no CI yet.
- `my-workflows.md`: your cross-project conventions. It is kept on re-render.
- `/ship-pr`: open, watch and triage a PR, then merge with a merge commit once
  it is green.

## Enforcement, not only advice

- **`pre-commit`** scans the staged diff for credentials, forbidden
  skips/xfails and project drift. **`pre-push`** scans the tree and runs
  `make check` when defined. Both wrap `.claude/hooks/guardrails.sh`, and CI
  calls the same script.
- **`check-project-drift.py`** fails when `AGENTS.md` no longer matches the
  tree. It covers the rule index, the command and skill lists, the mirrors, a
  thin `CLAUDE.md`, and the Python version. It also fails when a rule belongs
  to a stack or pack that `harness.json` doesn't declare, or when a declared
  one is missing its rules.
- **CI** runs the guardrails plus each stack's lint/type/test job.

## Repository layout

```
system/                  machine layer (shell, global agent rules, git)
templates/
  _shared/
    AGENTS.md            project context template (stack blocks, generated lists)
    core/articles/       rules for every project
    agents/ commands/ skills/ doctrine/   shared by every project
    stacks/<id>/         articles/ agents/ commands/ skills/ per stack
    packs/<id>/          opt-in rule packs
    ci/                  base.yml + jobs/<stack>.yml, composed per project
    githooks/
    my-workflows.md
  claude-code/           Claude harness assets (hooks, thin CLAUDE.md)
  opencode/              OpenCode config
  scripts/               render.py (renderer), inspect-project.py (detection),
                         rule index, mirrors, checks, scaffold
new-project.sh           create a repo + render the harness
scripts/lint-skills.py   enforce the skill contract
```

## Editing contract

- Edit shared content in `templates/_shared/`. Never edit generated OpenCode
  mirrors.
- Rule paths must be unique across core, stacks and packs. A stack adds rules
  and never replaces a core one.
- Every rule needs `read_when:` frontmatter.
- Each rule lives in one file; other files link to it rather than restating it.
- Re-render and check after changes (CI runs this matrix):

```bash
for s in python mcp agent fastapi,frontend godot,rust mcp,godot-addon; do
  out="/tmp/render-${s//,/-}"; rm -rf "$out"
  python3 templates/scripts/render.py --output-dir "$out" --project-name Test --stacks "$s" --packs production,acd
  python3 templates/scripts/check-harness-sync.py templates "$out"
  python3 "$out/.claude/hooks/check-project-drift.py" --root "$out"
done
```

- Deeper reference: [`docs/agents-sections/`](docs/agents-sections/),
  [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md),
  [`INSTALL.md`](INSTALL.md), [`prompts-skills.md`](prompts-skills.md).

## License

MIT — see [`LICENSE`](LICENSE).
