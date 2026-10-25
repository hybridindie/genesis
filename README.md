# AI Harness Genesis

**Constitutional AI instruction templates for Python (FastAPI, Flask, MCP) and TypeScript (React, Next.js) projects — plus a machine setup layer for the shell and the user-level agent rules.**

Generate equivalent instruction harnesses for GitHub Copilot, Claude Code, and Opencode with a single command. Templates codify Articles I–X (library-first architecture, TDD mandate, structured errors, async-first, API contracts, security, CI integrity, enforcement, caching) plus twelve extended articles, PostgreSQL schema standards, frontend conventions, and a complete workflow pipeline.

## Two layers

| Layer | Entry point | Installs into |
|-------|-------------|---------------|
| **System** (this machine) | `system/install.sh` | `~/.config/zsh`, `~/.config/opencode/AGENTS.md`, `~/.claude/{CLAUDE.md,settings.json}`, shared git config, optional Herdr/Zed |
| **Project** (one repo) | `install.sh`, `new-project.sh`, `/bootstrap-harness` | the target project's `.claude/`, `.github/`, `.opencode/` |

New machine: clone, then `bash system/install.sh`. New project:
`./new-project.sh myapp`. The full flow (machine → project → `/harness-eval` →
`/customize-harness`) is in [`SYSTEM.md`](SYSTEM.md); the system layer's details
and flags are in [`system/README.md`](system/README.md). Both are platform-aware
(macOS + Linux) and never overwrite a differing file without `--force`.

## Install — one command (recommended)

The repo is public, so from inside the project you want to tailor:

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/genesis/main/install.sh | bash
```

This fetches the genesis repo and renders a harness tailored to the current
directory via auto-detection — no clone, no auth. For the interactive
plan-review path (Claude Code / Opencode) and all other routes, see
[`INSTALL.md`](INSTALL.md).

## Install with AI

Clone this repo once. Then use the `install-harness` agent from any project:

**Claude Code:**
```
# Open this genesis repo in Claude Code, then:
@install-harness /absolute/path/to/your-project
```

**GitHub Copilot:**
```
# Open this genesis repo in VS Code, then use the install-harness agent:
@install-harness /absolute/path/to/your-project
```

The agent will:
1. Inspect the target project (stack, language, versions, dependencies)
2. Show an **install plan** — what will be included and what will be omitted
3. Ask for confirmation before running
4. Run bootstrap, evaluate the harness fit (`/harness-eval`), and tailor (`/customize-harness`)
5. Report what was created

## Quick Start (CLI)

```bash
# 1. Auto-detect (recommended) — probes project, infers mode/profile, asks only unknowns
cd your-project
bash /path/to/genesis/templates/scripts/bootstrap.sh --auto-detect --output-dir .

# 2. Manual CLI (supply all values)
bash /path/to/genesis/templates/scripts/bootstrap.sh \
  --project-name "YourProject" \
  --project-slug "yourproject" \
  --mode "full" \
  --profile "fastapi" \
  --has-mlflow "no" \
  --has-langgraph "no" \
  --has-nextjs "no" \
  --output-dir "."
```

### Post-bootstrap flow

```
bootstrap.sh     → render (deterministic: placeholders + overlays + conditionals)
    ↓
/harness-eval    → agent reads the actual code, evaluates stack-fit,
                    trims rules that don't apply, suggests missing rules
    ↓
/customize-harness → agent tailors domain examples, coverage tiers,
                      weaves my-workflows.md conventions
