# Research Report: Best Practices Review & Gap Analysis

**Date**: 2026-05-09
**Scope**: AI harness template system for TypeScript/React + Python/FastAPI projects across GitHub Copilot, Claude Code, and Opencode.
**Repositories audited**: `genesis` (formerly `instructions-and-rules`), `influencer-sync` (live), `nomikailist` (live)
**Total files cataloged**: 159

---

## Part 1: External Best Practices Research

### 1.1 GitHub Copilot (2024–2025)

| Finding | Impact | Source |
|---------|--------|--------|
| Copilot Code Review reads only **first 4,000 characters** of any instruction file | CRITICAL — `copilot-instructions.md` (236 lines) may exceed this when rendered | [GitHub Docs](https://docs.github.com/en/copilot/tutorials/use-custom-instructions) |
| Best file length: **under ~1,000 lines** per file | WARNING — several files approach or exceed this | GitHub Docs |
| Scoped `.instructions.md` files use `applyTo:` frontmatter for path matching | VALIDATED — our template already does this correctly | GitHub Docs |
| `description:` in copilot frontmatter improves context matching | VALIDATED — our mirror script generates this | GitHub Docs |
| Avoid vague directives like "be more accurate"; use concrete code examples | GAP — some sections use passive voice instead of imperative DO/DON'T | Community best practices |

### 1.2 Claude Code / Anthropic

| Finding | Impact | Source |
|---------|--------|--------|
| Anthropic explicitly warns: "**Bloated CLAUDE.md files cause Claude to ignore your actual instructions**" | CRITICAL — `CLAUDE.md` template (181 lines) is borderline; live `influencer-sync` version (220 lines) risks being ignored | Anthropic docs |
| Three-layer system: **Rules** (persistent) → **Skills** (on-demand) → **Hooks** (deterministic) | VALIDATED — our architecture matches this exactly | Claude Code best practices |
| Rules should be **file-scoped** (only loaded when matching files are touched) via `paths:` frontmatter | VALIDATED — our `_shared/articles/*.md` use `paths:` correctly | Anthropic docs |
| Constitutional/normative rule architecture is recognized as **sophisticated real-world example** | ACKNOWLEDGED — our Articles I–IX model is ahead of most teams | Community analysis |

### 1.3 Cursor / OpenCode

| Finding | Impact | Source |
|---------|--------|--------|
| Cursor uses `.cursor/rules/*.mdc` with YAML frontmatter (`alwaysApply`, `globs`, `description`) | **GAP** — we have no Cursor harness at all | Cursor docs |
| Supports 4 rule types: Always, File-matched, Intelligent (AI-gated), Manual | — | Cursor docs |
| OpenCode `opencode.json` supports **remote URL references** for shared rules | OPPORTUNITY — we could publish templates as a remote rule source | OpenCode docs |
| OpenCode has `AGENTS.md` + `instructions` array in `opencode.json` | VALIDATED — our `opencode.json` plugin-only approach is incomplete | OpenCode docs |

### 1.4 Cross-Platform Harmonization

| Finding | Impact | Source |
|---------|--------|--------|
| `AGENTS.md` is the **lowest-common-denominator** portable file across all 4+ platforms | VALIDATED — we use it for Copilot, Claude, and Opencode | Multi-platform analysis |
| Recommended hierarchy: `.claude/rules/` (source of truth) → Copilot mirrors → `AGENTS.md` (portable) | VALIDATED — our system follows this exactly | Community consensus |
| **Rule drift** between platforms is the #1 maintenance headache for teams | VALIDATED — our primitive-drift system addresses this directly | Multiple sources |

---

## Part 2: Gap Analysis — 30 Issues Found

### Category A: Missing Technical Domains (CRITICAL)

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| A1 | **Privacy / GDPR compliance** | CRITICAL | `customize-harness.md` references `gdpr` flag but no article exists. No rules for: data retention, right-to-deletion, data minimization, consent tracking, cross-border transfers, PII handling in logs |
| A2 | **Rate limiting specification** | CRITICAL | `error-handling.md` lists `RATE_LIMITED` code but no algorithm, per-endpoint tiers, headers (`X-RateLimit-*`), or middleware pattern specified |
| A3 | **Input sanitization / XSS / injection protection** | CRITICAL | `testing.md` mentions "dedicated suite required" for XSS/injection but zero implementation rules: no CSP, no output encoding, no parameterized query mandate, no command injection rules |
| A4 | **Production safety** (feature flags, canary, rollbacks) | CRITICAL | `cicd.md` silent on deployment safety. No: feature flags, canary requirements, rollback procedures, gradual traffic shifting, dark launches |
| A5 | **Dependency management** (CVE response, Renovate/Dependabot) | CRITICAL | `security.md` says "audit dependencies for CVEs before adoption" but no: update SLA, pinning rules, lockfile validation, automated vulnerability scanning |
| A6 | **JWT patterns underspecified** | CRITICAL | No algorithm mandate (HS256 banned?), no key rotation procedure, no revocation mechanism, no JWKS endpoint spec, no token binding |
| A7 | **Async I/O underspecified** | CRITICAL | No driver specified (asyncpg? psycopg3?), no timeout values, no retry exception types, no circuit breaker, no max backoff cap |

### Category B: Missing Technical Domains (MAJOR)

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| B1 | **Accessibility (a11y)** | MAJOR | `frontend/conventions.md` has zero a11y rules: no `aria-*`, no keyboard nav, no focus management, no screen-reader testing, no color contrast |
| B2 | **Logging standards** | MAJOR | Only "structured logging at boundary layers" mentioned. No: log levels, JSON schema, required fields (trace/correlation ID), retention policies, prohibited fields |
| B3 | **Health / readiness / liveness endpoints** | MAJOR | No `/health`, `/ready`, `/live` requirements, no dependency validation, no graceful shutdown, no startup probes |
| B4 | **Documentation requirements** | MAJOR | No README standards, no ADR mandate, no OpenAPI completeness rules beyond "FastAPI auto-generates", no runbook templates |
| B5 | **Performance budgets** | MAJOR | No bundle size limits, no Core Web Vitals targets, no API p95/p99 latency SLOs, no query execution budgets |
| B6 | **Error budgets / SLOs** | MAJOR | No availability targets, no burn rate alerting, no failure rate thresholds |
| B7 | **Incident response** | MAJOR | `CLAUDE.md` references `docs/deploy/` for incident response but no: severity classification (SEV-1/2/3), on-call patterns, post-mortem template, rollback decision tree |
| B8 | **Error code enum definition** | MAJOR | `error-handling.md` has 10 codes mapped to HTTP statuses but no canonical `ErrorCode` enum spec, no guidance on creating vs reusing codes |

### Category C: Template Mechanics Gaps

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| C1 | **Next.js support** (assumes Vite) | CRITICAL | `frontend/conventions.md` hard-codes Vite. No `{{FRAMEWORK}}` switch, no Next.js patterns (Server Components, app router, API routes) |
| C2 | **Monorepo structures** (packages/, apps/) | MAJOR | Template assumes flat `backend/` / `frontend/`. No workspace config, no shared packages, no cross-package deps, no Turborepo |
| C3 | **React Native / mobile** | MAJOR | `customize-harness.md` references `mobile-app` flag but no template content exists for it |
| C4 | **Serverless / edge deployment** | MAJOR | No Lambda, Vercel Edge, or Cloudflare Workers rules. No cold-start optimization, payload limits, stateless runtime constraints |
| C5 | **Database connection pooling** | MAJOR | `database/infrastructure.md` assumes `{{DB_PROVIDER}}` client but no: pool sizing, connection timeouts, reconnection policy, statement timeout |

### Category D: Enforcement Automation Gaps

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| D1 | **Most Articles have no automated checks** | CRITICAL | Of 8 enforcement gates, only 3 have tools. Articles I, II, IV, V, VI, IX have zero automated enforcement |
| D2 | **No machine-enforceable vs human-judgment classification** | MAJOR | "Functions under 40 lines" is machine-checkable (AST) but no hook exists. "No business logic in routes" requires human/AST review but not classified |
| D3 | **No unified severity taxonomy** | MINOR | Ad-hoc severity: `ANTI-PATTERNS (BLOCKING)`, `Suite Health (BLOCKING)`, agent `BLOCK/FLAG/PASS` — no unified ERROR/WARNING/INFO model |

### Category E: DRY / Cross-File Drift Risks

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| E1 | **Tech stack versions duplicated across 10+ files** | CRITICAL | `{{PYTHON_VERSION}}`, `{{REACT_VERSION}}`, etc. appear in: `CLAUDE.md`, `AGENTS.md`, `copilot-instructions.md`, agents, `conventions.md`, `workflow.md`, `README.md`, `bootstrap.sh` defaults. `check-agent-drift.sh` catches contradictions but not correctness |
| E2 | **Mirror pair lists in 3 places** | MAJOR | `primitive-drift.md` table, `check-primitive-drift.sh` array, `bootstrap.sh` case statement. Adding a new article requires 3 manual updates |
| E3 | **`copilot-instructions.md` duplicates Articles but is not mirrored** | MAJOR | Sections 2, 4-7 of `copilot-instructions.md` are hand-written summaries of Articles I-VII. If `_shared/articles/*.md` change, Copilot instructions can silently diverge |
| E4 | **Skills duplicated across Claude + Opencode** | MINOR | 4 skills (`gen-contract-test`, `create-migration`, `test-hygiene-scanner`, `e2e-assertion-audit`) exist in both `.claude/skills/` and `.opencode/skills/` with no sync mechanism |
| E5 | **Hook logic duplicated in prompts** | MINOR | `check-no-skipped-tests.sh` commands repeated as text in `pre-merge-verify.prompt.md` |

### Category F: Broken References

| # | Gap | Severity | Rationale |
|---|-----|----------|-----------|
| F1 | **`check-constitution.py` referenced but not templated** | MAJOR | `enforcement.md`, `workflow.md`, `CLAUDE.md`, `AGENTS.md` all reference `scripts/check-constitution.py` but no template file exists |
| F2 | **`check-test-hygiene.sh` referenced but missing** | MINOR | `TEMPLATE_README.md` references it in post-customization checks but file doesn't exist |
| F3 | **`sync-to-projects.sh` referenced but missing** | MINOR | `TEMPLATE_README.md` references it for propagating rule changes but file doesn't exist |

---

## Part 3: Positive Validations (What We Do Well)

| Practice | How We Implement | Comparison to Industry |
|----------|---------------|------------------------|
| **Constitutional architecture** (Articles I–IX) | Normative rule hierarchy with enforcement gates | Ahead of most teams; recognized as sophisticated |
| **Cross-platform parity** | Equivalent harnesses for Copilot, Claude, Opencode | Uncommon; most teams support only 1–2 platforms |
| **Primitive drift detection** | `check-primitive-drift.sh` validates mirror sync | Ahead of most teams |
| **Multi-agent orchestration** | UX researcher → UI designer → implementation designer → compliance reviewer | Ahead of most teams |
| **TDD mandate with tiered coverage** | Contract → Integration → E2E → Unit with 90/85/70/50% tiers | Ahead of most teams |
| **Skills for code quality** | `gen-contract-test`, `test-hygiene-scanner`, `e2e-assertion-audit` | Ahead of most teams |
| **Conditional template blocks** | `{{#HAS_MLFLOW}}...{{/HAS_MLFLOW}}` strips when disabled | Uncommon feature |
| **Auto-mirror generation** | `generate-copilot-mirrors.py` creates Copilot instructions from Claude rules | Uncommon automation |
| **CalVer versioning** | All templates follow `YYYY.MM.DD[-N]` | Ahead of most teams |
| **Hook-based enforcement** | Pre-commit hooks for skips, drift, hygiene | Ahead of most teams |

---

## Part 4: Recommended Action Plan

### Phase 1: Critical Missing Domains (Immediate)

1. **Create `_shared/articles/privacy-gdpr.md`** — Data retention, right-to-deletion, minimization, consent, cross-border transfers, PII rules
2. **Create `_shared/articles/rate-limiting.md`** — Token bucket algorithm, per-endpoint tiers, rate limit headers, middleware pattern
3. **Create `_shared/articles/input-security.md`** — CSP, XSS prevention, output encoding, parameterized queries, command injection, CSRF
4. **Create `_shared/articles/production-safety.md`** — Feature flags, canary deployment, rollback procedure, dark launch, traffic shifting
5. **Create `_shared/articles/dependency-security.md`** — Dependabot/Renovate config, CVE SLA, lockfile validation, SBOM
6. **Expand `_shared/articles/security.md`** — JWT algorithm mandate (RS256/ES256), key rotation procedure, revocation, JWKS endpoint
7. **Expand `_shared/articles/async-patterns.md`** — Driver specification, timeout values per service tier, retry exception types, circuit breaker

### Phase 2: Major Domain Expansion

8. **Expand `_shared/frontend/conventions.md`** — a11y rules (aria, keyboard, focus, screen-reader, color contrast)
9. **Create `_shared/articles/logging-observability.md`** — Log levels, JSON schema, required fields, retention, PII redaction, trace/correlation IDs
10. **Create `_shared/articles/health-endpoints.md`** — `/health`, `/ready`, `/live`, dependency validation, graceful shutdown
11. **Create `_shared/articles/documentation-standards.md`** — README template, ADR mandate, OpenAPI completeness, runbook template
12. **Create `_shared/articles/performance-budgets.md`** — Bundle size limits, Core Web Vitals, API latency SLOs, query budgets
13. **Expand `_shared/articles/error-handling.md`** — Canonical `ErrorCode` enum definition, sub-code hierarchy, creation vs reuse guidance

### Phase 3: Template Mechanics & DRY

14. **Add `{{FRAMEWORK}}` placeholder** — Support Vite (default) and Next.js variants in `frontend/conventions.md`
15. **Add `{{HAS_SERVERLESS}}` flag** — Conditional serverless/edge deployment rules
16. **Add `_shared/articles/monorepo.md`** — Workspace conventions, shared packages, dependency graph validation
17. **Add `_shared/articles/mobile.md`** — React Native variant with platform-specific security, navigation, state rules
18. **Extract mirror pair list to JSON** — Single source of truth: `templates/_shared/mirror-pairs.json`, read by `primitive-drift.md`, `check-primitive-drift.sh`, and `bootstrap.sh`
19. **Extract tech stack versions to single file** — `templates/_shared/versions.json` read by all templates, eliminating 10+ duplicate placeholders
20. **Generate `copilot-instructions.md` from Articles** — Instead of hand-written summaries, programmatically summarize `_shared/articles/*.md` into Section 2 of Copilot instructions

### Phase 4: Enforcement Automation

21. **Create `check-constitution.py` template** — AST-based checker for Articles I, II, IV, V, VI violations
22. **Create `check-lint-a11y.sh` hook** — CI hook that runs axe-core or similar on frontend builds
23. **Create `check-dependency-cves.sh` hook** — CI hook that runs `pip-audit` / `npm audit` and blocks high-severity CVEs
24. **Classify every rule** as `MACHINE_ENFORCED` / `HUMAN_REVIEW` / `HEURISTIC` with associated hooks

### Phase 5: Missing Scripts

25. **Create `check-test-hygiene.sh` hook** — Hardcoded dates, AsyncMock misuse, cross-tier truncates, envelope assertions
26. **Create `sync-to-projects.sh`** — Propagate template changes to `influencer-sync`, `nomikailist`, and other downstream repos
27. **Create `check-documentation-coverage.sh`** — Verify README, ADR, API docs exist for changed areas

---

## Appendix: File Length Analysis

| File | Lines | Risk Level |
|------|-------|------------|
| `github-copilot/.github/copilot-instructions.md` | 236 | HIGH — exceeds 4,000 char Code Review limit when rendered |
| `claude-code/.claude/skills/bootstrap-harness/SKILL.md` | 234 | MEDIUM — close to 1,000-line warning threshold |
| `claude-code/CLAUDE.md` | 181 | MEDIUM — borderline for Claude Code session loading |
| `claude-code/AGENTS.md` | 132 | LOW |
| `_shared/articles/testing.md` | 140 | LOW |
| `_shared/articles/sql-standards.md` | 104 | LOW |
| `_shared/articles/frontend/conventions.md` | 80 | LOW |
| `_shared/articles/architecture.md` | 68 | LOW |

**Recommendation**: Split `copilot-instructions.md` into a concise top-level summary (≤150 lines) + scoped `.instructions.md` files for detailed rules.
