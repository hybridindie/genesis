---
read_when: "Adding caching, materialized views, or cache headers"
paths:
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - "{{BACKEND_PATH}}/app/**/*.py"
  - "{{BACKEND_PATH}}/migrations/**/*.sql"
---

# Caching Strategy (Article X — Caching)

PostgreSQL-only infrastructure means no Redis, no Memcached, no external
cache layer. All caching uses PostgreSQL-native mechanisms.

## Core Principle

Everything that should be persisted lives in PostgreSQL. Caching is a
read-optimization layer on top of the source-of-truth data, not a separate
store. Cache invalidation is a database operation, not a network operation.

## NOLOG Tables for Cache Data

Use `UNLOGGED` tables for cache data that is disposable and can be rebuilt
from the source tables. NOLOG tables skip WAL writes, making them faster for
high-throughput cache writes.

```sql
CREATE UNLOGGED TABLE cache_lookup (
    cache_key   TEXT PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cache_lookup_expires ON cache_lookup (expires_at);
```

## Cache Patterns

### 1. Lookup Table (key-value cache)

For expensive-to-compute values (API responses, derived data, computed
aggregates):

```python
async def get_or_compute(cache_key: str, compute_fn, ttl_seconds: int):
    # Try cache
    row = await db.fetchrow(
        "SELECT cache_value FROM cache_lookup WHERE cache_key = $1 AND expires_at > now()",
        cache_key,
    )
    if row:
        return json.loads(row["cache_value"])
    
    # Compute and store
    value = await compute_fn()
    await db.execute(
        """INSERT INTO cache_lookup (cache_key, cache_value, expires_at)
           VALUES ($1, $2, now() + $3::interval)
           ON CONFLICT (cache_key) DO UPDATE SET cache_value = $2, expires_at = now() + $3::interval""",
        cache_key, json.dumps(value), f"{ttl_seconds} seconds",
    )
    return value
```

### 2. Materialized Views

For read-heavy aggregates that change infrequently. Refresh on a schedule or
on write:

```sql
CREATE MATERIALIZED VIEW mv_daily_stats AS
SELECT date_trunc('day', created_at) AS day, count(*) AS total
FROM events GROUP BY 1;

CREATE UNIQUE INDEX ON mv_daily_stats (day);
-- Refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_stats;
```

### 3. HTTP Cache Headers

For API responses that are cacheable:

- `Cache-Control: public, max-age=300` for semi-static data
- `Cache-Control: no-store` for authenticated/personalized responses
- `ETag` + `If-None-Match` for conditional requests (304 Not Modified)
- Never cache authenticated responses without a `Vary: Authorization` header

## TTL and Invalidation

- Every cache entry MUST have a TTL (`expires_at` column). No permanent cache.
- Active invalidation: `DELETE FROM cache_lookup WHERE cache_key = $1` on
  source-data change.
- Lazy invalidation: expired rows are cleaned up by a scheduled job or by
  the `get_or_compute` function's `ON CONFLICT` path.
- Materialized views: `REFRESH MATERIALIZED VIEW CONCURRENTLY` on a schedule
  (pg_cron or application-level scheduler).

## What NOT to Cache in NOLOG Tables

- Data that must survive a crash (use a regular LOGGED table)
- Data with transactional consistency requirements (the NOLOG table is not
  part of the source-of-truth transaction)
- Session tokens or auth state (use regular tables — NOLOG data is lost on
  crash recovery)

## Anti-Patterns

- Using Redis, Memcached, or any external cache (violates PostgreSQL-only)
- Caching without a TTL (permanent cache = permanent staleness)
- NOLOG tables for data that must survive a crash
- Cache-aside without active invalidation (relies solely on TTL expiry —
  stale for the entire TTL window)
- Caching authenticated responses without `Vary: Authorization`
- Using `SELECT *` into cache — cache only the specific fields the consumer
  needs (smaller payload, faster lookup)