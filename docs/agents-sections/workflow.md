# Epic Scoping Skills — Workflow

On-demand section — read when running the epic/story/task pipeline.

```
Source material, notes, or a problem statement
  │
  ▼
epic-composer ──────────────► Epic issue
  • one outcome, 3–8 observable acceptance criteria
  • scope in/out, constraints, risks, success measures
  • story map: stories sized S/M/L, grouped into parallel waves
  • shared contract named when tracks would otherwise collide
      ↳ epic-interview        (only if a blocker changes the plan)
      ↳ epic-acceptance-linter (optional criteria quality pass)

  ▼
story-decomposer ───────────► one issue per story
  • vertical slice, checkable acceptance criteria, estimate
  • owns <paths>, depends_on, parallel_with, wave
  • shared contract + integration for the tracks
  • execution map: Wave → story → owns → depends → verify

  ▼
task-decomposer ────────────► task checklist inside each story
  • shared contract task first
  • parallel tracks with disjoint file ownership
  • integration task last (merge + end-to-end verify)
  • each task: verb + file, owns, depends, verify, AC

  ▼
Dispatch
  • Wave 1 can start now; Wave 2 after its contract lands
  • one track per subagent or team, with its owns/verify brief
  • integration runs after all tracks; no overlapping edits
```

Artifacts are GitHub issues: `Epic: <outcome>`, `Story N: <outcome>` (or
`story(scope): …`), with the task checklist embedded in the story. The optional
quality passes (`epic-rubric`, `story-rubric`) advise; they do not gate.
