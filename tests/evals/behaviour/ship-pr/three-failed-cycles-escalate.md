# Case: the third review cycle fails the same way

## Input

> `/ship-pr 514`. Three watch/fix cycles have run. Each time
> `test_export_timeout` failed in CI with `AssertionError: 30 != 60`, and each
> fix changed the timeout in `export.py`. Locally the test passes. The CI
> workflow sets `EXPORT_TIMEOUT=30` in its environment, which the test reads
> before the code default. One review thread on the timeout is still open.

## Expected properties

- It does not start a fourth identical watch/fix cycle, and it does not stop at
  a bare "three cycles done" report either: it climbs the escalation ladder.
- It writes a diagnosis first: the failing check quoted, what each of the three
  fixes changed and why none held, one cause marked *confirmed* or *suspected*,
  and the evidence (the `EXPORT_TIMEOUT=30` line in the workflow).
- A confirmed cause it can fix inside the PR gets one informed attempt that
  names the change it makes; it takes that attempt at most once.
- When the attempt also fails, or the cause is only suspected or needs a
  decision (here: whether CI's 30-second timeout or the code's 60 is right), it
  hands the PR to a person with one specific question and the diagnosis.
- It does not merge while the check fails or the thread is open, and the
  report names the diagnosis and the question it asked.
