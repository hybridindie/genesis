# Template System Configuration

## Overview

This repository contains a unified template system for bootstrapping project-specific AI harnesses across three code-assistant platforms:

- **GitHub Copilot** — `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/rules/`, `.github/agents/`, `.github/prompts/`
- **Claude Code** — `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/scripts/`
- **Opencode** — `.opencode/` ecosystem with skills, commands, and plugins

## Quick Start

### 1. Bootstrap a New Project

**Option A: Interactive Skill (Recommended)**

```bash
# Claude Code
/bootstrap-harness --output-dir "../myproject"

# Opencode
/bootstrap-harness --output-dir "../myproject"
```

The skill will:
1. Scan the project (package.json, pyproject.toml, git repo, directory structure)
2. Show you what it discovered
3. Ask only the questions it couldn't answer automatically (domain, compliance, custom rules)
4. Render the harness and validate it

**Option B: CLI Script (Fast, Deterministic)**

```bash
bash templates/scripts/bootstrap.sh \
  --project-name "MyProject" \
  --project-slug "myproject" \
  --backend-path "backend" \
  --frontend-path "frontend" \
  --repo-org "myorg" \
  --repo-name "myproject" \
  --db-provider "supabase" \
  --state-manager "zustand" \
  --output-dir "../myproject"
```

**Option C: AI Customization Prompt**

Use `templates/scripts/customize-harness.md` as a prompt for deep semantic tailoring (removing articles, adjusting tiers, adding custom rules).

### 2. Render Templates

Templates use `{{PLACEHOLDER}}` syntax. The bootstrap script performs simple string substitution. The AI customization skill performs semantic tailoring (removing irrelevant articles, adjusting coverage tiers, etc.).

### 3. Sync Rule Mirrors

After customizing, run the drift checker to ensure Copilot and Claude rule mirrors stay in sync:

```bash
bash scripts/check-primitive-drift.sh
```

## Placeholder Schema

| Placeholder | Description | Example |
|---|---|---|
| `{{PROJECT_NAME}}` | Human-readable project name | `NomikaiList` |
| `{{PROJECT_SLUG}}` | URL-safe slug | `nomikailist` |
| `{{BACKEND_PATH}}` | Backend directory name | `backend` |
| `{{FRONTEND_PATH}}` | Frontend directory name | `frontend` |
| `{{REPO_ORG}}` | GitHub organization / user | `hybridindie` |
| `{{REPO_NAME}}` | Repository name | `nomikailist` |
| `{{PYTHON_VERSION}}` | Python minor version | `3.12` |
| `{{FASTAPI_VERSION}}` | FastAPI version | `0.119+` |
| `{{REACT_VERSION}}` | React major version | `19` |
| `{{TYPESCRIPT_VERSION}}` | TypeScript version | `5.9` |
| `{{VITE_VERSION}}` | Vite version | `7.3` |
| `{{DB_PROVIDER}}` | Database provider (`supabase` or `postgres`) | `supabase` |
| `{{STATE_MANAGER}}` | Frontend state manager | `zustand` |
| `{{TEST_BACKEND_CMD}}` | Backend test command | `uv run pytest` |
| `{{TEST_FRONTEND_CMD}}` | Frontend test command | `npx vitest run` |
| `{{LINT_BACKEND_CMD}}` | Backend lint command | `uv run ruff check .` |
| `{{LINT_FRONTEND_CMD}}` | Frontend lint command | `npm run lint` |
| `{{TYPE_BACKEND_CMD}}` | Backend type check | `uv run mypy src/` |
| `{{TYPE_FRONTEND_CMD}}` | Frontend type check | `npm run type-check` |
| `{{PKG_MANAGER_BACKEND}}` | Backend package manager | `uv` |
| `{{PKG_MANAGER_FRONTEND}}` | Frontend package manager | `npm` |
| `{{COVERAGE_AGGREGATE_BACKEND}}` | Aggregate backend coverage | `70` |
| `{{COVERAGE_AGGREGATE_FRONTEND}}` | Aggregate frontend coverage | `60` |
| `{{CALVER_VERSION}}` | Initial CalVer version | `2026.05.09` |
| `{{ARTICLE_I_SERVICE_EXAMPLES}}` | Example library names (comma list) | `auth_manager, analytics_engine, content_manager` |
| `{{FRONTEND_STORE_EXAMPLES}}` | Example Zustand store names | `auth, analytics, content` |
| `{{DB_EXTENSIONS}}` | PostgreSQL extensions | `pgvector, pgmq, HSTORE` |
| `{{HAS_MLFLOW}}` | Include MLflow article (`yes`/`no`) | `no` |
| `{{HAS_LANGGRAPH}}` | Include LangGraph article (`yes`/`no`) | `no` |
| `{{CICD_PLATFORM}}` | CI/CD platform | `github-actions` |
| `{{E2E_TOOL}}` | E2E testing tool | `playwright` |
| `{{UI_LIBRARY}}` | UI component library | `shadcn/ui` |
| `{{TAILWIND}}` | Uses Tailwind CSS (`yes`/`no`) | `yes` |
| `{{ZOD_VALIDATION}}` | Uses Zod validation (`yes`/`no`) | `yes` |
| `{{CUSTOM_INSTRUCTIONS}}` | Freeform custom rules block | *(empty or project-specific)* |
| `{{CUSTOM_TECH_STACK}}` | Freeform tech stack additions | *(empty or project-specific)* |

