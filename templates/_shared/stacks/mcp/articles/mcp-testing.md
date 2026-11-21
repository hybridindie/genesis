---
read_when: "Writing tests for an MCP server, tool schema, or transport"
paths:
  - "**/tests/**"
  - "**/test_*.py"
---

# MCP Testing: Fake the Peer, Assert the Envelope

Test the protocol edge without a live editor/service.

## MUST

- Contract tests assert the envelope: `id`, `ok`, `result`, `error`, `hint`,
  `required`.
- Use a fake peer (in-memory or socket double) for transport tests; no real
  editor, browser, or daemon in unit/contract tests.
- Table-driven tool tests: valid input, missing field, wrong type, unknown
  field, precondition failure, dry-run.
- Assert the side-effect boundary (what was called with what), not the internal
  implementation.
- Safety tests: destructive without `confirm` refused; `dry_run` performs
  nothing; timeout maps to `TIMEOUT`.

## SHOULD

- One happy-path + one failure contract test per tool family, plus targeted
  tests for mutations.
- Integration tests run against a real peer in a separate job.

## ANTI-PATTERNS

- Mocking the bridge so loosely the real envelope would fail.
- Asserting on a Python object instead of the JSON-serialized result.
- A test that passes when the peer is disconnected.
- Skipping the timeout path.
