---
read_when: "Choosing database infrastructure or local Postgres setup"
paths:
  - "supabase/**"
  - "{{BACKEND_PATH}}/src/libs/**/repositories/**"
  - "{{BACKEND_PATH}}/src/libs/**/repository.py"
  - "{{BACKEND_PATH}}/app/core/dependencies*.py"
  - "{{BACKEND_PATH}}/docs/DATABASE_ARCHITECTURE.md"
---

# PostgreSQL-Only Infrastructure (Article V)

PostgreSQL is the single infrastructure component for all data and messaging.

## Extensions & Features

- **pgvector** - Vector embeddings for AI/ML
- **pgmq** - Message queues
- **LISTEN/NOTIFY** - Real-time event streaming (8KB payload limit)
- **HSTORE + UNLOGGED tables** - Cache, sessions, rate limiting

## MUST

- Use repository pattern to isolate database-specific logic from business logic
- No direct SQL in business logic — use {{DB_PROVIDER}} client or repository abstraction
- UNLOGGED tables for ephemeral data
- Cache operations via HSTORE-based tables with automatic expiration
- All DB operations via {{DB_PROVIDER}} client
- New migrations in `supabase/migrations/*.sql`
- Keep LISTEN/NOTIFY payloads under 8KB; store larger data in tables and send keys

## {{DB_PROVIDER}} Repositories

New repositories belong in their service library (`src/libs/<service>/repository.py` or `src/libs/<service>/repositories/`), not in `app/repositories/`.
