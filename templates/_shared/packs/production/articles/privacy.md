---
read_when: "Storing, logging, exporting, or deleting personal data about users"
---

# Privacy and Personal Data

For services that store personal data about real users.

## MUST

- Collect only what a feature needs; note the purpose of each personal-data
  column in the migration or schema docs.
- Personal data never appears in logs, error trackers, or analytics; log
  internal ids instead.
- A user can export their data (JSON) and have it deleted; deletion cascades
  to related tables and finishes within 30 days.
- Each table holding personal data has a stated retention period and a
  cleanup job.
- Consent, where required, is opt-in and as easy to withdraw as to give.

## SHOULD

- Encrypt highly sensitive columns at rest.
- Keep a list of third-party services that receive personal data and why.
