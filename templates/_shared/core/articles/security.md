---
read_when: "Handling auth, secrets, user input, or destructive actions"
---

# Security: Least Privilege, No Secrets in Code

Dependency hygiene lives in `dependency-security.md`.

## MUST

- Secrets come from the environment or a secret store; never in code, tests,
  fixtures, logs, or git history. `.env` is gitignored; commit an example file
  with names only.
- Validate input at the boundary (schema, length, range, encoding) and check
  that the caller may perform the operation, before any side effect.
- Parameterise SQL and subprocess calls. No string-built SQL; no
  `shell=True` with interpolated input.
- Never `eval`/`exec` or dynamically import untrusted input, including model
  output.
- Destructive operations need an explicit confirmation flag and offer a
  preview (`dry_run` / `--dry-run`).
- Validate security-critical config at startup; refuse to run in production
  with missing or default secrets.

## SHOULD

- Least-privilege, scoped, short-lived tokens; no shared admin token.
- Constant-time comparison for secrets; standard crypto libraries only.
- Fail closed: unknown state denies.

## ANTI-PATTERNS

- Credentials in URLs, logs, or error messages.
- Trusting a client-supplied role, path, or command.
- Disabling TLS verification to "make it work".
