# Story Decomposer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 5.0.0, owner: John D
  invokes: .agents/skills/task-decomposer.md,
           .agents/templates/epic/story-shell.md,
           .agents/templates/epic/task-breakdown-shell.md
  doctrine: .agents/doctrine/parallelization-doctrine.md,
            .agents/doctrine/ai-readable-spec-rules.md,
            .agents/doctrine/source-discipline.md
-->

Turn a ready Epic into stories that can be dispatched in parallel. Each story
uses `.agents/templates/epic/story-shell.md`; the execution map is fixed.

## Inputs

- Required: the Epic body, including outcome, scope, and acceptance criteria.
- Read: the story shell and the three doctrine files above.
- Optional: named modules or paths from the Epic for ownership hints.
- Do not read: unrelated code or the whole repository.

## Deterministic Steps

1. **Gate the input.** If the Epic has no outcome or no acceptance criteria, stop
   and send it back to `epic-composer` / `epic-interview`.
2. **List the ACs.** Extract every `ACn` and keep the labels stable.
3. **Choose the story type** for each slice: user, spike, technical, or bug.
4. **Map ACs to stories.** Every AC maps to at least one story; every story maps
   back to an AC or an explicit constraint. Flag a gap instead of inventing one.
5. **Assign size and wave.** S/M/L only; split anything larger than L. Wave 1
   contains everything that can start today.
6. **Assign ownership.** Each story declares `owns` paths and `must not touch`.
   Parallel stories may not own the same path; split or sequence them.
7. **Define the shared contract** and integration story when tracks share an
   interface, type, schema, or file format.
8. **Validate the map.** Confirm no duplicate ownership, no story without an AC,
   and no later wave without a named dependency. Write each story to a temporary
   file and run:
   ```bash
   python3 .agents/scripts/validate_artifact.py --kind story "$story_file"
   ```
   Stop on `FAIL`.
9. **Emit the stories and map.** Do not create task checklists here; invoke the
   task decomposer for each story that will be implemented.

## LLM Judgment

Use judgment only for:

- finding the smallest vertical slices;
- sizing S/M/L;
- deciding whether a shared contract deserves its own story;
- resolving ownership when the Epic leaves it ambiguous.

Do not invent requirements, file paths, or dependencies.

## Output

- One story body per story using `.agents/templates/epic/story-shell.md`,
  titled `Story N: <outcome>` or `story(scope): <outcome>`.
- An execution map:

```markdown
| Wave | Story | Size | Owns | Depends on | Parallel with | Verify |
|------|-------|------|------|------------|---------------|--------|
| 1 | … | S/M/L | `<path/>` | — | … | `<command>` |
```

- A coverage note: every Epic AC covered exactly once, or an explicit gap.
- If the Epic is small enough to be one story, say so and emit one story.

## Stop Conditions

- Stop if the Epic is not ready; do not decompose an ambiguous outcome.
- Stop if two stories would own the same path and cannot be sequenced.
- Stop if an AC cannot be made observable; return it to the acceptance linter.

## Token Budget

- Default: read the Epic and the three doctrine files; open code only for paths
  named in the Epic. Read one more file only when an ownership/size decision is
  otherwise a guess, and say why.
- Target ≤ 900 words for the execution map plus story metadata; story bodies use
  the template, not prose expansion. Exceed only for a real dependency or
  ownership ambiguity.
- Do not restate the Epic or load unrelated rules.
