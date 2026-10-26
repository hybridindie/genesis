---
read_when: "Starting or finishing a unit of work, or deciding what to do next"
---

# Workflow: Issue → Red → Green → Preflight → PR

One issue per merge. The order is the process; skipping a step is a named
exception, not a shortcut.

## Steps

1. **Issue** — the problem, acceptance criteria, and non-goals. Found a
   defect mid-task? Open an issue; do not bury it in the current PR.
2. **Failing test** — reproduce or pin the behaviour. Confirm it fails for the
   right reason.
3. **Green code** — the minimum change to pass. Refactor separately once green.
4. **Preflight** — lint, types, tests, skip-scan, docs. Fix the cause, never the
   gate.
5. **PR** — one concern, links the issue, states a test plan and verified
   commands.
6. **Review** — address every comment with a change or a reply; unrelated
   findings become linked follow-ups.
7. **Merge** — only with green CI and resolved comments. Squash; delete branch.

## Session discipline

- Start by reading the issue and the relevant rule files (see the rule index).
- Keep a short plan; update it when scope changes.
- Before ending a session: run preflight, summarise what changed and what is
  unverified, leave the tree green.

## ANTI-PATTERNS

- "I'll open the issue later."
- Writing code before the test, then back-filling a test that cannot fail.
- Bundling a refactor, a dependency bump, and a feature.
- Pushing a failing test "to see CI".
- Resolving a review comment with neither a change nor a reply.

## Checklist

- [ ] Issue linked.
- [ ] Red test recorded before the fix.
- [ ] Preflight green locally.
- [ ] PR scope is one concern.
