# Task Decomposer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  contract: templates/_shared/doctrine/skill-execution.md
  version: 3.0.0, owner: John D
  invokes: .agents/templates/epic/task-breakdown-shell.md
  doctrine: .agents/doctrine/parallelization-doctrine.md,
            .agents/doctrine/ai-readable-spec-rules.md,
            .agents/doctrine/context-discovery.md
-->

Break one drafted story into a PR-sized task checklist for parallel dispatch.
The checklist lives inside the story issue, not in separate task issues.

## Inputs

- Required: the story body, including acceptance criteria and files.
- Read: `.agents/templates/epic/task-breakdown-shell.md` and the three doctrine
  files above.
- Optional: the named source files, only when a task needs a real path or API.
- Do not read: unrelated modules or the whole repository.

## Deterministic Steps

1. **Gate the input.** If the story has no acceptance criteria, stop and ask for
   them. If the story is larger than L, return it to the story decomposer.
2. **List the ACs and owned paths.** Keep the story's labels and ownership.
3. **Define the shared contract.** Name the interface/type/schema/file format,
   its owner, and a verification command. Skip it when there is no shared surface.
4. **Plan tracks.** Each track is one subagent/team, owns a disjoint path set, and
   depends only on the contract. Put dependent tasks in the same track.
5. **Write tasks.** Each task is one PR-sized unit (≈100 lines, ≤3 files) and
   names: verb, file/component, `(new)` if applicable, depends, verify command,
   and AC.
6. **Add integration.** One final task merges the tracks and runs the story-level
   end-to-end check.
7. **Validate the block.** Confirm every task has a verify step, every track has a
   disjoint ownership set, and every task traces to an AC or a prerequisite.
8. **Emit the block.** Append the shell output under the story's `**Tasks**`
   section. Do not create task issues.

## LLM Judgment

Use judgment only for:

- task granularity and file boundaries;
- the contract's shape when the story leaves it implicit;
- which tasks truly depend on each other.

Do not invent APIs, files, or acceptance criteria.

## Output

One task block using `.agents/templates/epic/task-breakdown-shell.md`:

- `### Parallelization` — contract, tracks, ownership table, integration;
- `### Tasks` — contract, per-track checklist, integration;
- `### Dispatch notes` — one track per subagent, paths owned, verify command,
  merge order.

A single sequential list is valid for an S-sized story; state why parallelizing
would add overhead.

## Stop Conditions

- Stop if the story has no ACs, no owned paths, or is larger than L.
- Stop if two tracks need the same path; split or sequence them.
- Stop if a task cannot name a verify command.

## Token Budget

- Read the story, the task shell, and the doctrine files; open only named files.
- Target ≤ 600 words for the task block; do not repeat the story.
- One checklist per story; no separate task issues.
