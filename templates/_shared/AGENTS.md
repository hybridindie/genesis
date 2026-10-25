# {{PROJECT_NAME}} — Agent Context

Canonical project context for every AI harness in this repo. OpenCode reads this
file natively; Claude Code imports it from `CLAUDE.md` (`@AGENTS.md`); GitHub
Copilot has its own `.github/copilot-instructions.md`. Do not duplicate this
content elsewhere.

## How to use this harness

- **Rules are on demand.** `.claude/rules/**` is the single store of
  constitutional rules. The [rule index](#rule-index) below says which file to
  read for which task — open the file instead of guessing. Do not load the whole
  directory.
- **This harness is yours.** It was rendered for this project and can be edited
  in place. There is no `templates/` directory here.
- **Customization:** run `/harness-eval` (trim rules that do not fit, suggest
  missing ones) then `/customize-harness` (weave the project's domain and
  `my-workflows.md` into this file). Both are idempotent.
- **`my-workflows.md`** holds cross-project conventions (commit style, tooling,
  direnv, permissions). It is loaded automatically and is the source of truth
  for those conventions.

## Project Overview

{{PROJECT_NAME}} — SaaS platform. PostgreSQL-only infrastructure.

## Test Suite Invariants (BLOCKING)

The test suite is a binary signal: fully green and trusted, or a liar. The full
rules live in `.claude/rules/backend/testing.md` and
`.claude/rules/frontend/conventions.md` — the short version:

- **Zero failing tests may be checked in.** `{{TEST_BACKEND_CMD}}` (backend) and
  `{{TEST_FRONTEND_CMD}}` (frontend) MUST exit zero on a clean checkout.
- **Zero unconditional skips may be checked in.** `@pytest.mark.skip`,
  `@pytest.mark.xfail`, `it.skip`, `test.skip`, `describe.skip`, `.todo`, `xit`,
  `xdescribe` are forbidden. `@pytest.mark.skipif(<bool>, reason=...)` gated on a
  real environmental precondition is the only permitted form.
- **Test drift is a bug.** When you change a route, component, store, schema,
  service, or API contract, update the co-owning tests in the same commit.
- **Determinism is mandatory.** Inject `Clock`, `RandomProvider`, `respx`,
  `vi.useFakeTimers()`, or MSW. Never depend on wall-clock `Date.now()`
  comparisons with hardcoded ISO strings.
- **Before claiming work is done**, run
  `bash .claude/hooks/check-no-skipped-tests.sh` and the relevant test suite.
- **Never use `--no-verify`, `--no-gpg-sign`, or any other hook-bypass flag.**
  Fix the failing hook instead.

## Rule Index

Read the matching rule **before** writing code in that area. Paths are relative
to the repo root.

| Rule file | Read when |
|---|---|
| `.claude/rules/backend/architecture.md` | Designing services, libraries, DI, or moving logic out of routes (Articles I–II) |
| `.claude/rules/backend/testing.md` | Writing or fixing any test; choosing tiers and coverage (Article III) |
| `.claude/rules/backend/error-handling.md` | Adding errors, envelopes, logging, or handling failures (Article IV) |
| `.claude/rules/backend/async-patterns.md` | Async endpoints, blocking I/O, concurrency, atomicity (Article V) |
| `.claude/rules/backend/api-design.md` | Routes, OpenAPI, Pydantic schemas, response models (Article VI) |
| `.claude/rules/backend/security.md` | Auth, secrets, encryption, input validation (Article VII) |
| `.claude/rules/backend/caching-strategy.md` | Caching, materialized views, HTTP cache headers (Article X) |
| `.claude/rules/cicd.md` | CI workflows, build determinism, pipeline integrity (Article VIII) |
| `.claude/rules/enforcement.md` | PR checklist, gates, versioning, definition of done (Article IX) |
| `.claude/rules/workflow.md` | The end-to-end issue → PR workflow pipeline |
| `.claude/rules/frontend/conventions.md` | React/TypeScript/Vite components, stores, services |
| `.claude/rules/database/sql-standards.md` | Schema design, migrations, indexes, SQL conventions |
| `.claude/rules/database/infrastructure.md` | PostgreSQL-only infrastructure decisions |
| `.claude/rules/agentic-workflow.md` | Agent delivery contract, ACD session discipline |
| `.claude/rules/error-budgets.md` | SLOs, error budgets, availability targets |
| `.claude/rules/performance-budgets.md` | Performance budgets and regressions |
| `.claude/rules/health-endpoints.md` | Health/readiness/liveness endpoints |
| `.claude/rules/input-security.md` | Input sanitisation, XSS, injection |
| `.claude/rules/logging-observability.md` | Logging, tracing, telemetry |
| `.claude/rules/privacy-gdpr.md` | Personal data, retention, GDPR |
| `.claude/rules/production-safety.md` | Feature flags, canaries, rollbacks |
| `.claude/rules/rate-limiting.md` | Rate limiting and throttling |
| `.claude/rules/dependency-security.md` | Dependency and supply-chain policy |
| `.claude/rules/documentation-standards.md` | Docs and ADR conventions |
| `.claude/rules/primitive-drift.md` | Editing a rule/mirror pair (keep bodies identical) |
| `.claude/rules/doctrine/*.md` | Referenced by the rules above; read only when a rule points here |

## Authoritative References

Source of truth — do NOT duplicate their content:

- `.claude/rules/` — guardrails (Articles I–X), coverage tiers, error mapping, acceptance checklist, versioning
- `{{BACKEND_PATH}}/docs/DATABASE_ARCHITECTURE.md` — {{DB_PROVIDER}}-first data access, repositories, migrations
- `{{BACKEND_PATH}}/docs/STRUCTURE.md` — backend directory organisation
- `docs/architecture/{{PROJECT_SLUG}}_prd.md` — product requirements
- `docs/deploy/` — deployment, env vars, migrations, rollback, incidents
- `docs/plans/` — design docs and implementation plans
- `my-workflows.md` — cross-project conventions for this repo

## Tech Stack

### Backend

- Python {{PYTHON_VERSION}}, FastAPI {{FASTAPI_VERSION}}
- PostgreSQL 17 ({{DB_EXTENSIONS}})
- {{DB_PROVIDER}} client for all DB operations (no SQLAlchemy)
- Docker Compose containerisation
{{#HAS_MLFLOW}}- MLflow (LLM observability, prompt versioning via Prompt Registry){{/HAS_MLFLOW}}
{{#HAS_LANGGRAPH}}- LangGraph 1.0 (agent orchestration){{/HAS_LANGGRAPH}}
- Testing: pytest, httpx, Pydantic

### Frontend

- React {{REACT_VERSION}}, TypeScript {{TYPESCRIPT_VERSION}}, Vite {{VITE_VERSION}}
- {{STATE_MANAGER}} stores ({{FRONTEND_STORE_EXAMPLES}})
- Vitest + MSW + React Testing Library
- {{E2E_TOOL}} E2E, {{UI_LIBRARY}} components

### Local Development

{{#HAS_SUPABASE}}- {{DB_PROVIDER}} CLI for the local PostgreSQL instance (`supabase/config.toml`)
  - API: port 54321, DB: port 54322, Studio: port 54323
  - Migrations in `supabase/migrations/`, seeds in `supabase/seed.sql`
- `supabase start` / `supabase stop` to manage the local instance
- `supabase db push` to apply migrations to remote{{/HAS_SUPABASE}}
{{#HAS_POSTGRES}}- PostgreSQL local instance via Docker Compose or local install
  - Migrations in `{{BACKEND_PATH}}/migrations/`, applied via `psql` or your migration tool
  - Connection string from the environment (`DATABASE_URL`){{/HAS_POSTGRES}}

## Development Workflow

Follow TDD per Article III (`.claude/rules/backend/testing.md`):

1. Write the failing test first (contract tests before implementation).
2. Implement the minimal code to pass.
3. Refactor if needed.
4. Run the constitution checker before opening a PR.

Test authoring order: contract → integration → e2e → unit.

### GitHub project context

If GitHub MCP tools are configured, use them (not `gh`) for issues, PRs and
project state: open epics, P0/P1 issues, open PRs, recently merged PRs. If they
are not configured, `gh` is fine.

- **Priority labels:** `priority:critical` (P0), `priority:high` (P1), `priority:medium` (P2), `priority:low` (P3)
- **Type labels:** `type:epic`, `type:story`, `type:task`, `type:bug`, `type:spike`
- Issues reference their parent epic; PRs say "Closes #N".
- P0 issues use `[P0] Description`; branches use `feature/<issue>-<description>`.

## Key Commands

```bash
# Constitution compliance
cd {{BACKEND_PATH}} && {{PKG_MANAGER_BACKEND}} run python scripts/check-constitution.py

# Backend tests
cd {{BACKEND_PATH}} && {{TEST_BACKEND_CMD}} tests/contract tests/unit -n auto --no-cov
cd {{BACKEND_PATH}} && {{TEST_BACKEND_CMD}} tests/integration -n auto --dist=loadgroup --no-cov
cd {{BACKEND_PATH}} && {{TEST_BACKEND_CMD}} tests/e2e -p no:xdist --no-cov

# Frontend tests
cd {{FRONTEND_PATH}} && {{TEST_FRONTEND_CMD}}

# Database
{{#HAS_SUPABASE}}supabase start
supabase db push{{/HAS_SUPABASE}}
{{#HAS_POSTGRES}}# Apply migrations via your migration tool (psql, alembic, etc.){{/HAS_POSTGRES}}
```

{{CUSTOM_TECH_STACK}}

## Harness Map

| Capability | Claude Code | OpenCode | Copilot |
|---|---|---|---|
| Project context | `CLAUDE.md` (`@AGENTS.md`) | `AGENTS.md` (this file) | `.github/copilot-instructions.md` |
| Rules | `.claude/rules/**` (path-scoped) | `.claude/rules/**` (read via the index) | `.github/instructions/*.instructions.md` |
| Commands | `.claude/commands/*.md` | `.opencode/commands/*.md` | `.github/prompts/*.prompt.md` |
| Subagents | `.claude/agents/*.md` | `.opencode/agents/*.md` (read-only routers) | `.github/agents/*.agent.md` |
| Skills | `.claude/skills/*/SKILL.md` | `.opencode/skills/*/SKILL.md` | prompts |
| Hooks / gates | `.claude/hooks/*.sh` | CI + `/preflight` | `.github/hooks/policy.json` |

### Commands available

`/preflight`, `/start-session`, `/end-session`, `/fix`, `/migration-check`,
`/harness-eval`, `/graphify` (OpenCode ships the graphify command; Claude uses
its graphify skill).

### Skills available

`customize-harness`, `gen-contract-test`, `create-migration`,
`test-hygiene-scanner`, `e2e-assertion-audit`. Invoke by name/description; the
harness advertises them.

## MCP Servers

- **Context7** — up-to-date library docs. `resolve-library-id` first, then
  `query-docs`. Use it for {{DB_PROVIDER}}, FastAPI, React, {{STATE_MANAGER}},
  {{E2E_TOOL}}, Pydantic and any other dependency.
- **{{UI_LIBRARY}}** — component registry; check it before building UI
  components by hand.
- **{{E2E_TOOL}}** — browser automation for E2E, OAuth debugging, visual checks.

## Knowledge Graphs

Architecture graphs built with graphify. Read the relevant report **before**
structural recommendations, new libraries, or data-flow tracing in that area.

| Graph | Report | When |
|---|---|---|
| Backend app | `{{BACKEND_PATH}}/src/graphify-out/GRAPH_REPORT.md` | Adding/changing a lib, tracing service dependencies, DI |
| Frontend app | `{{FRONTEND_PATH}}/src/graphify-out/GRAPH_REPORT.md` | Store topology, component ownership, service wiring |

Build or refresh with `/graphify <path>` (all harnesses ship the command). If the
`graphify` CLI is not installed, say so — do not install it unprompted.

## Project Constraints

{{CUSTOM_INSTRUCTIONS}}

- **Architecture**: Articles I–IX (library-first, DI, TDD, DomainError, async, Pydantic, security, CI).
- **Database**: {{DB_PROVIDER}}-only (no SQLAlchemy), TEXT+CHECK over ENUMs, FK indexes, migrations via the {{DB_PROVIDER}} CLI.
{{#HAS_MLFLOW}}- **AI prompts**: all prompts through the MLflow Prompt Registry (no hardcoded inline prompts).{{/HAS_MLFLOW}}
- **Testing**: TDD per Article III, tiered coverage, zero skips, zero failures.
- **Frontend**: {{STATE_MANAGER}} stores (300-line max), {{UI_LIBRARY}} components, typed service modules.

## Glossary

- **DomainError**: structured base exception with a stable `code` for clients
- **Contract test**: validates an externally visible interface/schema boundary
- **Deterministic**: same input → same output (time/randomness controlled)
- **Idempotent**: repeated identical invocations produce the same final state
- **Envelope**: JSON wrapper: `{"data": ...}` or `{"error": ...}`

## Architecture Milestones

These are permanent architectural decisions, not a changelog. Check merged PRs
for recent work.

{{CUSTOM_TECH_STACK}}
