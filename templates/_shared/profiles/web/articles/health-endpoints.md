---
read_when: "Adding health, readiness, or liveness endpoints"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
  - "{{BACKEND_PATH}}/app/main.py"
  - "infra/k8s/**/*.yaml"
---

# Health, Readiness & Liveness Endpoints

## MUST

### Required Endpoints
Every service MUST expose three endpoints under a `/health` path prefix:

| Endpoint | Purpose | HTTP Status |
|----------|---------|-------------|
| `GET /health` | Combined check: healthy = ready & alive | 200 or 503 |
| `GET /health/ready` | Ready to serve traffic? (DB, cache, external deps OK) | 200 or 503 |
| `GET /health/live` | Process alive? (no deadlock, no infinite loop) | 200 or 503 |

### Health (`/health`)
Aggregated status. Returns:
- `200 OK` if both ready and live checks pass
- `503 Service Unavailable` if either fails, with `Retry-After` header
- Response body:
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "pass", "latency_ms": 12},
    "cache": {"status": "pass", "latency_ms": 3},
    "external_api": {"status": "pass", "latency_ms": 45}
  }
}
```

### Readiness (`/health/ready`)
- Checks external dependencies: database connectivity, cache reachability, message broker, third-party APIs
- Must return `503` if any critical dependency is unavailable
- Non-critical dependencies: return `200` with warnings in body, do not fail readiness
- Timeout per check: 2 seconds total, 500ms per individual check

### Liveness (`/health/live`)
- Simple lightweight check: process is running and not in an infinite loop or deadlock
- Must not check external dependencies (to avoid cascading failures)
- Must complete in < 100ms
- Return 200 or 503

### Graceful Shutdown
- On SIGTERM: stop accepting new connections, finish in-flight requests, then exit
- Shutdown timeout: 30 seconds (configurable)
- Return 503 on health checks during shutdown period
- FastAPI: use `lifespan` context manager for startup/shutdown logic

## SHOULD

- Startup probe: check if the application is initialized (migrations applied, caches warmed)
- Deep health check: validate end-to-end functionality (a known query returns expected data)
- Health check caching: cache dependency status for 5 seconds to avoid thundering herd
- Separate port for health metrics (if load balancers poll aggressively)
- Kubernetes: configure `livenessProbe`, `readinessProbe`, and `startupProbe` in manifests

## ANTI-PATTERNS (BLOCKING)

- Health endpoint that always returns 200 regardless of downstream health (liar endpoint)
- Readiness check that checks external APIs with no timeout (blocks, cascades failures)
- Liveness check that queries the database (causes pod restart when DB is down)
- No graceful shutdown (dropped connections, mid-request termination)
- Health endpoint that performs expensive operations (full table scans, N+1 queries)

## Enforcement Checklist

- [ ] `/health`, `/health/ready`, `/health/live` implemented
- [ ] Readiness checks database, cache, and critical external deps
- [ ] Liveness check is lightweight (<100ms, no external deps)
- [ ] Graceful shutdown on SIGTERM with timeout
- [ ] Health endpoint returns structured JSON with per-check latency
- [ ] Kubernetes probes (if applicable) match application endpoints
