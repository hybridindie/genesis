---
read_when: "Writing or fixing tests, choosing coverage, or touching test infrastructure"
---

# Testing: Red First, Deterministic, Zero Skips

This file is the single source for test discipline. Other rules and agents
link here instead of restating it.

## MUST

- Write the failing test first and confirm it fails for the right reason;
  commit the test with the fix.
- Every bug fix ships a regression test.
- Public interfaces (HTTP, MCP, CLI, file formats, addon commands) get a
  contract test before the implementation changes.
- Deterministic: inject clock, RNG, ids, and network. No `sleep` to
  synchronise, no real sockets in unit tests, no order dependence.
- No unconditional skip or xfail is committed. A skip is allowed only for a
  real environment precondition (missing GPU, OS-specific path), and its line
  carries `skip-ok: <reason>` so the skip gate accepts it.
- The suite is green on a clean checkout. A failing or flaky test is fixed or
  removed in its own PR, never left red.

## Coverage floors

| Code | Floor |
|---|---|
| Safety, security, irreversible actions | 90% |
| Core domain logic | 80% |
| IO and adapters | 70% |
| Helpers and formatting | 50% |

Floors apply to changed files. Coverage is a floor, not a goal; behaviour
assertions matter more than the number.

## SHOULD

- Follow the repo's existing test layout. For a new repo: `tests/unit`,
  `tests/contract`, `tests/integration` (real adapters, behind a marker), and
  `tests/e2e`.
- Fakes for external systems; golden files for serialised output.
- Tests are independent and safe to run in parallel.

## ANTI-PATTERNS

- Weakening an assertion or deleting a test to get green.
- Mocking the unit under test, or asserting only that a mock was called.
- Asserting on log text instead of structured output.
- A test written after the code that could not have failed.
