---
read_when: "Writing a README, ADR, API reference, or agent-facing docs"
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

## Checklist

- [ ] Quickstart runs from scratch.
- [ ] Commands match the current CLI.
- [ ] Public contract documented.
- [ ] Links checked.
