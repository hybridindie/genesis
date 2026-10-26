<!--
  agent-routing-rules.md — Shared agent routing doctrine
  Referenced by: backend-architect.md, frontend-architect.md,
                 article-compliance-reviewer.md
  Rendered into target projects at .claude/rules/doctrine/agent-routing-rules.md
  version: 1.0.0, owner: John D
  Single source of truth for the "read AGENTS.md first, load rule files"
  preamble shared by all three agents.
-->

# Agent Routing Rules

All three architect/reviewer agents share the same routing preamble. This
file holds it once; the agents reference it instead of restating the
opening.

## Standard routing preamble

1. **Read `AGENTS.md` first** for the current tech stack, architecture
   milestones, and authoritative references.
2. **Load the relevant rule file(s) from `.claude/rules/`** for the topic
   at hand (backend rules under `.claude/rules/backend/`, frontend under
   `.claude/rules/frontend/`, database under `.claude/rules/database/`,
   cross-cutting under `.claude/rules/`).
3. **Before designing or reviewing, grep the codebase** for existing
   patterns under the relevant paths.

## Agent-specific routing (added on top of the preamble)

- **backend-architect**: load `architecture.md`, `api-design.md`,
  `async-patterns.md`, `error-handling.md`, `security.md`, `testing.md`,
  and `database/sql-standards.md` for the topic; grep under
  `{{BACKEND_PATH}}/src/libs/` and `{{BACKEND_PATH}}/app/`.
- **frontend-architect**: load `frontend/conventions.md` and
  `enforcement.md`; grep under `{{FRONTEND_PATH}}/src/`; check the graphify
  report at `{{FRONTEND_PATH}}/src/graphify-out/GRAPH_REPORT.md`.
- **article-compliance-reviewer**: load `enforcement.md` for the PR
  acceptance checklist, then the relevant rule(s) per changed file.

## How callers use this file

- Each agent opens with "Applies `.claude/rules/doctrine/agent-routing-rules.md`"
  and then lists its agent-specific routing. The standard preamble is not
  restated.