# Case: a track fails its check a third time and the cause is confirmed

## Input

> Epic #40, story S1. Track `S1/api` owns `src/report/**` and
> `tests/report/**`. Its check has failed three times: each attempt's verify
> tail ends in `ImportError: cannot import name 'ReportRow' from
> 'src.report.schema'`, and each retry note asked the subagent to add the
> import. The contract track `S1/contract` (already merged) exports
> `ReportRecord`, not `ReportRow`. The third `retry` call blocked the unit
> for replanning. Each subagent reported its token use when it finished.

## Expected properties

- It does not stop at "blocked for replanning" or ask the human what to do
  next: it starts a fresh, read-only subagent with the unit's findings, the
  three diffs, the verify tails and the unit's `history`, and that subagent
  writes the diagnosis file (Symptom, What changed between attempts, Cause,
  Evidence, Rung and why) per `.agents/doctrine/escalation.md`.
- The diagnosis subagent does not edit code, commit, or run `dispatch.py`;
  the lead runs `dispatch.py escalate S1/api --diagnosis <file> --outcome
  <rung>` itself.
- The outcome follows the diagnosis: the cause is confirmed by reading the
  merged contract (it does not export `ReportRow`) and lies in the plan, so
  it calls `--outcome replan`, not a fourth `retry` and not `attempt`.
- The diagnosis names a lesson, so the same `escalate` call carries
  `--lesson "<one-sentence constraint>" --lesson-paths <globs>`; it does not
  propose the lesson to a person or wait for approval, and it does not run
  `dispatch.py learn` separately.
- After every subagent finishes (each track subagent and the diagnosis
  subagent), it runs `budget.py record --epic 40 --unit <unit> --tokens <n>`
  with that subagent's reported tokens.
- Other units in the wave keep running; the report lists `S1/api` under
  `needs_replan` with the diagnosis as its note.
