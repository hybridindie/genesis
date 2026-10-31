---
read_when: "Starting or finishing a unit of work, opening or reviewing a PR, or deciding what to do next"
---

# Workflow: Issue → Red → Green → Preflight → PR → Merge

The issue is the spec. One issue per PR. Skipping a step is a stated
exception, not a shortcut.

## Steps

1. **Issue** — problem, acceptance criteria, non-goals. A defect found
   mid-task becomes a new issue, not part of this PR.
2. **Red** — a failing test that pins the behaviour (see `testing.md`).
3. **Green** — the smallest change that passes. Refactor in a separate commit
   or PR once green.
4. **Preflight** — run `/preflight`. Fix the cause, never the gate: no
   `--no-verify`, no `|| true`, no disabled checks.
5. **PR** — one concern; `closes #N`; a test plan naming the commands run.
   Note rollback for risky changes.
6. **Review** — every comment gets a change or a reply; unrelated findings
   become linked issues.
7. **Merge** — green CI and resolved threads. Merge commit
   (`gh pr merge --merge`), then delete the branch.

## Reporting

- Say what you verified and with which command.
- Name anything skipped, partial, flaky, or unverified. Never report work as
  done that was not run.

## Versioning

- One source of truth for the version; everything else derives from it.
- Libraries use SemVer. Apps may use CalVer if the repo already does.

## ANTI-PATTERNS

- Bundling a refactor, a dependency bump, and a feature.
- Pushing a red test "to see CI".
- A changelog that lists commits instead of user-visible changes.
