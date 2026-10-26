# Story Decomposer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  version: 4.0.0, owner: John D
  invokes: .agents/skills/task-decomposer.md,
           .agents/templates/epic/story-shell.md,
           .agents/templates/epic/task-breakdown-shell.md,
           .agents/evals/story-rubric.md
  doctrine: .agents/doctrine/parallelization-doctrine.md,
            .agents/doctrine/ai-readable-spec-rules.md,
            .agents/doctrine/source-discipline.md
-->

You are turning a ready Epic into stories that can be dispatched in parallel.

Use `.agents/templates/epic/story-shell.md` for each story issue body. The
output should let a lead assign each wave to different subagents or teams
without re-reading the Epic.

## Read first

- The Epic: outcome, acceptance criteria, constraints, story map.
- `.agents/doctrine/parallelization-doctrine.md` — parallel is the default.
- `.agents/doctrine/ai-readable-spec-rules.md` — name files, APIs, and what is
  new versus existing.

If the Epic has no acceptance criteria, or its outcome is still ambiguous, send
it back to `epic-composer` / `epic-interview` instead of decomposing.

## Shape

Each story is one vertical slice that can ship on its own. Choose the type:

- **user** — delivers observable value to a user.
- **spike** — time-boxed investigation that unblocks other stories; output is a
  decision or findings, not production code.
- **technical** — enablement that cannot be absorbed into a user story (schema,
  CI, migration, shared contract).
- **bug** — restores broken behaviour.

A good story has:

- one clear outcome and a checkable acceptance criterion (BDD scenarios where
  they help);
- an estimate: **S** (~½–1 day), **M** (~1–2 days), **L** (~2–3 days); split
  anything larger;
- an Epic back-link and the ACs or constraints it covers;
- an explicit ownership scope: the paths it will touch.

## Parallel plan

Draft the execution map before writing the stories:

1. **Shared contract** — if two stories need the same interface, type, schema,
   or file format, make defining it the first story (or a small task inside
   the earliest story). Name its owner.
2. **Waves** — group independent stories into Wave 1, Wave 2, … A wave is what
   can be dispatched together.
3. **Ownership** — each story declares `owns` (paths) and anything it must not
   touch. Two parallel stories must not own the same files; if they do, split
   the scope or sequence them.
4. **Integration** — the last story (or an explicit task) merges the tracks and
   runs the end-to-end check.

Only sequence stories for a real dependency. If the only reason is “it feels
safer”, put them in the same wave behind a contract.

## Output

- One issue body per story, using the story shell (title: `Story N: <outcome>`
  or `story(scope): <outcome>`).
- An **Execution map** table: Wave · Story · Size · Owns · Depends on ·
  Parallel with · Verify.
- A coverage note: every Epic AC mapped to at least one story; every story
  mapped back to an AC or an explicit constraint.

Then invoke `.agents/skills/task-decomposer.md` for each story that will be
implemented, or let the user choose which stories to break down first.

## Guardrails

- No horizontal slices (“build the database layer”). Use a technical story
  only when it is a real prerequisite.
- No story without acceptance criteria, and no story larger than L.
- No duplicated ownership between parallel stories.
- Don't invent requirements the Epic does not contain; mark gaps explicitly.
- Don't over-parallelize a small story: one track is fine when the work is
  genuinely one unit.

## Self-check (not a gate)

- Could each Wave 1 story start today without another story landing?
- Does every story name the files or modules it will change?
- Is the shared contract small enough to land first?
- Is every Epic AC covered exactly once?
