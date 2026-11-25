# AI Harness Genesis

AI instruction templates for the projects I build: Python MCP servers, LLM
agent systems, FastAPI + React/Next web apps, Godot games and addons, and Rust
native code. Any mix in one repo. There is also a machine setup layer for the
shell and the user-level agent rules.

OpenCode and Claude Code are both first-class: `AGENTS.md` is canonical and
`CLAUDE.md` imports it.

It also hosts the **Epic Scoping Skills**, which turn source material into a
planned Epic and run the plan with parallel agents (see
[Plan and run work](#plan-and-run-work)).

## Two layers

| Layer | Entry point | Installs into |
|-------|-------------|---------------|
| **System** (this machine) | `system/install.sh` | `~/.config/zsh`, `~/.config/opencode/AGENTS.md`, `~/.claude/{CLAUDE.md,settings.json}`, shared git config, optional Herdr/Zed |
| **Project** (one repo) | `install.sh`, `new-project.sh`, `/bootstrap-harness` | the target project's `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.opencode/` |

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

Re-rendering never clobbers tailoring. `.claude/harness.sums` records a
sha256 for every file the renderer writes. On the next render, a file that no longer
matches its hash is a local edit: it is kept and listed (`--force-overwrite`
replaces it). A rendered file you deleted stays deleted. New rules are still
added to the AGENTS.md index.

### After install

```
render           → core + stacks + packs, placeholders, generated rule index
      ↓
/harness-eval    → verify stacks against the code, trim rules that don't fit,
                   suggest missing ones
      ↓
/customize-harness → weave the project's domain into AGENTS.md
```

## What a project gets

- `AGENTS.md`: canonical context with the stack summary, the real commands,
  and a **generated rule index**.
- `CLAUDE.md`: a thin `@AGENTS.md` import.
- `.claude/rules/`: core, stack and pack rules, read on demand.
- `.claude/{commands,agents,skills,hooks}/`, with mirrors in
  `.opencode/{commands,agents,skills}/`.
- `.claude/harness.json`: stacks, packs, paths and tooling, which the drift
  gate checks, plus ship-pr's `merge_policy`, which re-renders keep. A tailored repo that covers a stack under its own rule name
  says so with `rule_aliases` (`{"rust": "native.md"}`).
- `.claude/harness.sums`: sha256 of each rendered file, in `sha256sum`
  format, so a re-render can tell your edits apart from its own output.
- `.githooks/`: tracked pre-commit/pre-push guardrails, installed once per
  clone.
- `.github/workflows/ci.yml` (or `.gitea/workflows/ci.yml`): one job per stack,
  only written when the project has no CI yet.
- `/ship-pr`: open, watch and triage a PR on GitHub or Gitea (the forge comes
  from `origin`, as for the tracker), then merge once it is green, as
  `merge_policy` in `harness.json` allows: `merge` is `when-green` (default)
  or `never` (stop at "ready to merge" for a person), `method` is `merge`
  (default), `squash` or `rebase`, and a PR touching an irreversible path
  (migrations, deploy, infra) always waits for a person.
- The plan-and-dispatch pipeline from genesis's `.agents/` (epic/story/task
  skills, plan-reviewer, wave-dispatcher, factory, with their scripts,
  doctrine, templates and rubrics), at the same paths. Scripts need `python3`,
  plus `uv` or PyYAML. `.agents/plan-constraints.yaml` stays yours.

## Enforcement, not only advice

- **`pre-commit`** scans the staged diff for credentials, forbidden
  skips/xfails and project drift. **`pre-push`** scans the tree and runs
  `make check` when defined. Both wrap `.claude/hooks/guardrails.sh`, and CI
  calls the same script.
- **`check-project-drift.py`** fails when `AGENTS.md` no longer matches the
  tree. It covers the rule index, the command and skill lists, the mirrors, a
  thin `CLAUDE.md`, and the Python version. It also fails when a rule belongs
  to a stack or pack that `harness.json` doesn't declare, and warns when a
  declared one has no rules.
- **CI** runs the guardrails plus each stack's lint/type/test job.

## Plan and run work

The Epic Scoping Skills live in `.agents/` and work in both harnesses:

```
/epic-composer     source notes → Epic issue (outcome, ACs, story map in waves)
/story-decomposer  Epic → story issues (owns, depends_on, shared contract)
/plan-reviewer     second-model verdict on a plan before dispatch
/task-decomposer   story → parallel tracks with disjoint file ownership
/wave-dispatcher   run each runnable track in its own worktree, check, merge
/ship-pr           open the PR, address the review, merge once green (per merge_policy)
/factory           run all of the above for each approved Epic, unattended
```

Set **`PLAN_REVIEW_MODEL`** to the plan reviewer's model, a cheap one that
differs from the coding model (the fallback, `opencode/big-pickle`, is a free
OpenCode Zen model that may be retired).

Every plan is a fenced `agent-plan` YAML block that `.agents/scripts/plan.py`
validates. `.agents/scripts/dispatch.py` does the git work for the
dispatcher:

- It checks each track's diff against the paths it owns and runs its verify
  command, after a baseline run that catches a check that can't fail.
- It retries a failed track at most three times, then sends it back to
  replanning.
- It gates merges by blast radius: `contained`, `wide`, or `irreversible`,
  which needs a person's approval.
- It keeps each unit's attempts and rollbacks for review.

Lessons from confirmed failures go in `.agents/plan-constraints.yaml` and
reach later plans. The full flow is in
[`docs/agents-sections/workflow.md`](docs/agents-sections/workflow.md), and
the usage guide is [`prompts-skills.md`](prompts-skills.md).

### The factory

Start it by typing `/factory` (or "start the factory") in a session. It runs in
that session, in the foreground, so you can watch each round and step in. It
works every approved `Epic:` issue that is open when it starts, oldest first,
one at a time, then exits; it never waits for new Epics: story-decomposer → plan-reviewer → task-decomposer →
wave-dispatcher with ship-pr. The full behaviour is in
[`.agents/skills/factory/SKILL.md`](.agents/skills/factory/SKILL.md).

Labels on the Epic (story issues get `factory:needs-input` too):

| Label | Set by | Meaning |
|---|---|---|
| `factory:drafted` | the drafter | an agent wrote this Epic; it waits for a person's approval |
| `factory:approved` | a person | a drafted Epic may run |
| `factory:auto-approve` | a person | run drafted Epics without a per-Epic approval |
| `factory:running` | the factory | picked up and in progress |
| `factory:needs-input` | the factory | stopped on a question only a person can answer |
| `factory:over-budget` | the factory | the token budget ran out; paused |
| `factory:shipped` | the factory | every story merged |

An Epic without `factory:drafted` counts as approved. The factory never sets
the two approval labels; `tracker.py` refuses them.

**Escalation ladder** ([`.agents/doctrine/escalation.md`](.agents/doctrine/escalation.md)):
every loop gets three attempts, then a written diagnosis, then exactly one rung:
one informed `attempt`, one `replan`, or `needs-input` for a person. Only a
confirmed cause may take `attempt` or `replan`. Escalating a unit blocks only
that unit and those that depend on it.

**Budget:** 5,000,000 tokens per Epic by default (`--limit` to change), tracked
by `.agents/scripts/budget.py` from each subagent's reported spend. At 80% the
factory posts one warning comment on the Epic; at 100% it starts nothing new,
adds `factory:over-budget` and waits for you to raise the limit or remove the
label.

## Repository layout

The file tree and how rendering works are in
[`docs/agents-sections/source-structure.md`](docs/agents-sections/source-structure.md).

## Developing genesis

```bash
uv run --with pytest --with pyyaml pytest -q tests .agents/scripts/tests   # unit + eval tests
python3 scripts/lint-skills.py              # skill bodies follow the execution contract
python3 scripts/sync-skill-wrappers.py      # regenerate .claude/skills pointers (--check to verify)
bash templates/claude-code/.claude/hooks/check-primitive-drift.sh   # .claude ↔ .opencode mirrors
```

CI (`.github/workflows/validate-templates.yml`) runs the tests and the skill
lint, renders a matrix of stack combinations, and checks each render. A PR stays within the size
budget of 400 lines and 25 files (`pr_size.py`, run by ship-pr).

## Editing contract

- Edit shared content in `templates/_shared/`. Never edit generated OpenCode
  mirrors.
- Rule paths must be unique across core, stacks and packs. A stack adds rules
  and never replaces a core one.
- Every rule needs `read_when:` frontmatter.
- Each rule lives in one file; other files link to it rather than restating it.
- Re-render and check after changes: the matrix CI runs is in
  [`templates/TEMPLATE_README.md`](templates/TEMPLATE_README.md#checks).
- Deeper reference: [`docs/agents-sections/`](docs/agents-sections/),
  [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md),
  [`INSTALL.md`](INSTALL.md), [`prompts-skills.md`](prompts-skills.md).

## License

MIT — see [`LICENSE`](LICENSE).
