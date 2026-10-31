---
description: Check a SQL migration against the project's SQL standards before committing
---

Check the migration `$ARGUMENTS` against `.claude/rules/database/sql-standards.md`.

1. Read the migration and the MUST items in `sql-standards.md`.
2. Report each violation as `line — rule — fix`. Do not restate passing rules.
3. If there are none, report **MIGRATION VALID**.
