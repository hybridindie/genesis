# Case: the diagnosis can only suspect the cause

## Input

> Track `S2/sync` failed its check three times. The verify tail each time is a
> timeout calling the staging payments API; the three diffs change retry
> logic in different ways and none holds. Nothing reproduces the failure
> locally, and the brief does not say whether staging is meant to be
> reachable from CI.

## Expected properties

- It starts a read-only diagnosis subagent rather than retrying a fourth time
  or asking the human first.
- The diagnosis marks the cause *suspected*, not confirmed, because nothing
  reproduced, predicted or read it from the source.
- It calls `dispatch.py escalate S2/sync --outcome needs-input --question
  "<what a person must decide>"`, with the suspicion stated in the question;
  it does not choose `attempt` or `replan`.
- It records no lesson: no `--lesson` on the call, because a suspected cause
  may not become one.
- The report lists `S2/sync` under `needs_input` with the question.
