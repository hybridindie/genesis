<!--
  test-discipline-rules.md — Shared test discipline doctrine
  Referenced by: testing.md, enforcement.md (checklist),
                 backend-architect.md, frontend-architect.md
  Rendered into target projects at .claude/rules/doctrine/test-discipline-rules.md
  version: 1.0.0, owner: John D
  Single source of truth for the zero-skip / zero-fail / coverage-tier rules
  restated across testing.md, enforcement.md, and both architect agents.
-->

# Test Discipline Rules

The test-discipline rules referenced by multiple articles and agents live
here. The full `testing.md` rule holds the TDD mandate, coverage
tiers, and Suite Health definition; this file holds only the rules restated
across enforcement and the architect agents.

## Zero-tolerance rules

- Zero `@pytest.mark.skip`, zero `xfail`, zero failing or erroring tests may
  be checked in.
- `{{TEST_BACKEND_CMD}}` MUST exit zero.
- `{{TEST_FRONTEND_CMD}}` MUST exit zero.

## Coverage tier rule

Coverage minimums (from `testing.md`, referenced by the CI coverage gate):

- Security-critical code: 90%+
- Business logic: 70%+ ({{COVERAGE_AGGREGATE_BACKEND}} aggregate backend)
- Frontend: 60%+ ({{COVERAGE_AGGREGATE_FRONTEND}} aggregate frontend)
- AI/ML: 50%+

CI fails the pipeline on coverage regression for changed files (line +
branch).

## How callers use this file

- `testing.md` is the canonical source; this doctrine holds
  the rules enforcement and the agents restate.
- `enforcement.md` references this for the checklist's test items instead
  of restating them.
- `backend-architect.md` and `frontend-architect.md` reference this for
  their hard constraints on skips/failures.