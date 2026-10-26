# Epic Composer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  Do not add frontmatter here; harnesses parse frontmatter from their own
  .opencode/skills/ or .claude/skills/ files.
  version: 4.0.0, owner: John D
  invokes: .agents/skills/epic-interview.md,
           .agents/skills/epic-acceptance-linter.md,
           .agents/templates/epic/epic-shell.md
  doctrine: .agents/doctrine/source-discipline.md,
            .agents/doctrine/acceptance-criteria-rules.md,
            .agents/doctrine/context-discovery.md
-->

You are shaping an Epic from real source material: transcripts, notes, docs, a
problem statement, or a rough idea.

Produce a GitHub issue body that a team can review and decompose. Use
`.agents/templates/epic/epic-shell.md` as the shape; drop or add sections when
the work demands it, but keep the outcome, acceptance criteria, and story map.

## Read first

- The source material, all of it. Separate what is **stated**, what is
  **inferred**, and what is **unknown** (`.agents/doctrine/source-discipline.md`).
- `.agents/doctrine/acceptance-criteria-rules.md` for what makes a criterion
  checkable.
- The project's context: existing modules, constraints, prior decisions
  (`.agents/doctrine/context-discovery.md`).

## What a good Epic looks like

- **One outcome.** If you can name two unrelated outcomes, split the Epic.
- **3–8 acceptance criteria**, each observably true or false, written as
  “When …, then …, so that …”. Outcomes, not implementation.
- **Explicit scope.** What is in, what is out, and why the exclusions exist.
- **A story map that can run in parallel.** Stories sized S/M/L, ordered into
  waves, each naming what it depends on and what it can run beside.
- **A shared contract** for any work that would otherwise have to be
  sequential: the interface, type, schema, or file format both sides need.
- **Honest gaps.** Unknowns, contradictions, and assumptions are visible, not
  smoothed over.

## How to work

1. Synthesize the sources into a short problem statement and outcome.
2. Draft the acceptance criteria before the stories; stories exist to satisfy
   them.
3. Sketch the story map:
   - vertical slices, one shippable outcome each;
   - a spike first only if an unknown blocks more than one story;
   - a contract story only when parallel tracks share an interface;
   - waves where everything in a wave can be dispatched together.
4. If a gap blocks scope or acceptance, run `.agents/skills/epic-interview.md`
   and ask only the questions that change the plan.
5. Write the Epic body. Link the story issues once they exist; before that,
   use `#TBD` and keep the story titles stable.
6. Optionally run `.agents/skills/epic-acceptance-linter.md` on your criteria,
   and `.agents/evals/epic-rubric.md` as a quality pass when the user asks for
   a strict review.

## Parallelization

Read `.agents/doctrine/parallelization-doctrine.md`. Default to parallel:
only sequence work when a real dependency exists, and name it. The Epic's
`Parallelization map` should let a lead say “dispatch Wave 1 now, Wave 2 after
the contract lands” without re-reading the whole Epic.

## Guardrails

- Don't invent facts, metrics, or approvals. Label inferred content; mark
  unknowns.
- Don't write implementation-as-criteria (“the API returns JSON”) when an
  outcome will do (“the user sees their order history”).
- Don't decompose into tasks here; that belongs to the story's task breakdown.
- Keep the Epic reviewable in one sitting. If it sprawls, split it.

## Self-check (not a gate)

- Would a stakeholder recognise the problem and the outcome?
- Is every criterion checkable without reading the code?
- Could Wave 1 be dispatched today with no further questions?
- Are the unknowns and their owners visible?
