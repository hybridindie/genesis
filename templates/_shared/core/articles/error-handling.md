---
read_when: "Adding or changing error paths, return values, or failure responses"
---

# Error Handling: Structured, Actionable, Never Silent

Failures are data the caller can act on, not stack traces and not a
half-success.

## MUST

- Catch at the boundary (HTTP handler, MCP tool, CLI command, addon router)
  and convert to the boundary's error shape. No raw trace crosses it.
- Errors carry a stable code from a fixed set (`VALIDATION_ERROR`,
  `NOT_FOUND`, `PRECONDITION_FAILED`, `TIMEOUT`, `INTERNAL_ERROR`, …) and a
  hint that says what to do next.
- Partial success is reported as partial: name what was skipped, aborted, or
  not applied. Never report success when part of the effect failed.
- Never swallow an exception (`except Exception: pass`) or return `None` to
  mean "failed".

## Boundary shapes

Use the shape native to the boundary:

- **HTTP:** correct 4xx/5xx status plus a JSON body with `code`, `message`,
  `hint`. Never 200 with an error body.
- **MCP / bridge envelopes:** `{ ok: false, code, message, hint, required? }`.
- **CLI:** non-zero exit code, message and hint on stderr, `--json` error
  object when requested.
- **Library:** a typed exception per domain carrying `code` and context.

## SHOULD

- Validate before side effects.
- Point at the offending field or path, not the whole payload.
- Correlate the error with the request/command id in logs.

## ANTI-PATTERNS

- A hint that repeats the code.
- Secrets, file contents, or home paths in error messages.
