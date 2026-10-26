# Epic Scoping Skills — Skills, Templates, Doctrine, Wrappers

On-demand section — read when invoking a skill or checking its references.

## Skills

| Skill | Shared content | Purpose |
|---|---|---|
| epic-composer | `.agents/skills/epic-composer.md` | Draft an Epic issue from source material, with a parallel story map |
| epic-interview | `.agents/skills/epic-interview.md` | Ask the smallest set of questions that unblocks the Epic |
| epic-acceptance-linter | `.agents/skills/epic-acceptance-linter.md` | Review acceptance criteria; suggest concrete rewrites |
| story-decomposer | `.agents/skills/story-decomposer.md` | Turn an Epic into story issues with waves, contracts and file ownership |
| task-decomposer | `.agents/skills/task-decomposer.md` | Break one story into a parallel task checklist for delegation |
| bootstrap-harness | `.agents/skills/bootstrap-harness.md` | Install/tailor a project harness (also `install-harness` and `install.sh`) |

## Templates and evals

- Epic issue body: `.agents/templates/epic/epic-shell.md`
- Story issue body: `.agents/templates/epic/story-shell.md`
- Task breakdown block (pasted under the story's `**Tasks**`):
  `.agents/templates/epic/task-breakdown-shell.md`
- Traceability table: `.agents/templates/epic/traceability-template.md`
- Optional Epic quality pass: `.agents/evals/epic-rubric.md`
- Optional story/task quality pass: `.agents/evals/story-rubric.md`

## Doctrine (shared rules)

| Module | Referenced by | Purpose |
|---|---|---|
| `parallelization-doctrine.md` | story-decomposer, task-decomposer | Contract → parallel tracks → integration; the metadata (`owns`, `depends_on`, `parallel_with`, `verify`) that makes work dispatchable |
| `acceptance-criteria-rules.md` | epic-composer, epic-interview, epic-acceptance-linter, story-decomposer | What makes a criterion observable and testable |
| `ai-readable-spec-rules.md` | story-decomposer, task-decomposer | Name files/APIs, exists-vs-new, no pronouns, executable specs |
| `source-discipline.md` | all epic skills | Separate stated/inferred/unknown; never invent; surface contradictions |
| `context-discovery.md` | epic-composer, story-decomposer, task-decomposer | Greenfield vs brownfield probes |
| `review-checkpoint.md` | epic-composer, story-decomposer (optional) | Present a draft → ask → incorporate |
| `skill-execution.md` | all shipped/body skills | Fixed execution order, LLM-only zones, output/stop/token contracts |

When a rule is shared by two or more skills, it belongs in `doctrine/`. Edit
there once; all references inherit.

## Harness-specific wrappers

| Harness | Skill location | Commands | Hooks | Frontmatter fields |
|---|---|---|---|---|
| OpenCode | `.opencode/skills/<name>/SKILL.md` | `opencode.json` command entries: `/epic-composer`, `/epic-interview`, `/epic-acceptance-linter`, `/story-decomposer`, `/task-decomposer` | `.opencode/plugins/*.ts` | `name`, `description` |
| Claude Code | `.claude/skills/<name>/SKILL.md` | skills double as `/epic-composer`, `/epic-acceptance-linter`, `/epic-interview`, `/story-decomposer`, `/task-decomposer` (accept `$ARGUMENTS`) | `.claude/hooks/*.sh` | `name`, `description`, `when_to_use` |

Profile-only assets: `migration-check` and the `create-migration` /
`e2e-assertion-audit` skills ship with the `web` profile. The other profiles get
the core commands and skills only.

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
