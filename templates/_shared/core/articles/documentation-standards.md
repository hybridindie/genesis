---
read_when: "Writing a README, ADR, API reference, or agent-facing docs (AGENTS.md included)"
---

# Documentation: Run It, Then Explain It

Docs answer three questions in order: what is this, how do I run it, where is
the detail.

## MUST

- README starts with a one-paragraph purpose, then a copy-pasteable quickstart
  that works on a clean checkout.
- State the supported runtime floor and the exact commands for install, test,
  lint, and run.
- Every command in the docs is copy-pasted from a working run.
- Public APIs, tools, and file formats have an authoritative reference with
  types, defaults, and error codes.
- Decisions with trade-offs get an ADR (`docs/adr/NNNN-title.md`): context,
  decision, consequences, alternatives.
- Agent-facing docs include a `llms.txt` index (or equivalent) pointing at the
  authoritative pages, not a duplicate copy.
- `AGENTS.md` is the always-loaded context, so every line costs every session.
  It holds what doesn't change with each issue: what the project is, the
  architecture, the commands, the rule index and the invariants. It holds **no
  status**: no lists of open, active or done issues and epics, no per-feature
  or per-test history. The issue tracker and the git log are the record; an
  agent queries them (`gh issue list`, `git log`) when it needs status.
- A rule or invariant cites at most one issue or ADR, for why it exists. The
  history behind it stays in that issue.

## SHOULD

- Examples over description; one realistic example beats five fragments.
- A "gotchas" section for non-obvious behaviour.
- Link checks in CI; fail on broken internal links.

## ANTI-PATTERNS

- Screenshots where text would do.
- Docs that restate the code instead of the contract.
- A quickstart that assumes an already-configured machine.
- Undated "coming soon" sections.
- Two pages describing the same API differently.
- Status or a changelog in `AGENTS.md` (an "active epics" list, "#N done",
  a suite's per-issue notes): it duplicates the tracker and goes stale.

## Checklist

- [ ] Quickstart runs from scratch.
- [ ] Commands match the current CLI.
- [ ] Public contract documented.
- [ ] Links checked.
- [ ] `AGENTS.md` carries no status, and each rule in it cites at most one issue.
