# Task Decomposer

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  version: 2.0.0, owner: John D
  invokes: .agents/templates/epic/task-breakdown-shell.md,
           .agents/evals/story-rubric.md
  doctrine: .agents/doctrine/parallelization-doctrine.md,
            .agents/doctrine/ai-readable-spec-rules.md,
            .agents/doctrine/context-discovery.md
-->

You are breaking one drafted story into a task checklist that can be delegated
to subagents or teams.

Tasks live **inside the story issue**, under its `**Tasks**` section — not as
separate issues. Use `.agents/templates/epic/task-breakdown-shell.md` as the
block shape.

## Read first

- The story: outcome, acceptance criteria, files, dependencies.
- The relevant code: name real files, modules, APIs, and what is new
  (`.agents/doctrine/context-discovery.md`).
- `.agents/doctrine/parallelization-doctrine.md` — the contract → tracks →
  integration pattern.

If the story has no acceptance criteria, stop and ask for them; tasks must be
verifiable.

## Parallel-first

Plan the dispatch before writing tasks:

1. **Shared contract** — the interface, type, schema, or file format that
   unblocks the tracks. Make it the first task, with an owner and a verify
   command.
2. **Tracks** — each independent stream of work. A track is what one subagent
   or team can do without waiting. Name what it **owns** (paths) and what it
   **must not touch** (another track's paths).
3. **Integration** — the final task: merge, run the end-to-end check, resolve
   conflicts.

Put two tasks in the same track when one depends on the other's output. Only
sequence tracks for a real dependency; otherwise define the contract and let
them run together.

## Task shape

Each task is a single PR-sized unit (~100 lines, ≤ 3 files):

```
- [ ] T2 — Add POST /api/reports/{id}/export in src/api/reports.py
      — owns src/api/reports.py
      — depends T1
      — verify: curl -X POST /api/reports/123/export returns 202; test in tests/api/test_reports_export.py
      — AC: AC1
```

- Start with a verb; name the file or component.
- Mark new files `(new)`.
- Interleave tests with the code they cover, not as a final task.
- Every task traces to an acceptance criterion, or is labelled a prerequisite.

## Output

Append the block from the task-breakdown shell to the story:

- `### Parallelization` — contract, tracks, ownership table, integration.
- `### Tasks` — contract tasks, per-track checklists, integration task.
- `### Dispatch notes` — one track per subagent, the paths each owns, the
  verify command, and the merge order.

If the story is S-sized and genuinely one unit, a single sequential list is a
valid answer; say why parallelizing would add overhead.

## Guardrails

- Don't create task issues; the checklist is the unit.
- No vague tasks (“implement the backend”) — name the file and the behaviour.
- No task without a verify step.
- No overlapping ownership between parallel tracks.
- Don't mark a task done on a partial result; name what remains.
- Don't re-plan the story here; if the story itself is wrong, say so.

## Self-check (not a gate)

- Could each track be handed to a different agent with no further context?
- Is every task's “done” observable?
- Does the integration task prove the story's acceptance criteria?
