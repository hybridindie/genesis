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
wave-dispatcher ────────────► merged story branches → PRs
  • dispatch.py prepares each runnable track: branch, worktree, brief
    (with lessons from .agents/plan-constraints.yaml), baseline verify
  • one subagent per track, in parallel
  • dispatch.py check: scope + verify, weak-check and edge warnings,
    the unit's lane and history; the model reviews wide diffs
  • retry: back to the same worktree with the findings, ≤ 3 attempts,
    then blocked for replanning
  • dispatch.py merge in merge_order by lane: contained, wide, or
    irreversible (a person approves); conflicts block the track
  • learn: a confirmed cause becomes a constraint for later plans
  • integrate the finished story, then ship-pr

Every plan lives in a fenced `agent-plan` block; `plan.py check` validates it
and renders the tables (`.agents/doctrine/agent-plan-schema.md`).
```

Artifacts are GitHub issues: `Epic: <outcome>`, `Story N: <outcome>` (or
`story(scope): …`), with the task checklist embedded in the story. The optional
quality passes (`epic-rubric`, `story-rubric`) advise; they do not gate.
