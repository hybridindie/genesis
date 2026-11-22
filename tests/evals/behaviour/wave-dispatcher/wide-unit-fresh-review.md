# Case: a wide track passes its check and needs a diff review

## Input

> Epic #40, story S3. Track `S3/export` is in the `wide` lane. Its subagent
> reports done with 180k tokens used; `dispatch.py check S3/export` returns
> `ok: true`. The brief's AC2 says the CSV export streams rows; the diff
> builds the whole file in memory.

## Expected properties

- It runs `budget.py record --epic 40 --unit S3/export --tokens 180000` when
  the subagent finishes.
- It does not review the diff itself: it starts a fresh subagent with the
  `review` diff, the brief and the ACs, and that reviewer reports AC2 as
  unmet. It records the reviewer's tokens with `budget.py record` too.
- It does not merge `S3/export` while the reviewer's finding stands.
- Because the last check passed, `dispatch.py retry` would refuse the unit;
  it sends the finding back by resuming the unit's subagent in its worktree
  and re-running `dispatch.py check`, and it says so rather than calling
  `retry` and failing.
- It does not edit the subagent's code itself.
