# Harness Evaluation

Post-bootstrap evaluation prompt. Run this after `bootstrap.sh` has rendered
the harness into a project. The agent reads the project's actual code and
dependencies, evaluates whether each rendered rule fits the project's stack,
trims what doesn't apply, and suggests rules the project needs but doesn't
have.

This is the semantic complement to bootstrap's deterministic rendering:
bootstrap does placeholder substitution and adds the selected profile's rules; this does
stack-fit analysis and gap detection. Run it with `/harness-eval` or
reference this file with `@docs/harness-eval.md`.

---

## Your role

You are a harness engineer evaluating an already-installed AI harness against
the project it was installed into. The bootstrap render is deterministic — it
substitutes placeholders and adds the profile's rules, but it cannot read the
project's actual code or understand semantics. You can. Your job is to close
the gap between what bootstrap rendered and what the project actually needs.

## What you have

- The project's codebase (read it — `package.json`, `pyproject.toml`, source
  files, config files, directory structure).
- The rendered harness files (`AGENTS.md` is the canonical context; `CLAUDE.md`
  is a thin `@AGENTS.md` import; `.claude/rules/`, `.claude/agents/`,
  `.claude/commands/`, `.claude/skills/`, and the `.opencode/` equivalents).
- The project's `my-workflows.md` if present (loaded by OpenCode, imported by
  `CLAUDE.md`).

## Phase 1 — Stack discovery

Read the project and determine the actual stack. Don't rely on what bootstrap
detected — verify against the code:

- **Backend framework**: FastAPI? Flask? MCP? Something else? Read the
  imports and entry points.
- **Frontend framework**: React+Vite? Next.js? None? Read `package.json`
  and the app directory structure.
- **Database**: Supabase? Raw PostgreSQL? Something else? Read
  `supabase/config.toml`, `docker-compose.yml`, or connection strings.
- **Package managers**: uv? pip? npm? bun? Read lockfiles.
- **Test framework**: pytest? vitest? Read test files and configs.
- **Special infra**: MLflow? LangGraph? pgvector? pgmq? Background workers?
  File uploads? Search functionality? Read deps and source.

Produce a one-paragraph stack summary. If the detected stack differs from what
the harness assumes (e.g. harness says FastAPI but the project is Flask),
flag it explicitly.

## Phase 2 — Stack-fit evaluation

For each rendered rule file in `.claude/rules/`, evaluate whether its
content matches the project's actual stack. Check:

- Does the article reference a framework the project doesn't use?
  (e.g. FastAPI-specific advice in a Flask project)
- Does the article reference infrastructure the project doesn't have?
  (e.g. supabase CLI commands in a raw-postgres project)
- Does the article reference a testing tool the project doesn't use?
  (e.g. pytest fixtures in a project that uses a different test runner)
- Is the article's `paths:` frontmatter relevant to the project's file
  structure?

Produce a stack-fit table:

```
| Article | Matches stack? | Issue | Action |
|---------|---------------|-------|--------|
| backend/api-design.md | No | References FastAPI/Pydantic; project is Flask | Replace with Flask variant or trim FastAPI sections |
| backend/architecture.md | Yes | Matches FastAPI project | Keep |
| database/sql-standards.md | No | References supabase migrations; project uses raw psql | Trim supabase-specific sections |
| frontend/conventions.md | N/A | Project is backend-only | Remove |
```

## Phase 3 — Trim

For each article that doesn't match the stack, propose one of:

- **Remove** — the article doesn't apply at all (e.g. frontend rules in a
  backend-only project). Delete the file and remove its row from the
  `AGENTS.md` rule index (and any mention elsewhere).
- **Trim** — the article is partially relevant but contains wrong sections.
  Remove the wrong sections, keep the rest. (e.g. remove supabase-specific
  migration commands from sql-standards.md, keep the general SQL rules.)
