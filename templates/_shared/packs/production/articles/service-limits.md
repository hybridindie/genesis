---
read_when: "Adding rate limits, caching, timeouts, or performance-sensitive endpoints and queries"
---

# Service Limits: Rate, Cache, Performance

## MUST

- Auth and other abuse-prone endpoints have rate limits; a limited request
  gets 429 with `Retry-After`, never a silent drop.
- Rate limiting lives in middleware or a dependency, not in handlers, and
  never `sleep`s.
- Every cache entry has a TTL and an invalidation path. Authenticated
  responses are `Cache-Control: no-store` or vary on the auth header.
- Database queries have a statement timeout in production.
- Endpoints that take user-controlled sizes (page size, depth, batch) cap
  them.

## SHOULD

- Prefer Postgres-native caching (tables with `expires_at`, materialized
  views) before adding Redis; add Redis only with a stated reason.
- Check new queries on large tables with `EXPLAIN ANALYZE`; fix N+1 patterns.
- Track p95 latency for key endpoints and frontend bundle size per PR once
  there is a baseline worth protecting.

## ANTI-PATTERNS

- Loading a whole table into memory for convenience.
- Returning full entities when the caller needs ids or summaries.
- CPU-heavy work inside an async request handler.