```

Both approaches produce:
- `.claude/rules/` — Constitutional Articles I–X + doctrine (source of truth)
- `.github/instructions/` — Auto-mirrored Copilot instructions
- `.github/copilot-instructions.md` — Repo-wide Copilot guidance
- `AGENTS.md` — Canonical project context (read natively by OpenCode; imported by `CLAUDE.md`)
- `CLAUDE.md` — Thin `@AGENTS.md` + `@my-workflows.md` import plus Claude-specific notes
- `my-workflows.md` — Your cross-project conventions, loaded by OpenCode and imported by Claude
- `.opencode/` — Equivalent skills, commands, agents, plugins
- `.claude/skills/` + `.opencode/skills/` — utility skills + `customize-harness`
- `docs/harness-eval.md` — evaluation prompt for `/harness-eval`
- `my-workflows.md` — an editable copy of your cross-project conventions

### What installs vs. what's repo-hosted

This repo is two things. **What `bootstrap.sh` installs into a target project** is
the *constitutional harness* (Articles, rules, agents, commands, utility skills,
doctrine, harness-eval). The **Epic Scoping Skills** (`epic-composer`,
`story-decomposer`, `task-decomposer`, …) are a *separate, repo-hosted*
capability: they live under `.agents/` and run in this genesis repo. See
[`AGENTS.md`](AGENTS.md) for the full architecture.

## Architecture

### Single source, thin wrappers

Two systems share the same pattern:

- **Genesis harness**: `templates/_shared/` → rendered into target projects by `bootstrap.sh`. Articles, agents, commands, doctrine, and shippable skills.
- **Epic Scoping Skills**: `.agents/` → thin wrappers in `.claude/`, `.opencode/`, `.github/`. Skills, doctrine, templates, evals.

**Golden rule:** Edit content in `.agents/` (epic skills) or `templates/_shared/` (genesis). Edit frontmatter in the harness wrappers. Never duplicate content into a wrapper. Shared rules referenced by multiple files live in a `doctrine/` layer — reference, don't restate.

### Articles and doctrine

| File | Article | Topic |
|------|---------|-------|
| `articles/architecture.md` | I & II | Library-first, service isolation |
| `articles/testing.md` | III | TDD mandate, tiered coverage |
| `articles/error-handling.md` | IV | Structured errors, DomainError envelope |
| `articles/async-patterns.md` | V | Async-first, concurrency, atomicity |
| `articles/api-design.md` | VI | OpenAPI, Pydantic models, route delegation |
| `articles/security.md` | VII | OAuth2/JWT, AES-256, secret hygiene |
| `articles/cicd.md` | VIII | CI gates, deterministic builds |
| `articles/enforcement.md` | IX | PR checklist, enforcement gates, versioning |
| `articles/caching-strategy.md` | X | PG NOLOG tables, materialized views, HTTP cache headers |
| `articles/workflow.md` | — | Step-by-step workflow pipeline (#1–7) |
| `database/sql-standards.md` | — | PostgreSQL schema conventions |
| `database/infrastructure.md` | — | PostgreSQL-only infrastructure |
| `frontend/conventions.md` | — | React/TypeScript/Vite conventions |

### Extended articles (shipped, unnumbered)

Topic-scoped articles that ship alongside Articles I–X when the stack needs them:

| File | Topic |
|------|-------|
| `articles/agentic-workflow.md` | Agentic Continuous Delivery (ACD) |
| `articles/dependency-security.md` | Dependency and supply-chain security |
| `articles/documentation-standards.md` | Documentation and ADR standards |
| `articles/error-budgets.md` | Error budgets and SLOs |
| `articles/health-endpoints.md` | Health, readiness and liveness endpoints |
| `articles/input-security.md` | Input sanitisation, XSS and injection |
| `articles/logging-observability.md` | Logging, observability and telemetry |
| `articles/performance-budgets.md` | Performance budgets and SLOs |
| `articles/primitive-drift.md` | Rule/instruction mirror sync |
| `articles/privacy-gdpr.md` | Privacy and GDPR |
| `articles/production-safety.md` | Feature flags, canaries, rollbacks |
| `articles/rate-limiting.md` | Rate limiting and throttling |

Shared rules referenced by multiple articles/agents live in
`templates/_shared/doctrine/` (genesis) and `.agents/doctrine/` (epic skills).
Each doctrine module is a single source of truth — edit once, all references
inherit.

### Profile overlays

Some articles have profile-specific variants that replace the base article
when the profile is selected:

| Profile | Overlays | What changes |
|---------|----------|-------------|
| `flask` | 5 (architecture, api-design, testing, async-patterns, error-handling) | Flask blueprints, sync-first, test client, error handlers |
| `mcp` | 2 (architecture, api-design) | MCP tools, resources, prompts, async server |
| `nextjs` (`--has-nextjs yes`) | 1 (frontend/conventions) | App Router, Server Components, Server Actions |

`fastapi` (the default) and `generic-python` (the fallback) have no overlays — the
base articles apply as rendered.

### Mirror System

`.claude/rules/*.md` (Claude) and `.github/instructions/*.instructions.md` (Copilot) are **body-identical mirrors**. `generate-copilot-mirrors.py` creates Copilot mirrors from Claude rules. `check-primitive-drift.sh` detects mirror drift.

### Three harnesses, one canonical context

| Platform | Entry Files | Ecosystem |
|----------|-------------|-----------|
| **OpenCode (primary)** | `AGENTS.md` (auto-discovered) + `my-workflows.md` (`instructions`) | `.opencode/skills/`, `.opencode/commands/`, `.opencode/agents/` |
| **Claude Code** | `CLAUDE.md` (`@AGENTS.md`, `@my-workflows.md`) | `.claude/rules/`, `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/hooks/` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/instructions/`, `.github/agents/`, `.github/prompts/` |

Rules live once in `.claude/rules/`. Claude scopes them by `paths:` frontmatter;
OpenCode reads them on demand through the **rule index** in `AGENTS.md` — it does
not load the directory eagerly.

### Permission defaults

Generated harnesses ship least-privilege defaults, not just prose:

- **Opencode** — a v2 ordered `permissions` array in `.opencode/opencode.json`.
- **Claude Code** — `.claude/settings.json` with `deny` / `ask` / `allow` rules.

Routine commands are allowed, destructive ones (`sudo`, `rm -rf`, package installs,
force-push, `direnv allow`) ask first, and credential paths (`~/.ssh`, `~/.aws`,
`~/.kube`, `**/.env`) are denied. Patterns are prefix matches, not a sandbox.

## Placeholder Schema

Templates use `{{PLACEHOLDER}}` syntax with `{{#FLAG}}...{{/FLAG}}` conditional blocks:

| Placeholder | Default | Description |
|-------------|---------|-------------|
| `{{PROJECT_NAME}}` | — | Human-readable project name |
| `{{PROJECT_SLUG}}` | — | URL-safe slug |
| `{{BACKEND_PATH}}` | `backend` | Backend directory name |
| `{{FRONTEND_PATH}}` | `frontend` | Frontend directory name |
| `{{PYTHON_VERSION}}` | `3.12` | Python minor version |
| `{{FASTAPI_VERSION}}` | `0.119+` | FastAPI version |
| `{{REACT_VERSION}}` | `19` | React major version |
| `{{STATE_MANAGER}}` | `zustand` | Frontend state manager |
| `{{DB_PROVIDER}}` | `supabase` | Database provider |
| `{{HAS_MLFLOW}}` | `no` | Include MLflow Prompt Registry rules |
| `{{HAS_LANGGRAPH}}` | `no` | Include LangGraph agent rules |
| `{{HAS_NEXTJS}}` | `no` | Use Next.js frontend overlay (App Router, Server Components) |
| `{{HAS_SUPABASE}}` | derived | Supabase-specific local-dev commands in AGENTS.md |
| `{{HAS_POSTGRES}}` | derived | Raw-postgres local-dev commands in AGENTS.md |
| `{{COVERAGE_AGGREGATE_BACKEND}}` | `70` | Aggregate backend coverage target |
| `{{CALVER_VERSION}}` | today's date | Initial CalVer version |

When a flag is `no`, `process-conditionals.py` strips the entire `{{#FLAG}}...{{/FLAG}}` block.

## Tech Stack Support

| Profile | Backend | Frontend | Database | Detected By |
|---------|---------|----------|----------|-------------|
| `fastapi` (default) | FastAPI, Pydantic | React 19, TS, Vite (or Next.js) | PostgreSQL / Supabase | `pyproject.toml` + `package.json` |
| `flask` | Flask | React 19, TS, Vite (or Next.js) | PostgreSQL / Supabase | `flask` in deps |
| `mcp` | MCP server, Pydantic | None | None (stateless) | `mcp` in `pyproject.toml` deps |
| `generic-python` | Python (no framework) | Optional | Optional | Fallback |

**Frontend:** React + TypeScript + Vite (default), or Next.js (`--has-nextjs yes`).
**Package managers:** uv (Python), npm or Bun (frontend).
**Database:** PostgreSQL only — Supabase or raw postgres. No Redis, no external caches (caching via PG NOLOG tables — Article X).

## Built-in Skills

| Skill | Platforms | Purpose |
|-------|-----------|---------|
| `bootstrap-harness` | Claude, Opencode | Interactive project scanner + renderer + evaluation + tailoring |
| `customize-harness` | Claude, Opencode | Semantic domain tailoring (rename examples, adjust tiers, weave workflows) |
| `gen-contract-test` | Claude, Opencode | Scaffold contract tests (TDD Article III) |
| `create-migration` | Claude, Opencode | Supabase SQL migration scaffolding |
| `test-hygiene-scanner` | Claude, Opencode | Find hardcoded dates, AsyncMock misuse, cross-tier truncates |
| `e2e-assertion-audit` | Claude, Opencode | Flag no-op assertions in E2E tests |

## Commands

| Command | Purpose |
|---------|---------|
| `/preflight` | Run all CI-equivalent checks before pushing |
| `/start-session` | Start an ACD implementation session |
| `/end-session` | Close a session — validate gates, commit |
| `/fix` | Pipeline is red — diagnose and restore green |
| `/migration-check <file>` | Validate a migration against sql-standards.md |
| `/harness-eval` | Evaluate harness stack-fit, trim, suggest missing rules |

## Epic Scoping Skills

A separate skill suite turns raw source material into implementable,
parallel-first backlogs. Shared content lives in `.agents/`.

| Skill | Command | Purpose |
|-------|---------|---------|
| `epic-composer` | `/epic-composer` | Synthesize sources into an outcome-driven Epic |
| `epic-interview` | `/epic-interview` | Close critical gaps before drafting |
| `epic-acceptance-linter` | `/epic-acceptance-linter` | Lint acceptance-criteria quality |
| `story-decomposer` | `/story-decomposer` | Decompose a ready Epic into INVEST stories |
| `task-decomposer` | `/task-decomposer` | Break a story into AI-executable tasks |

See **[`prompts-skills.md`](prompts-skills.md)** for the full guide and
**[`AGENTS.md`](AGENTS.md)** for the concise cross-harness entrypoint.

## Updating the Harness

### When a rule changes in the genesis repo

1. Edit the source: `templates/_shared/articles/<name>.md` (or `doctrine/`, `agents/`, `commands/`).
2. Re-run bootstrap into target projects: `bash templates/scripts/bootstrap.sh --auto-detect --output-dir <target>`.
3. Run drift check: `bash .claude/hooks/check-primitive-drift.sh`.
4. In each target project: run `/harness-eval` to re-trim for the project's stack, then `/customize-harness` to re-tailor.

### When the project's stack changes

1. Run `/harness-eval` — the agent reads the new stack, trims rules that no longer fit, suggests rules the new stack needs.
2. Run `/customize-harness` — re-tailors domain examples and workflows.
3. Optionally re-run `bootstrap.sh --auto-detect` if new profile overlays apply (e.g. switched from Vite to Next.js).

### Editing contract

- **Articles/agents/commands**: edit in `templates/_shared/`. Re-run bootstrap to re-render.
- **Doctrine**: edit in `templates/_shared/doctrine/` (genesis) or `.agents/doctrine/` (epic skills). All references inherit.
- **Frontmatter**: edit in the harness wrappers (`.claude/`, `.opencode/`, `.github/`), not in `.agents/`.
- **Versioning**: bump `version:` in each file's header comment (patch/minor/major). See [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md).
- **Drift**: `check-primitive-drift.sh` catches mirror desync. `warn-pointer-edit` hooks warn on editing wrappers or doctrine.

## Context Budget

**In a rendered project** — OpenCode loads `AGENTS.md` (~6KB) plus
`my-workflows.md` (~4KB) and reads rule files on demand via the rule index
(~2.5K tokens of entry context). Claude loads the thin `CLAUDE.md`
(`@AGENTS.md` + `@my-workflows.md`) and path-scoped rules, which load only when
matching files are touched. Before the restructure, OpenCode eagerly loaded all
30 rule files (~83KB, ~21K tokens) and never saw the project context.

**This repo's own harness** — ~7.6KB across `AGENTS.md`, `CLAUDE.md` and
`.claude/CLAUDE.md`; reference sections are lazy-loaded from
`docs/agents-sections/`. Full pipeline runs (all skills + doctrine + rubrics +
templates) peak at ~18K tokens (9.2% of a 200K window).

## Versioning

Templates follow CalVer: `YYYY.MM.DD[-N]`. Epic-scoping files carry a `version: x.y.z` in their header comment — see [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md) for the bump policy.

## License

MIT — see [`LICENSE`](LICENSE).