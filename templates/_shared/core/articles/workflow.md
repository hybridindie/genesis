---
read_when: "Starting or finishing a unit of work, committing, opening or reviewing a PR, or deciding what to do next"
---

# Workflow: Issue → Red → Green → Preflight → PR → Merge

The issue is the spec. One issue per PR. Skipping a step is a stated
exception, not a shortcut.

## Steps

1. **Issue**: problem, acceptance criteria, non-goals. A defect found
   mid-task becomes a new issue, not part of this PR.
2. **Red**: a failing test that pins the behaviour (`testing.md`).
3. **Green**: the smallest change that passes (`working-style.md`). Refactor
   in a separate commit or PR once green.
4. **Preflight**: run `/preflight`. Fix the cause, never the gate: no
   `--no-verify`, no `|| true`, no disabled checks.
5. **PR**: one concern; `closes #N`; a test plan naming the commands run.
   Note rollback for risky changes. Title + body ≤ 2000 characters combined;
   the automated reviewer truncates past that. Detail that won't fit goes in
   the issue or a PR comment.
6. **Review**: the automated reviewer (OpenCodeReview) comments inline as
   `Important —` or `Nit —`. Fix every Important finding; reply to a Nit you
   keep. Unrelated findings become linked issues. `/review` re-runs it.
7. **Merge**: green CI and resolved threads. Merge commit
   (`gh pr merge --merge`), then delete the branch.

## Commits and branches

- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`); imperative subject ≤ 72 chars; the body says why.
- Short-lived branches off `main`, named `<type>/<issue>-<slug>`.
- Read the full diff before committing. Never commit generated output,
  `.env`, credentials, or machine-specific paths.
- Force-push only with `--force-with-lease`.
- One source of truth for the version. Libraries use SemVer; apps may use
  CalVer if the repo already does.

## Reporting

- Say what you verified and with which command.
- Name anything skipped, partial, flaky, or unverified. Never report work as
  done that was not run.

## ANTI-PATTERNS

- Bundling a refactor, a dependency bump, and a feature.
- Pushing a red test "to see CI".
- A changelog that lists commits instead of user-visible changes.
