---
name: create-migration
description: Scaffold a {{DB_PROVIDER}} SQL migration compliant with sql-standards.md
when_to_use: >
  Run when adding or altering a table or constraint. Trigger phrases: "create a
  migration", "add a table", "alter the schema", "write SQL migration".
user-invocable: true
disable-model-invocation: true
arguments:
  - name: description
    description: "Migration description in snake_case (e.g., 'add_user_profiles_table')"
    required: true
  - name: tables
    description: "Comma-separated list of tables to create or alter"
    required: true
---

# Create Migration

<!--
  contract: .claude/rules/doctrine/skill-execution.md
  version: 2.1.0, owner: John D
-->

Generate one SQL migration file. The filename and checklist are deterministic;
the model designs the table columns and constraints.

## Inputs

- Required: `description` in snake_case and `tables` (comma-separated).
- Read: `.claude/rules/database/sql-standards.md` and the nearest existing
  migration for style.
- Do not read: unrelated application code or the whole migrations directory.

## Deterministic Steps

1. **Create the skeleton.**
   ```bash
   python3 .agents/skills/create-migration/scripts/new_migration.py \
     --description "{{description}}" --tables "{{tables}}"
   ```
   The script owns the timestamp, filename, table skeleton, and overwrite guard.
   It writes to the first of `supabase/migrations/`, `migrations/` or
   `db/migrations/` that exists; pass `--dir <path>` for anything else. Exit `2`
   means no SQL migrations directory (or an Alembic project) — stop.
2. **Fill the skeleton** at the printed path; never invent a timestamp or path.
   Columns, types, constraints and indexes follow `sql-standards.md` (Data
   Types, Table Structure, Indexes, Constraints).
3. **Keep the commented rollback** the script wrote under `-- DOWN`.
4. **Validate** against "Checking a migration" in `sql-standards.md`.
5. **Report** the path and any checklist item the caller must decide.

## LLM Judgment

Use judgment only for:

- column sets, data types, and constraint names for the requested tables;
- `ON DELETE` behavior per relationship;
- whether an index is genuinely needed.

Do not invent tables or columns outside the request.

## Output

The complete migration file contents, ready to write at the deterministic path.
Include a one-line summary of tables changed and the validation result.

## Stop Conditions

- Stop if `description` or `tables` is missing.
- Stop if the target file already exists; do not overwrite it.
- Stop if the script exits `2`: no SQL migrations directory, or an Alembic
  project (use `alembic revision -m` instead).
- Stop if a requested change violates `sql-standards.md`.

## Token Budget

- Default: read ≤ 2 files (`sql-standards.md` and one existing migration). Read a
  referenced type/table definition when needed to avoid an invalid FK or type,
  and say why.
- Do not scan the migrations directory.
- Emit SQL only; add prose only for a blocker or a standards conflict.
