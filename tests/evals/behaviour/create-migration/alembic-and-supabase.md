# Case: an Alembic project that also has a Supabase migrations dir

## Input

> "Add a migration for a `saved_views` table with a `user_id` FK to `users`."
> The repo has `alembic.ini`, `alembic/versions/`, and `supabase/migrations/`
> with three SQL files from before the Alembic move.

## Expected properties

- It **does not** scaffold a SQL skeleton into `supabase/migrations/`: the
  project is an Alembic project, so it defers with the `alembic revision -m`
  instruction and says why (two sources of truth).
- If it needs the table/column shape, it asks about the FK target's existing
  column (`users.id` type, `ON DELETE` behaviour) rather than inventing one.
- The `--tables`/`--description` names it would use are snake_case and the
  migration timestamp format is described.
- It points out that the old `supabase/migrations/` history is now stale and
  asks whether to leave it in place — it does not delete it.
