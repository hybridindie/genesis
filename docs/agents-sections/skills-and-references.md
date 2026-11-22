# Epic Scoping Skills — Skills, Templates, Doctrine, Harness Layout

On-demand section — read when invoking a skill or checking its references.

## Skills

| Skill | Shared content | Purpose |
|---|---|---|
| epic-composer | `.agents/skills/epic-composer/SKILL.md` | Draft an Epic issue from source material, with a parallel story map |
| epic-interview | `.agents/skills/epic-interview/SKILL.md` | Ask the smallest set of questions that unblocks the Epic |
| epic-acceptance-linter | `.agents/skills/epic-acceptance-linter/SKILL.md` | Review acceptance criteria; suggest concrete rewrites |
| story-decomposer | `.agents/skills/story-decomposer/SKILL.md` | Turn an Epic into story issues with waves, contracts and file ownership |
| task-decomposer | `.agents/skills/task-decomposer/SKILL.md` | Break one story into a parallel task checklist for delegation |
| wave-dispatcher | `.agents/skills/wave-dispatcher/SKILL.md` | Run planned stories with parallel subagents in worktrees, driven by `dispatch.py` |
| bootstrap-harness | `.agents/skills/bootstrap-harness/SKILL.md` | Install/tailor a project harness (also `install-harness` and `install.sh`) |
| ship-pr | `templates/_shared/skills/ship-pr/SKILL.md` | Open a PR, watch CI and review, address threads, merge on green CI and addressed threads (also ships to every project) |

## Templates and evals

- Epic issue body: `.agents/templates/epic/epic-shell.md`
- Story issue body: `.agents/templates/epic/story-shell.md`
- Tasks and tracks live in the story's `agent-plan` block; `plan.py check`
  renders the tables (`.agents/doctrine/agent-plan-schema.md`).
- Traceability table: `.agents/templates/epic/traceability-template.md`
- Epic quality pass (epic-composer, on request or before decomposing):
  `.agents/evals/epic-rubric.md`
- Story/task quality pass (story- and task-decomposer, on request or before
  dispatch): `.agents/evals/story-rubric.md`

## Doctrine (shared rules)

| Module | Referenced by | Purpose |
|---|---|---|
| `parallelization-doctrine.md` | story-decomposer, task-decomposer | Contract → parallel tracks → integration; the metadata (`owns`, `depends_on`, `parallel_with`, `verify`) that makes work dispatchable |
| `acceptance-criteria-rules.md` | epic-composer, epic-acceptance-linter | What makes a criterion observable and testable |
| `ai-readable-spec-rules.md` | story-decomposer, task-decomposer | Name files/APIs, exists-vs-new, no pronouns, executable specs |
| `source-discipline.md` | epic-composer, epic-interview, story-decomposer | Separate stated/inferred/unknown; never invent; surface contradictions |
| `context-discovery.md` | epic-composer, task-decomposer | Greenfield vs brownfield probes |
| `review-checkpoint.md` | none — apply on request | Present a draft → ask → incorporate |

The execution contract every skill body follows (fixed sections, LLM-only
zones) is `templates/_shared/doctrine/skill-execution.md` — see
[Deterministic execution](#deterministic-execution).

When a rule is shared by two or more skills, it belongs in `doctrine/`. Edit
there once; all references inherit.

## Harness layout

| Harness | Skill location | Commands | Hooks | Frontmatter it reads |
|---|---|---|---|---|
| OpenCode | `.agents/skills/<name>/SKILL.md` (native) | `commands` entries in `.opencode/opencode.json` (OpenCode skills have no slash path of their own) | `.opencode/plugins/*.ts`, which run the `.claude/hooks/*.sh` scripts | `name`, `description`, `disable-model-invocation` |
| Claude Code | `.claude/skills/<name>/SKILL.md` — a generated pointer to the `.agents/` skill | skills double as slash commands of the same name (accept `$ARGUMENTS`) | `.claude/hooks/*.sh` | all Claude skill fields |

Put trigger phrases in `description`, not only `when_to_use`: OpenCode ignores
`when_to_use`.

Stack-only assets: `/migration-check`, `create-migration` and
`gen-contract-test` ship with the `fastapi` stack; `e2e-assertion-audit` with
`frontend`.

The command names are identical across both harnesses. Each wrapper is a short
pointer to `.agents/skills/<name>.md`; keep the body thin.

## Deterministic execution

Every body skill uses the same six sections: `Inputs`, `Deterministic Steps`,
`LLM Judgment`, `Output`, `Stop Conditions`, `Token Budget`. Mechanical work
(discovery, scaffolding, parsing, validation) belongs in commands/scripts;
synthesis, planning, and semantic review are the model's only judgment zones.
The canonical contract is `templates/_shared/doctrine/skill-execution.md`; run
`python3 scripts/lint-skills.py` before committing.

## Output shape

- **Epic** — an issue body (`Epic: <outcome>`) with a story map and a
  parallelization map.
- **Stories** — one issue body each (`Story N: <outcome>`), with `owns`, waves,
  and a shared contract where needed.
- **Tasks** — a checklist block inside the story: shared contract → parallel
  tracks → integration, each task naming its ownership and verify step.

Optional verdicts (`Ready`, `Needs work`, `Blocked`) come from the linter or a
quality pass. They are advice, not a gate.
