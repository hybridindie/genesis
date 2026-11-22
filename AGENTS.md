# AI Harness Template Repository

This is the **genesis repository**. Two products:

- **System layer**: `system/` → rendered into a machine by `system/install.sh`
  (zsh config, user-level agent rules, git defaults, optional Herdr/Zed).
- **Project layer**: `templates/` → rendered into a repository by `bootstrap.sh`
  (`.claude/` and `.opencode/` harnesses).

It also hosts the **Epic Scoping Skills** as its own installed harness.

## Architecture (summary)

Three layers share the same single-source pattern:

- **System layer**: `system/` → `system/install.sh` renders into `$HOME`. Shell config, user-level `AGENTS.md`, shared git settings. Machine-specific values are flags, never hardcoded.
- **Genesis harness**: `templates/_shared/` → rendered into target projects by `bootstrap.sh`. Rule articles (core + per-stack + opt-in packs), agents, commands, doctrine, and shippable skills.
- **Epic Scoping Skills**: `.agents/` holds every primitive both harnesses share — skills (`.agents/skills/<name>/SKILL.md`, read natively by OpenCode), doctrine, templates, evals, scripts. Claude Code gets generated pointers in `.claude/skills/`; there is no `.opencode/skills/`.

**Golden rule:** Edit content in `system/` (machine layer), `.agents/` (epic skills) or `templates/_shared/` (genesis). Never hand-edit a generated pointer or mirror (`python3 scripts/sync-skill-wrappers.py` regenerates the `.claude/skills` pointers). Shared rules referenced by multiple files live in a `doctrine/` layer — reference, don't restate.

Canonical project context is `templates/_shared/AGENTS.md`: OpenCode reads it
natively and `CLAUDE.md` imports it (`@AGENTS.md`).

The end-to-end flow (new machine → new project → tailoring) is in
[`SYSTEM.md`](SYSTEM.md).

## On-demand reference sections

Read these when you need the detail — they are not auto-loaded:

| Section | File | Read when |
|---|---|---|
| What it does / Install / Key flags | [`docs/agents-sections/genesis-overview.md`](docs/agents-sections/genesis-overview.md) | Installing or bootstrapping a harness |
| Source structure (file tree) | [`docs/agents-sections/source-structure.md`](docs/agents-sections/source-structure.md) | Editing the genesis repo structure |
| Epic skills architecture | [`docs/agents-sections/architecture.md`](docs/agents-sections/architecture.md) | Understanding the `.agents/` layout |
| Workflow (pipeline diagram) | [`docs/agents-sections/workflow.md`](docs/agents-sections/workflow.md) | Running the epic → story → task pipeline |
| Skills, templates, evals, doctrine, harness layout, response states | [`docs/agents-sections/skills-and-references.md`](docs/agents-sections/skills-and-references.md) | Invoking a skill or checking references |
| Full usage guide | [`prompts-skills.md`](prompts-skills.md) | Per-harness setup, hooks table, worked examples |
| Editing contract (versioning, drift, hooks) | [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md) | Editing this repo |
| LSP / language servers | [`docs/agents-sections/lsp.md`](docs/agents-sections/lsp.md) | Enabling LSP or debugging missing diagnostics |

## Skills at a glance

| Skill | Invoke | Shared content |
|---|---|---|
| epic-composer | `/epic-composer` | `.agents/skills/epic-composer/SKILL.md` |
| epic-interview | `/epic-interview` | `.agents/skills/epic-interview/SKILL.md` |
| epic-acceptance-linter | `/epic-acceptance-linter` | `.agents/skills/epic-acceptance-linter/SKILL.md` |
| story-decomposer | `/story-decomposer` | `.agents/skills/story-decomposer/SKILL.md` |
| task-decomposer | `/task-decomposer` | `.agents/skills/task-decomposer/SKILL.md` |
| plan-reviewer | `/plan-reviewer` | `.agents/skills/plan-reviewer/SKILL.md` |
| wave-dispatcher | `/wave-dispatcher` | `.agents/skills/wave-dispatcher/SKILL.md` |
| factory | `/factory` | `.agents/skills/factory/SKILL.md` |
| bootstrap-harness | `/bootstrap-harness` | `.agents/skills/bootstrap-harness/SKILL.md` |
| ship-pr | `/ship-pr` | `templates/_shared/skills/ship-pr/SKILL.md` |

Post-bootstrap flow: `bootstrap.sh` (render) → `/harness-eval` (trim + suggest)
→ `/customize-harness` (domain tailoring). The harness-eval prompt lives at
[`docs/harness-eval.md`](docs/harness-eval.md).

OpenCode loads each skill from `.agents/skills/` directly; Claude Code's
generated pointer loads the same file on demand. Doctrine files (`.agents/doctrine/`) are
read on-demand when a skill references them.