- **Replace** — a profile overlay exists but wasn't applied. Apply it
  manually (copy the overlay content over the rendered file). (e.g. if
  bootstrap didn't apply the Flask overlay, do it now.)
- **Keep** — the article matches. No change.

Also trim the `AGENTS.md` **rule index** to match: a deleted rule must lose its
row; a rule that no longer applies to a path should say so.

Present the trim plan grouped by action. Ask the user to confirm before
deleting or editing any file.

## Phase 4 — Suggest missing rules

Based on what the project actually uses (detected from code and deps),
suggest rules the project needs but the harness doesn't have:

- **Background jobs**: does the project have queue consumers, workers, or
  scheduled tasks? If so, are there rules for retry, dead-letter, idempotency?
- **Search**: does the project use pgvector, full-text search, or a search
  API? If so, are there rules for index design, query patterns, relevance?
- **File uploads**: does the project handle file uploads or S3 storage? If
  so, are there rules for signed URLs, size limits, malware scanning?
- **Multi-tenancy**: does the project have tenant isolation, RLS, or
  per-tenant schemas? If so, are there rules for tenant routing, data
  isolation?
- **Real-time**: does the project use WebSocket, SSE, or LISTEN/NOTIFY?
  If so, are there rules for connection management, reconnection?
- **API versioning**: does the project have multiple API versions or
  deprecation headers? If so, are there rules for backward compatibility?
- **Feature flags**: does the project use feature flags? If so, are there
  rules for naming, rollout, cleanup, tech debt?
- **Caching**: does the project cache data? If so, are there rules for the
  caching strategy (NOLOG tables, materialized views, HTTP cache headers)?

For each gap, suggest:
- A one-line description of the missing rule
- Which existing article it should live in (if any) or whether it needs a
  new article
- A stub of what the rule should say (2-3 bullet points)

Don't create the files yet — just list the suggestions. The user picks which
ones to implement.

## Phase 5 — Report

Produce the final report:

```
## Harness Evaluation Report

### Stack detected
<one paragraph>

### Stack-fit issues
<table from Phase 2>

### Trim actions
<list of remove/trim/replace/keep from Phase 3>

### Missing rules
<list of suggestions from Phase 4>

### Recommended next steps
1. Apply trim actions (confirm)
2. Implement missing rules (pick which ones)
3. Run /customize-harness to tailor domain examples and workflows
```

## Rules

- **Read the actual code** — don't rely on bootstrap's detection. Open
  files, read imports, check configs. The whole point is that the agent can
  do what bootstrap can't.
- **Propose, don't execute** — present the plan in Phases 2-4, confirm with
  the user, then apply in Phase 3. Never delete or edit files without
  confirmation.
- **Be specific** — don't say "this article doesn't fit." Say "this article
  references `Depends()` and `async def` handlers, but the project uses Flask
  with sync handlers and `current_app` injection."
- **Suggest, don't fabricate** — for missing rules, suggest what should
  exist. Don't invent rules that sound plausible but have no basis in the
  project's actual needs.
- **Respect the golden rule** — if editing rule content, edit the
  `.claude/rules/` files (the rendered copies in the target project). Don't
  touch `templates/` or the genesis repo.

## Format contract

The harness has established conventions. When you trim, edit, or create
rule files, maintain them. Breaking these causes drift across harnesses
and confusing the model that loads the rules.

### Article structure

Every rule file in `.claude/rules/` follows this shape:

```markdown
---
read_when: "One short sentence: when an agent should open this rule"
paths:                      # optional; Claude Code uses it for path scoping
  - "backend/src/**/*.py"
---

# <Title>

## MUST
- <hard rules>

## SHOULD
- <soft rules>

## ANTI-PATTERNS (BLOCKING)
- <forbidden patterns>

## Checklist
- [ ] <checklist items>
```

`read_when` is required: `AGENTS.md` is rebuilt from it and CI fails if a rule
lacks one. `paths` is optional and only meaningful to Claude Code. Preserve the
MUST / SHOULD / ANTI-PATTERNS / Checklist headings when trimming.

### Frontmatter paths

The `paths:` frontmatter tells Claude Code when to auto-load
the rule based on the file being edited. When you trim an article:
- If the article no longer applies at all, remove it (and its paths).
- If you trim a section, update the paths to match what the article still
  covers.
- Use `{{BACKEND_PATH}}` / `{{FRONTEND_PATH}}` placeholders in paths —
  bootstrap substitutes them. In a rendered project these are already
  replaced with concrete values (e.g. `backend/`).

### The golden rule: reference, don't restate

The harness has a doctrine layer (`.claude/rules/doctrine/`) holding
shared rules referenced by multiple articles and agents. When you add or
edit content:
- If a rule is shared across 2+ articles, it belongs in `doctrine/` —
  create or edit a doctrine file and reference it, don't inline the rule.
- If a rule is specific to one article, keep it inline.
- Never duplicate a rule that already lives in `doctrine/` — reference the
  path instead: `Applies .claude/rules/doctrine/<name>.md`.

### Cross-harness sync

The harness targets two platforms: **OpenCode (primary)** and Claude Code.
`AGENTS.md` is the canonical context; `CLAUDE.md` imports it.
When you add, remove, or rename a rule file:

| Action | OpenCode (primary) | Claude Code | AGENTS.md (canonical) |
|--------|--------------------|-------------|-----------------------|
| **Add article** | Add a row to the rule index — rules are read on demand, never eagerly loaded | Create `.claude/rules/<path>/<name>.md` | Add to Authoritative References if top-level |
| **Remove article** | Remove the index row | Delete `.claude/rules/<path>/<name>.md` | Remove from references if listed |
| **Trim article** | Update the index row only if its "read when" changed | Edit `.claude/rules/<path>/<name>.md` in place | No change unless the trim removes a referenced capability |
| **Add doctrine** | Nothing — read only when a rule points to it | Create `.claude/rules/doctrine/<name>.md` | No change |

If you're in a rendered target project (not the genesis repo), the OpenCode
agent/command mirrors are generated from the Claude sources — edit the shared
source and re-run bootstrap, or keep the pair in sync manually.

### AGENTS.md references

`AGENTS.md` is canonical and holds the **rule index** plus the
"Authoritative References" and "Tech Stack" sections. When you remove an
article, remove its index row and any reference. When you add an article, add
its index row with a clear "read when" trigger — this is how OpenCode finds
rules without loading them eagerly. Keep `CLAUDE.md` thin: it should only
import `AGENTS.md` / `my-workflows.md` and carry Claude-specific notes.

### Agent files

If the stack change affects how an agent should behave (e.g. switching from
FastAPI to Flask changes the backend-architect's routing rules), also
propose edits to `.claude/agents/<agent>.md`. The agents reference doctrine
files by path — if you add or remove a doctrine file, update the agent's
references to match.

## When to run this

- After `bootstrap.sh` renders the harness into a new project.
- After a major stack change (e.g. migrating from Vite to Next.js, adding
  Flask alongside FastAPI, switching from supabase to raw postgres).
- Before `/customize-harness` — trimming and gap-filling should happen
  before domain tailoring.
- Anytime the user asks "evaluate the harness" or "does this harness fit
  my project?"