---
read_when: "Adding a datastore, queue, cache, or other infrastructure; or changing how the backend reaches the database"
paths:
  - "{{BACKEND_PATH}}/**/repositor*/**"
  - "{{BACKEND_PATH}}/**/repository.py"
  - "supabase/**"
  - "docker-compose*.yml"
---

# Data Infrastructure: Postgres First

## MUST

- Persistence goes through repositories (or the project's data-access
  layer). Routes and services do not build SQL.
- Use the data-access library already in the project ({{DB_PROVIDER}}); don't
  introduce a second one for new code.
- Schema changes are migrations in the project's migration directory, never
  manual edits to a running database.

## SHOULD

- Reach for Postgres features before new infrastructure: `pgvector` for
  embeddings, a Postgres-backed queue (pgmq, procrastinate) for jobs,
  `LISTEN/NOTIFY` for small events (payload < 8 KB; send keys, not data).
- A new datastore, broker, or cache needs a stated reason in the PR and an
  entry in `AGENTS.md` → Stack.
