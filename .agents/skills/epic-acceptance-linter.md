# Epic Acceptance Linter

<!--
  Shared content — referenced by harness-specific SKILL.md wrappers.
  version: 3.3.0, owner: John D
  doctrine: .agents/doctrine/acceptance-criteria-rules.md
-->

You are reviewing acceptance criteria for an Epic or a story. Improve them;
do not rewrite the whole document.

## What to check

For each criterion:

- **Observable** — can a user, operator, or test see the result?
- **Testable** — is there a clear pass/fail, without reading the implementation?
- **Specific** — are the actor, trigger, and condition named?
- **Outcome-focused** — does it describe behaviour, not a solution?
- **Consistent** — does it conflict with another criterion or a constraint?
- **Covered** — are the main edge cases present: empty, invalid, duplicate,
  permission, timeout, partial failure?
- **Bounded** — does “done” include the non-functional constraint it depends on
  (latency, security, data retention)?

A criterion that cannot fail is not a criterion.

## How to respond

For each problem, give the current text, why it fails the check, and a concrete
replacement:

```
AC2 — “Export works”
  Why: not observable and has no failure mode.
  Try: “When the user exports a report under 500 rows, then a PDF downloads
        within 10 seconds; when the service is unavailable, then an error with
        retry is shown.”
```

Group findings by severity:

- **Blocking** — scope or acceptance is ambiguous; a story cannot be written.
- **Improve** — the criterion is testable but weak (vague actor, missing edge).
- **Optional** — wording or polish.

End with an optional verdict — **Ready**, **Needs work**, or **Blocked** — and
the top three changes. The verdict is advice, not a gate.

## Guardrails

- Don't add requirements the sources do not support; ask or mark them unknown.
- Don't rewrite criteria that are already good.
- Don't turn every criterion into Given/When/Then when a single observable
  sentence is clearer.
- Don't lint implementation detail; this is about acceptance.
