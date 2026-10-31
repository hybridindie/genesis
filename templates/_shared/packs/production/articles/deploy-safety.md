---
read_when: "Deploying a service, adding health checks, changing startup/shutdown, or shipping a migration alongside code"
---

# Deploy Safety

For services that run continuously (docker-compose, k8s/k3s). Sized for a
small team: every deploy is reversible and observable, without an on-call
rota.

## MUST

- Deploys go through CI from `main`; no manual edits on a running host or
  database.
- Migrations are backward-compatible with the running code: expand first,
  deploy code, contract later. Migrations roll forward; undo with a new
  migration.
- Rollback is one documented command (redeploy the previous image tag).
- Images are tagged with a version or commit, never only `latest`.
- Services expose `GET /health/live` (process up, no dependency checks, fast)
  and `GET /health/ready` (critical dependencies reachable, each check with a
  short timeout); both return 200 or 503.
- On SIGTERM: stop accepting work, finish in-flight requests within a
  timeout, then exit. Readiness returns 503 while draining.

## SHOULD

- k8s probes point at the endpoints above; liveness never touches the DB.
- Risky features ship behind an environment-variable flag that defaults off,
  and the flag is removed once the feature is stable.
- Watch error rate and latency for a few minutes after a deploy.
- Write a short incident note (what, why, fix, prevention) after any outage
  or data loss.

## ANTI-PATTERNS

- A health endpoint that always returns 200.
- A migration that breaks the version currently running.
- Rollback steps that exist only in someone's memory.
