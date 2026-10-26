---
read_when: "Writing or fixing tests, choosing coverage, or touching test infrastructure"
---

# Testing: Red First, Deterministic, Zero Skips

## MUST

- Write the failing test first; commit test + fix together.
- Every bug fix ships a regression test.
- Contract tests come before implementation for public interfaces (HTTP, MCP, CLI, file formats).
- Determinism: inject clock/RNG/network. No sleeps, real sockets, wall-clock comparisons, or order-dependent tests.
- Zero unchecked skips/xfail. A conditional skip is allowed only for a genuine environment precondition.
- Tests are independent and parallel-safe; no shared mutable fixtures.

## Tiers

| Risk | Minimum |
|---|---|
| Safety, security, irreversible actions | 90%+ |
| Core business rules | 80%+ |
| IO and adapters | 70%+ |
| Helpers and formatting | 50%+ |

Coverage is a floor, not a goal.

## Layout

- `tests/contract/` — schema, envelope, protocol
- `tests/integration/` — real adapters (DB, HTTP, subprocess)
- `tests/e2e/` — user-visible flows
- `tests/unit/` — pure logic
- Fakes for external systems; golden files for serialized output.

## ANTI-PATTERNS

- Asserting on log strings instead of structured output.
- Mocking the thing under test.
- `sleep()` to synchronise.
- Tests that pass serially but fail in parallel.
- Coverage theatre: asserting a mock was called without checking behaviour.

## Checklist

- [ ] Test failed before the fix.
- [ ] No skip/xfail added.
- [ ] No wall clock/RNG/network dependence.
- [ ] Contract test covers the public boundary.
