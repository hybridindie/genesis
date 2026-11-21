Part of #12

**Acceptance criteria**

- [ ] **Given** a report under 500 rows, **when** export is requested, **then** a PDF job id returns within 1s.

```yaml agent-plan
version: 1
kind: story
story: S1
epic: "#12"
issue: "#13"
branch: feat/13-export-api
acs: [AC1]
ac_text:
  AC1: Given a report under 500 rows, when export is requested, then a PDF job id returns within 1s.
owns: [backend/export/**, tests/export/**]
must_not_touch: [frontend/**]
verify: uv run pytest tests/export -q
context: The export pipeline is synchronous today; this story adds a job API.
tracks:
  - id: contract
    kind: contract
    owns: [backend/export/schema.py]
    verify: uv run python -c "import backend.export.schema"
  - id: A
    name: API route
    owns: [backend/export/routes.py, tests/export/test_routes.py]
    depends_on: [contract]
    verify: uv run pytest tests/export/test_routes.py -q
  - id: B
    name: PDF worker
    owns: [backend/export/worker.py, tests/export/test_worker.py]
    depends_on: [contract]
    verify: uv run pytest tests/export/test_worker.py -q
tasks:
  - id: T1
    track: contract
    do: Define ExportJob in backend/export/schema.py (new)
    files: [backend/export/schema.py]
    verify: uv run python -c "import backend.export.schema"
    acs: [AC1]
  - id: T2
    track: A
    do: "Add POST /reports/{id}/export returning ExportJob"
    files: [backend/export/routes.py, tests/export/test_routes.py]
    depends_on: [T1]
    verify: uv run pytest tests/export/test_routes.py -q
    acs: [AC1]
  - id: T3
    track: B
    do: Render the PDF in a background worker
    files: [backend/export/worker.py, tests/export/test_worker.py]
    depends_on: [T1]
    verify: uv run pytest tests/export/test_worker.py -q
    acs: [AC1]
integration:
  merge_order: [contract, A, B]
  verify: uv run pytest tests/export -q
```
