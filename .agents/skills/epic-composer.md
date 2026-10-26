# Epic Composer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 5.0.0, owner: John D
  invokes: .agents/skills/epic-interview.md,
           .agents/skills/epic-acceptance-linter.md,
           .agents/templates/epic/epic-shell.md
  doctrine: .agents/doctrine/source-discipline.md,
            .agents/doctrine/acceptance-criteria-rules.md,
            .agents/doctrine/context-discovery.md
-->

Shape one Epic from named source material into a GitHub issue body. The model
synthesizes and plans; the shape, order, and checks are fixed.

## Inputs

- Required: the source paths, transcript, note, or problem statement named by the
  caller.
- Read: `.agents/templates/epic/epic-shell.md` and the three doctrine files above.
- Optional: the existing Epic or issue body when refining.
- Do not read: unrelated repositories, whole directory trees, or generated
  harness output.

## Deterministic Steps

1. **Inventory the sources.** List each input path once; do not summarize yet.
2. **Extract facts.** For each source, record only: problem, actors, desired
   outcome, constraints, prior decisions, and unknowns. Label each as stated,
   inferred, or unknown per `source-discipline.md`.
3. **Draft the outcome and scope.** Use the exact headings in `epic-shell.md`.
   Keep one outcome; list explicit exclusions.
4. **Draft 3–8 acceptance criteria.** Use the form `When …, then …, so that …`.
   If the count exceeds 8, split the Epic instead of shrinking the criteria.
5. **Build the story map.** Assign every story a size (S/M/L), priority (P0–P2),
   wave, dependency, and ownership scope. Default to parallel; name the real
   dependency for every later wave.
6. **Define the shared contract.** If parallel tracks share an interface, type,
   schema, or file format, name it and its owner. Otherwise write `none`.
7. **Gap gate.** If a gap changes scope, actors, or acceptance, run
   `.agents/skills/epic-interview.md` and ask only its blockers. If the criteria
   need review, run `.agents/skills/epic-acceptance-linter.md`.
8. **Validate the shape.** Check that every heading from `epic-shell.md` exists,
   the AC count is 3–8, every story has an owner and a wave, and every AC maps to a
   story or an explicit constraint.

## LLM Judgment

Use judgment only for:

- synthesizing the problem and outcome from conflicting source material;
- choosing the smallest coherent vertical slices;
- sizing and wave assignment when dependencies are ambiguous;
- deciding whether a gap is a blocker or a deferrable.

Do not invent facts, metrics, approvals, or acceptance criteria. Mark inferred
content and unknowns.

## Output

One Epic issue body using `.agents/templates/epic/epic-shell.md`, with the
stable title `Epic: <outcome>`. Include the story table and parallelization map
even when the stories do not have issue numbers yet (`#TBD`).

## Stop Conditions

- Stop and ask if the source has no identifiable problem or outcome.
- Stop and ask if two sources contradict each other on scope or acceptance.
- Stop and split if the work has two unrelated outcomes or more than 8 ACs.
- Do not decompose into tasks; that belongs to the story's task breakdown.

## Token Budget

- Read the named sources, `epic-shell.md`, and the three doctrine files only.
- Do not enumerate the repository or load unrelated rules.
- Target ≤ 1,200 words in the Epic body; if longer, split the Epic.
- Reuse the template headings; do not restate them in prose.