## File Manifest

### Shared Constitutional Articles (rendered into all three harnesses)

| File | Description | Target Paths |
|---|---|---|
| `_shared/articles/architecture.md` | Article I & II: Library-first, service isolation | `.claude/rules/backend/architecture.md` + `.github/instructions/backend-architecture.instructions.md` |
| `_shared/articles/testing.md` | Article III: TDD mandate, coverage tiers | `.claude/rules/backend/testing.md` + `.github/instructions/backend-testing.instructions.md` |
| `_shared/articles/error-handling.md` | Article IV: Structured errors | `.claude/rules/backend/error-handling.md` + `.github/instructions/backend-error-handling.instructions.md` |
| `_shared/articles/async-patterns.md` | Article V: Async-first | `.claude/rules/backend/async-patterns.md` + `.github/instructions/backend-async-patterns.instructions.md` |
| `_shared/articles/api-design.md` | Article VI: OpenAPI & Pydantic | `.claude/rules/backend/api-design.md` + `.github/instructions/backend-api-design.instructions.md` |
| `_shared/articles/security.md` | Article VII: Secure-by-default | `.claude/rules/backend/security.md` + `.github/instructions/backend-security.instructions.md` |
| `_shared/articles/cicd.md` | Article VIII: CI/CD integrity | `.claude/rules/cicd.md` + `.github/instructions/cicd.instructions.md` |
| `_shared/articles/enforcement.md` | Article IX: Enforcement gates, PR checklist, versioning | `.claude/rules/enforcement.md` + `.github/instructions/enforcement.instructions.md` |
| `_shared/articles/primitive-drift.md` | Mirror sync rule | `.github/instructions/primitive-drift.instructions.md` |
| `_shared/database/sql-standards.md` | PostgreSQL schema standards | `.claude/rules/database/sql-standards.md` + `.github/instructions/database-sql-standards.instructions.md` |
| `_shared/database/infrastructure.md` | PostgreSQL-only infra | `.claude/rules/database/infrastructure.md` + `.github/instructions/database-infrastructure.instructions.md` |
| `_shared/frontend/conventions.md` | React/TypeScript conventions | `.claude/rules/frontend/conventions.md` + `.github/instructions/frontend-conventions.instructions.md` |

### Harness-Specific Templates

