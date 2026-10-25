<!--
  ci-enforcement-rules.md — Shared CI/enforcement doctrine
  Referenced by: enforcement.md (Enforcement Gates table),
                 cicd.md (MUST list), backend-architect.md, frontend-architect.md
  Rendered into target projects at .claude/rules/doctrine/ci-enforcement-rules.md
  version: 1.0.0, owner: John D
  Single source of truth for what CI enforces and the merge gates.
-->

# CI Enforcement Rules

The enforcement gates and CI MUST list are defined here once. Articles and
agents reference this file instead of restating the gates.

## Enforcement Gates

| Gate | Tool | Blocks Merge On |
|------|------|-----------------|
| Workflow Pipeline | `.claude/rules/workflow.md` | Skipped step (no issue, test-after-code, unaddressed PR comment, bundled drive-by fix) |
| Constitution Checker | `{{BACKEND_PATH}}/scripts/check-constitution.py` | Structure violations |
| Test Coverage | CI coverage report | Below tier minimums |
| Suite Health | `.claude/hooks/check-no-skipped-tests.sh` + CI | Any forbidden skip pattern or failing/erroring test |
| Agent/Rule Drift | `.claude/hooks/check-agent-drift.sh` + PreToolUse hook | Any stack version claim that contradicts `AGENTS.md` |
| Type Check | pyright/mypy | New type errors |
| Lint | ruff | Lint errors |
| Security | bandit / dependency audit | High severity unresolved |
| Contracts | contract tests | Schema drift |
| Test Fidelity Agent *(planned)* | Expert validation agent (CI Stage 1) — activate after ≥20 calibration cycles | Agent-generated test code that omits edge cases or weakens assertions vs. the specification |
| Architectural Conformance Agent *(planned)* | Expert validation agent (CD Stage 1) — activate after ≥20 calibration cycles | Implementation violating feature description constraints |

## CI MUST list

- Enforce CI gates: lint, type check, tests, coverage, security scan,
  dependency audit.
- Fail pipeline on coverage regression or high severity CVE.
- Deterministic build artifacts (pin dependencies / lockfiles committed).
- Coverage diff per PR (line + branch for changed files).

## Constraint 8 (pipeline-red rule)

While the pipeline is red, agents may only generate changes restoring
pipeline health. No feature work until green is restored.

## How callers use this file

- `enforcement.md` references this for the gates table.
- `cicd.md` references this for the MUST list and constraint 8.
- The architect agents reference this for the CI gates they must respect.