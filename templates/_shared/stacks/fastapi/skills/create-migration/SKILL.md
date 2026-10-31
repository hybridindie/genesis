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
  version: 2.0.0, owner: John D
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
   python3 .claude/skills/create-migration/scripts/new_migration.py \
     --description "{{description}}" --tables "{{tables}}"
   ```
   The script owns the timestamp, filename, table skeleton, and overwrite guard.
2. **Fill the skeleton** at the printed path; never invent a timestamp or path.
3. **Use this table checklist** for the columns/constraints you add:
   - `CREATE TABLE IF NOT EXISTS public.{table} (...)`;
   - `id UUID DEFAULT gen_random_uuid() PRIMARY KEY`;
   - `created_at` and `updated_at` as `TIMESTAMPTZ DEFAULT now()`;
   - a `BEFORE UPDATE` trigger for `updated_at`;
   - `TEXT` for strings; no `VARCHAR` or `ENUM`;
   - named `CHECK` constraints;
   - `{parent}_id UUID REFERENCES public.{parent}(id) ON DELETE …`;
   - indexes for FK columns;
   - schema-qualified references (`public.`).
4. **Add a commented rollback**:
   ```sql
   -- DOWN
   -- DROP TABLE IF EXISTS public.{table} CASCADE;
   ```
5. **Validate against the Migration Checklist** in `sql-standards.md`: no
   `VARCHAR`, no `ENUM`, every FK has `ON DELETE`, every table has `updated_at`
   and its trigger, no redundant indexes.
6. **Report** the path and any checklist item the caller must decide.

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
- Stop if the project is not a {{DB_PROVIDER}} project or has no
  `supabase/migrations/` directory.
- Stop if a requested change violates `sql-standards.md`.

## Token Budget

- Default: read ≤ 2 files (`sql-standards.md` and one existing migration). Read a
  referenced type/table definition when needed to avoid an invalid FK or type,
  and say why.
- Do not scan the migrations directory.
- Emit SQL only; add prose only for a blocker or a standards conflict.
