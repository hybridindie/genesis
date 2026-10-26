---
read_when: "Adding or changing error paths, return values, or failure envelopes"
---

# Error Handling: Structured, Actionable, Never Silent

Failures are data the caller can act on, not stack traces and not a half-success.

## MUST

- Use a stable, enumerated error code (`VALIDATION_ERROR`, `NOT_FOUND`,
  `PRECONDITION_FAILED`, `TIMEOUT`, `INTERNAL_ERROR`, …). No ad-hoc strings.
- Return a structured error: `{ ok: false, code, message, hint, required? }`.
  `hint` tells the caller what to do next; it does not restate the code.
- Catch at the boundary (HTTP handler, MCP tool, CLI command) and convert to a
  structured error. No exception escapes as a trace.
- Correlate logs and responses with the request/command id.
- Distinguish expected failures from bugs; both are reported, differently.
- Partial success is reported honestly: name what was skipped, aborted, or
  non-atomic. Never `ok: true` when the effect half-failed.

## SHOULD

- One error type per domain, carrying `code` + context.
- Validation happens before side effects.
- Errors include the offending field/path, not the whole payload.

## ANTI-PATTERNS

- `except Exception: pass`
- Returning `None` to mean "failed".
- A hint that repeats the error code.
- Logging secrets, file contents, or full home paths.
- HTTP 200 with `{"error": ...}` when a 4xx/5xx is correct.

## Checklist

- [ ] Every failure has a stable code and a hint.
- [ ] Boundary converts exceptions; nothing leaks as a trace.
- [ ] Partial results name what did not happen.
