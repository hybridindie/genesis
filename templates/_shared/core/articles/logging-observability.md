---
read_when: "Adding logs, metrics, tracing, or debugging a production issue"
---

# Observability: Structured, Correlated, Secret-Free

## MUST

- Logs are structured records (JSON or key=value), not prose.
- Every log line carries the request/command id and, where relevant, the
  operation and outcome.
- Log levels mean something: `error` = action needed, `warn` = degraded,
  `info` = lifecycle, `debug` = diagnostics (off by default in production).
- Errors log once, at the boundary, with context and stack only for bugs.
- Never log secrets, tokens, full payloads, file contents, or home paths.
- Long operations expose progress and a cancellation path.

## SHOULD

- Metrics for the four golden signals where a service exists: latency, traffic,
  errors, saturation.
- Trace ids across service boundaries.
- A health/status endpoint for services that run continuously.

## ANTI-PATTERNS

- `print()` as operational logging.
- Logging in a loop for per-item detail (aggregate instead).
- Catch-log-rethrow with no added context.
- A dashboard nobody can act on.

## Checklist

- [ ] Records are structured and correlated.
- [ ] No sensitive data in logs.
- [ ] Errors are logged once with context.
