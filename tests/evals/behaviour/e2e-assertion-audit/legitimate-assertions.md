# Case: hits that are legitimate assertions

## Input

> `scan.py` reports 9 hits in `tests/e2e/`: 4 `getByText("Save")`, 2
> `toBeTruthy()` on `response.ok`, 2 `toBeLessThan(500)` on status, 1
> `expect(true).toBe(true)` left from a debug session.

## Expected properties

- Only the `expect(true).toBe(true)` is treated as a defect; the `toBeTruthy()`
  on a boolean and the status checks are judged **legitimate** with a stated
  reason (a boolean has no better assertion; a status bound is the intent).
- `getByText("Save")` is flagged as a brittle selector where the accessible name
  is stable, and left alone where the text *is* the behaviour under test.
- Every hit gets a verdict; the summary counts real defects, not hits.
- No spec file is rewritten wholesale, and any suggested `getByRole` names are
  derived from the DOM it can see rather than invented.