| Harness | File | Description |
|---|---|---|
| GitHub Copilot | `.github/copilot-instructions.md` | Master Copilot instructions |
| GitHub Copilot | `.github/agents/ux-researcher.agent.md` | UX research agent |
| GitHub Copilot | `.github/agents/implementation-designer.agent.md` | Implementation designer agent |
| GitHub Copilot | `.github/prompts/pre-merge-verify.prompt.md` | Pre-merge verification prompt |
| GitHub Copilot | `.github/CUSTOMIZATIONS.md` | Customization system doc |
| Claude Code | `CLAUDE.md` | Thin `@AGENTS.md` + `@my-workflows.md` import, Claude-only notes |
| Claude Code | `AGENTS.md` | Canonical project context (shared with every harness) |
| Claude Code | `.claude/commands/preflight.md` | Local CI checks command |
| Claude Code | `.claude/commands/migration-check.md` | Migration validation command |
| Claude Code | `.claude/agents/backend-architect.md` | Backend architect agent |
| Claude Code | `.claude/agents/frontend-architect.md` | Frontend architect agent |
| Claude Code | `.claude/agents/article-compliance-reviewer.md` | Compliance reviewer agent |
| Claude Code | `.claude/skills/gen-contract-test/SKILL.md` | Contract test generator skill |
| Claude Code | `.claude/skills/create-migration/SKILL.md` | Migration scaffolder skill |
| Claude Code | `.claude/skills/test-hygiene-scanner/SKILL.md` | Test hygiene scanner skill |
| Claude Code | `.claude/skills/e2e-assertion-audit/SKILL.md` | E2E assertion audit skill |
| Claude Code | `.claude/hooks/check-no-skipped-tests.sh` | Skip/xfail pre-commit hook |
| Claude Code | `.claude/hooks/check-primitive-drift.sh` | Mirror drift hook |
| Claude Code | `.claude/hooks/check-agent-drift.sh` | Agent version drift hook |
| Claude Code | `.claude/scripts/bash/bootstrap.sh` | Feature bootstrap script |
| Claude Code | `.claude/scripts/bash/check-task-prerequisites.sh` | Task prerequisite checker |
| Opencode | `.opencode/opencode.json` | Opencode config (instructions + v2 permissions) |
| Opencode | `.opencode/commands/graphify.md` | Graphify CLI command |
| Opencode | `.opencode/skills/gen-contract-test/SKILL.md` | Contract test generator |
| Opencode | `.opencode/skills/create-migration/SKILL.md` | Migration scaffolder |
| Opencode | `.opencode/skills/test-hygiene-scanner/SKILL.md` | Test hygiene scanner |
| Opencode | `.opencode/skills/e2e-assertion-audit/SKILL.md` | E2E assertion audit |
| Opencode | `.opencode/commands/preflight.md` | Local CI checks command |
| Opencode | `.opencode/commands/migration-check.md` | Migration validation command |
| Opencode | `.opencode/agents/backend-architect.md` | Backend architect agent |
| Opencode | `.opencode/agents/frontend-architect.md` | Frontend architect agent |
| Opencode | `.opencode/agents/article-compliance-reviewer.md` | Compliance reviewer agent |
| Opencode | `AGENTS.md` | Canonical context (auto-discovered) |

## Customization Modes

### Mode A: Bootstrap Script (Fast, Deterministic)

Best for: Standard TypeScript/React + Python/FastAPI projects with no special infrastructure.

Replaces placeholders with provided values. Does NOT remove optional articles.

### Mode B: AI Customization Skill (Semantic, Adaptive)

Best for: Projects with special infrastructure (MLflow, LangGraph, custom queues), unusual constraints, or non-default stacks.

The AI reads the full template, asks clarifying questions, then:
1. Removes irrelevant articles (e.g., drops MLflow article if `{{HAS_MLFLOW}}=no`)
2. Adjusts coverage tiers based on project criticality
3. Rewrites example library names to match domain
4. Adds custom rules block
5. Suggests additional hooks or agents

## Post-Customization Drift Checks

After rendering templates into a project, always run:

```bash
# Mirror sync (Claude <-> Copilot rules)
bash .claude/hooks/check-primitive-drift.sh

# Agent version sync (stack versions in agents vs AGENTS.md)
bash .claude/hooks/check-agent-drift.sh

# Test hygiene scan
bash .claude/hooks/check-test-hygiene.sh
```

## Updating the Templates

When a rule changes across all projects:
1. Edit the `_shared/` source of truth.
2. Run `bash templates/scripts/sync-to-projects.sh` to propagate to `influencer-sync`, `nomikailist`, etc.
3. Verify with drift checker.

## Versioning

Templates follow CalVer: `YYYY.MM.DD[-N]`.
Current: {{CALVER_VERSION}}.
