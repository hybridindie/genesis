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
plan-reviewer ──────────────► ready | needs-work | blocked
  • plan.py check, then a second model via plan_review.py
  • needs-work goes back to the author, ≤ 3 rounds, then escalation

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
  • escalate after 3 failures: diagnosis, then attempt | replan | needs-input
  • integrate the finished story, then ship-pr

Every plan lives in a fenced `agent-plan` block; `plan.py check` validates it
and renders the tables (`.agents/doctrine/agent-plan-schema.md`).
```

Artifacts are GitHub issues: `Epic: <outcome>`, `Story N: <outcome>` (or
`story(scope): …`), with the task checklist embedded in the story. The optional
quality passes (`epic-rubric`, `story-rubric`) advise; they do not gate.

## The factory

`/factory` runs the pipeline from story-decomposer onwards without prompting,
in the session that started it. It works every approved `Epic:` issue that is
open when it starts (no `factory:drafted`, or a person's `factory:approved` /
`factory:auto-approve`), oldest first and one at a time, then exits:

```
list ─► factory:running ─► budget gate ─► stories ─► plan review ─► tasks
         ─► waves (budget gate before each round) ─► factory:shipped
```

- **Budget:** `budget.py` keeps a ledger per Epic, 5,000,000 tokens by
  default. At 80% it posts one warning; at 100% it starts nothing new and
  labels the Epic `factory:over-budget`.
- **Escalation:** every loop follows `.agents/doctrine/escalation.md`. A unit
  that ends at `needs-input` gets `factory:needs-input` on its story; the rest
  of the wave keeps running. Plan review that is blocked or unreviewable puts
  `factory:needs-input` on the Epic and stops it.
- **Reporting:** one status line per round in the session and a round summary
  comment on the Epic.

Labels and the full flow: the README's "The factory" section and
`.agents/skills/factory/SKILL.md`.
