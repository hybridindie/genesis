---
read_when: "Writing schema changes, migrations, or SQL queries"
paths:
  - "supabase/migrations/**"
  - "supabase/seed.sql"
---

# SQL Standards: Schema Design & Migrations

## Data Types

MUST:
- `TEXT` for all string columns — never `VARCHAR(n)`
- `TEXT NOT NULL CHECK (col = ANY(ARRAY[...]))` for status/category columns — never `CREATE TYPE ... AS ENUM`
- `UUID` with `DEFAULT gen_random_uuid()` for primary keys — never `uuid_generate_v4()`
- `TIMESTAMPTZ` for all temporal columns — never `TIMESTAMP` without time zone
- `NUMERIC(p,s)` for money and precise values — never `FLOAT`, `REAL`, or `DOUBLE PRECISION`
- `JSONB` for semi-structured data — never `JSON`
- `INTEGER` or `BIGINT` for counts — never `SMALLINT` unless storage-critical

## Naming

Tables:
- `snake_case`, plural (`creators`, `fan_profiles`, `agency_members`)

Columns:
- `snake_case`, no abbreviations
- FK columns: `_id` suffix, singular parent table name
- Timestamps: `_at` suffix (`created_at`, `deleted_at`, `measured_at`)
- URLs: `_url` suffix
- Booleans: `is_` or `has_` prefix
- Counts: `_count` suffix
- JSON columns: `_data` or `_metadata` suffix

Constraints and indexes:
- CHECK constraints: `{table}_{column}_check`
- Indexes: `idx_{table}_{columns}`

## Table Structure

MUST:
- Every table: `id UUID DEFAULT gen_random_uuid() PRIMARY KEY`
- Every table: `created_at TIMESTAMPTZ DEFAULT now()` and `updated_at TIMESTAMPTZ DEFAULT now()`
- `updated_at` must have a trigger to auto-set on UPDATE
- Use `CREATE TABLE IF NOT EXISTS`

## Indexes

MUST:
- Every FK column gets a corresponding index
- No duplicate indexes — a composite index on `(a, b)` already covers queries on `a` alone
- Don't create indexes on columns already covered by a UNIQUE constraint

SHOULD:
- Composite index column order: highest-selectivity column first

## Constraints

MUST:
- FKs use `REFERENCES` with explicit `ON DELETE` behavior (`CASCADE`, `SET NULL`, or `RESTRICT`)
- `NOT NULL` on every column unless NULL has a defined semantic meaning
- CHECK constraints for value validation — prefer over application-level validation

## Schema Qualification

MUST:
- Always schema-qualify table and function references in migrations: `public.table_name`
- Never rely on `search_path`

## RPC / Function Standards

MUST:
- Validate inputs at the top of every RPC function
- Restrict `EXECUTE` grants to `service_role` unless explicitly designed for client-side use
- When `DROP FUNCTION` + `CREATE FUNCTION` is used, re-apply all grants and ownership in the same migration

## Migration Checklist

Before committing any `.sql` migration, verify:

- [ ] No `VARCHAR` — use `TEXT`
- [ ] No `ENUM` types — use `TEXT + CHECK`
- [ ] All FK columns have indexes
- [ ] No duplicate indexes
- [ ] Table has `created_at` and `updated_at` with `TIMESTAMPTZ`
- [ ] `updated_at` has a `BEFORE UPDATE` trigger
- [ ] UUIDs use `gen_random_uuid()`
- [ ] Timestamps use `TIMESTAMPTZ`
- [ ] Boolean columns use `is_`/`has_` prefix
- [ ] Count columns use `_count` suffix
- [ ] FK columns use `_id` suffix
- [ ] CHECK constraints named `{table}_{column}_check`
- [ ] `ON DELETE` specified on all FK constraints
- [ ] All table/function references are schema-qualified (`public.`)
- [ ] RPC functions validate inputs and restrict grants

ANTI-PATTERNS (BLOCKING):
- `VARCHAR(n)` columns
- `CREATE TYPE ... AS ENUM`
- FK columns without indexes
- `TIMESTAMP` without time zone
- Missing `updated_at` trigger
- Duplicate indexes
- Unqualified table/function names
- Missing input validation in RPC functions

Use `/migration-check <file>` to validate a migration against this checklist before committing.
