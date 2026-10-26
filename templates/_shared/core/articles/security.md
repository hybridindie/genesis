---
read_when: "Handling auth, secrets, user input, dependencies, or destructive actions"
---

# Security: Least Privilege, No Secrets in Code

## MUST

- Secrets come from the environment or a secret store; never in code, tests,
  fixtures, logs, or git history.
- `.env` files are gitignored; ship `.env.example` with names and no values.
- Validate input at the boundary: schema, length, range, encoding, and the
  operation allowed for the caller.
- Parameterise queries and shell calls. No string-built SQL or `shell=True`
  with interpolated input.
- Dependencies are pinned with a lockfile; run an audit in CI.
- Destructive operations require explicit confirmation (`confirm=True`) and
  support a preview (`dry_run`).
- Agents inherit permissions: default allow, ask before destructive commands,
  deny credential paths (`~/.ssh`, `~/.aws`, `~/.kube`, `**/.env`).

## SHOULD

- Constant-time comparison for tokens; standard libraries over custom crypto.
- Least-privilege tokens, scoped keys, short expiries.
- Fail closed: unknown state denies, it does not allow.

## ANTI-PATTERNS

- Credentials in URLs, logs, error messages, or commit history.
- Trusting a client-supplied role, path, or command.
- Disabling TLS verification to "make it work".
- One shared admin token for everything.
- `eval`, `exec`, or dynamic import of untrusted input.

## Checklist

- [ ] No secret material in the diff.
- [ ] Input validated before side effects.
- [ ] Destructive path requires confirm and honours dry-run.
- [ ] Dependencies pinned and audited.
