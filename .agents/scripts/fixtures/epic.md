**Why**

Users can only export CSV.

**Outcome**

Reports export as PDF.

```yaml agent-plan
version: 1
kind: epic
epic: "#12"
acs: [AC1, AC2, AC3]
contracts:
  - id: C1
    what: ExportJob response schema
    owner: S1
    paths: [backend/export/schema.py]
stories:
  - id: S1
    title: Export API returns a PDF job
    issue: "#13"
    size: M
    priority: P0
    acs: [AC1]
    owns: [backend/export/**, tests/export/**]
    verify: uv run pytest tests/export -q
  - id: S2
    title: Export button in the report view
    issue: "#14"
    size: S
    priority: P1
    acs: [AC2]
    owns: [frontend/src/reports/**]
    verify: npm test -- reports
  - id: S3
    title: Failure banner with retry
    issue: "#15"
    size: S
    priority: P1
    acs: [AC3]
    depends_on: [S1, S2]
    owns: [frontend/src/reports/ExportError.tsx]
    verify: npm test -- ExportError
```
