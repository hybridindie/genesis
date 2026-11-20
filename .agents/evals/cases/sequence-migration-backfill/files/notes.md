Planning notes — report owners, 2026-11-14

Every report needs an owner so people know who to ask. Today reports have no
owner. Plan from Marco:
1. Migration: add a nullable `owner_id` column to the reports table.
2. Backfill: fill owner_id from the audit log (who created the report). Has to
   run after the column exists; takes ~20 min on prod data.
3. Once backfilled, a second migration makes owner_id NOT NULL. Can't run
   before the backfill or it fails on existing rows.
Jen: the API needs to return owner on GET /reports/{id} and the report page
shows "Owner: <name>". UI can be built against the response shape as soon as
we agree on it — it doesn't need real data.
Priya: also a filter "my reports" on the list page.
Out of scope: changing owners, transferring ownership.
