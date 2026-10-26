---
read_when: "Opening or reviewing a PR, cutting a release, or reporting status"
---

# Enforcement: Definition of Done

A change is done when it is tested, documented where needed, reviewed, and
honest about what it does not cover.

## PR checklist

- [ ] Issue referenced (`closes #N`); one concern per PR.
- [ ] Failing test first (or a regression test for a bug).
- [ ] Local preflight green: lint, types, tests, zero-skip scan.
- [ ] Errors are structured; no traces cross a boundary.
- [ ] No secrets, generated output, or unrelated drive-by edits.
- [ ] Docs updated when a contract, command, or structure changed.
- [ ] Risky changes note rollback and blast radius.

## Honest reporting

- Say what you verified and how. "Tests pass" names the command.
- Report partial results explicitly: skipped steps, non-atomic batches,
  flaky reruns, unverified paths.
- Never claim completion for work that was not run.

## Review

- Review the diff, not the summary.
- Every comment gets a code change or a written reply; unrelated concerns
  become a linked follow-up issue.
- Prefer small PRs; split refactors from behaviour changes.

## Versioning

- Libraries: SemVer (`MAJOR.MINOR.PATCH`), breaking changes bump `MAJOR`.
- Apps/services: CalVer (`YYYY.MM.DD[-N]`) in the manifest and changelog.
- One source of truth for the version; derived files are generated.

## ANTI-PATTERNS

- Merging with a red or skipped gate.
- "Fixed" by weakening an assertion or deleting a test.
- Hidden scope: opportunistic renames or dependency bumps in a feature PR.
- A changelog that lists commits instead of user-visible changes.
