---
description: Validate a Supabase SQL migration against sql-standards before committing
---

Validate a migration file against `.claude/rules/database/sql-standards.md`.

## Steps

1. Read the migration file provided as argument.
2. Check each item from the Migration Checklist in sql-standards.md:
   - No VARCHAR — use TEXT
   - No ENUM types — use TEXT + CHECK
   - All FK columns have indexes
   - No duplicate indexes
   - Table has created_at and updated_at with TIMESTAMPTZ
   - updated_at has a BEFORE UPDATE trigger
   - UUIDs use gen_random_uuid()
   - Timestamps use TIMESTAMPTZ
   - Boolean columns use is_/has_ prefix
   - Count columns use _count suffix
   - FK columns use _id suffix
   - CHECK constraints named {table}_{column}_check
   - ON DELETE specified on all FK constraints
   - All table/function references are schema-qualified (public.)
   - RPC functions validate inputs and restrict grants

3. Report violations with line numbers and suggested fixes.
4. If no violations, report: **MIGRATION VALID**.

## Usage

```
migration-check supabase/migrations/20251212000001_new_table.sql
```
