# Case: mostly legitimate hits

## Input

> `scan.py` reports 12 hits: 6 `hardcoded-dates` in `tests/fixtures/reports/`,
> 3 `hardcoded-dates` in `tests/unit/test_billing.py` asserting a due-date
> calculation, 2 `asyncmock` in a class that wraps a real async client, and 1
> `singleton` on `mlflow`.

## Expected properties

- The fixture hits are dismissed **with a reason** (fixture data, not an
  assertion), and the report says so — not "12 issues found".
- The 3 assertions in `test_billing.py` are identified as the real risk
  (hardcoded dates rot as the calendar moves) and a concrete fix is proposed
  (freeze time or derive the expected date).
- The `AsyncMock` hits are judged on whether the code under test talks to a real
  seam; the report says which seam and what to use instead.
- It does not edit every hit, and it does not dismiss a hit merely because the
  pattern is noisy — each gets a verdict.
