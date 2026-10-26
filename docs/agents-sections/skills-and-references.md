# Epic Scoping Skills — Skills, Templates, Evals, Doctrine, Wrappers, Response States

On-demand section — read when invoking a skill or checking its references.

## Skills

| Skill | Shared content | Purpose |
|---|---|---|
| epic-composer | `.agents/skills/epic-composer.md` | Transforms source material into a complete Epic |
| epic-acceptance-linter | `.agents/skills/epic-acceptance-linter.md` | Lints acceptance criteria quality |
| epic-interview | `.agents/skills/epic-interview.md` | Guided interview to close gaps |
| story-decomposer | `.agents/skills/story-decomposer.md` | Decomposes a ready Epic into INVEST-compliant stories |
| task-decomposer | `.agents/skills/task-decomposer.md` | Breaks down stories into AI-executable tasks with parallelization assessment |
| bootstrap-harness | `.agents/skills/bootstrap-harness.md` | The install/tailor flow: fetch genesis → detect stack → plan review → render via `bootstrap.sh` → validate → report. Also exposed as the `install-harness` agent and the `install.sh` shortcut. |

## Templates and evals

- Epic skeleton: `.agents/templates/epic/epic-shell.md`
- Story backlog: `.agents/templates/epic/story-shell.md`
- Traceability table: `.agents/templates/epic/traceability-template.md`
- Epic readiness rubric: `.agents/evals/epic-rubric.md`
- Story readiness rubric: `.agents/evals/story-rubric.md`

## Doctrine (shared rules)

| Module | Referenced by | Purpose |
|---|---|---|
| `acceptance-criteria-rules.md` | epic-acceptance-linter, epic-composer, story-decomposer, epic-rubric dim 8, story-rubric dim 13 | The six AC linting rules + examples — single source |
| `parallelization-doctrine.md` | story-decomposer, task-decomposer, story-rubric dims 11 & 15 | Contract → parallel tracks/waves → integration |
| `ai-readable-spec-rules.md` | story-decomposer, task-decomposer, story-rubric dim 19 | Name files/APIs, exists-vs-new, no pronouns, executable specs |
| `source-discipline.md` | epic-composer, epic-interview, epic-acceptance-linter, story-decomposer, task-decomposer, epic-rubric dim 11 | Don't invent / surface unknowns / prefer unknown / label inferred |
| `review-checkpoint.md` | epic-composer Phase 6, story-decomposer Phase 6 | Present → ask → incorporate → declare-or-loop |
| `context-discovery.md` | epic-composer Phase 0, task-decomposer Phase 1 | Greenfield/brownfield probe |

When a rule is shared by two or more skills/rubrics, it belongs in `doctrine/`.
Edit there once; all references inherit.

## Harness-specific wrappers

| Harness | Skill location | Commands | Hooks | Frontmatter fields |
|---|---|---|---|---|
| Opencode | `.opencode/skills/<name>/SKILL.md` | `opencode.json` command entries: `/epic-composer`, `/epic-interview`, `/epic-acceptance-linter`, `/story-decomposer`, `/task-decomposer` | `.opencode/plugins/*.ts` | `name`, `description` |
| Claude Code | `.claude/skills/<name>/SKILL.md` | skills double as `/epic-composer`, `/epic-acceptance-linter`, `/epic-interview`, `/story-decomposer`, `/task-decomposer` (accept `$ARGUMENTS`) | `.claude/hooks/*.sh` | `name`, `description`, `when_to_use` |

Profile-only assets: `migration-check` and the `create-migration` /
`e2e-assertion-audit` skills ship with the `web` profile. The other profiles get
the core commands and skills only.

The command names are identical across both harnesses (the skill names). Each skill
wrapper is a one-line body referencing `.agents/skills/<name>.md`; the Opencode
and Claude Code wrappers also take `$ARGUMENTS` for user-provided input.

## Response states

Each skill labels its output with one of these states (`→` marks a progression;
`/` marks alternatives):

- **epic-composer:** `SYNTHESIS_ONLY` → `INTERVIEW_REQUIRED` → `PARTIAL_EPIC` → `FINAL_EPIC`
- **epic-acceptance-linter:** `PASS` / `NEEDS_REVISION` / `BLOCKED`
- **epic-interview:** `QUESTIONS_PENDING` / `PARTIALLY_RESOLVED` / `RESOLVED`
- **story-decomposer:** `EPIC_NOT_READY` / `DECOMPOSITION_PLANNED` / `STORIES_DRAFTED` / `TASKS_ADDED` / `READY_FOR_IMPLEMENTATION` / `NEEDS_REVISION` / `REFINEMENT_IN_PROGRESS`
- **task-decomposer:** `NEEDS_ACCEPTANCE_CRITERIA` / `PARALLELIZATION_PLANNED` / `TASKS_DRAFTED` / `TASKS_LINTED` / `READY`