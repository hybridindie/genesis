Part of #11 · Story S2

**What** Add an Export action on the report page. **Why** Readers can download
the numbers without asking engineering.

**Context**

`src/report/pdf.py` (S1) exposes `render_report_pdf(report) -> bytes`. Routes
live in `src/report/routes.py`; the web app calls them through
`web/src/report/`. The endpoint returns a job id the button polls.

**Acceptance criteria**

- [ ] **Given** a report with data, **when** the reader chooses Export,
  **then** a PDF downloads and the response carries a `job` id.
- [ ] **Given** a report with no data, **when** the reader chooses Export,
  **then** the PDF carries the empty-state line instead of failing.

<!-- agent-plan:generated -->
**Parallelization**

| Track | Kind | Owns | Depends on | Parallel with | Verify | Status |
|-------|------|------|------------|---------------|--------|--------|
| api | contract | `src/report/routes.py`, `tests/report/test_export.py` | — | — | `pytest tests/report/test_export.py -q` | todo |
| web | track | `web/src/report/ExportButton.tsx`, `web/src/report/ExportButton.test.tsx` | api | — | `cd web && npm test -- ExportButton` | todo |

- **Integration:** merge api → web, then `pytest tests/report -q && (cd web && npm test -- ExportButton)`

**Tasks**

_api_
- [ ] **T1** — Add POST /reports/{id}/export returning a job id, in src/report/routes.py — files `src/report/routes.py`, `tests/report/test_export.py` — AC1 — verify `pytest tests/report/test_export.py -q -k endpoint`
- [ ] **T2** — Cover the empty report case — files `tests/report/test_export.py` — after T1 — AC2 — verify `pytest tests/report/test_export.py -q -k empty`

_web_
- [ ] **T3** — Add the Export button that calls the endpoint and polls the job — files `web/src/report/ExportButton.tsx`, `web/src/report/ExportButton.test.tsx` — AC1 — verify `cd web && npm test -- ExportButton`
<!-- /agent-plan:generated -->

**Done when**

- [ ] Acceptance criteria pass
- [ ] Every track's verify passes and the integration check is green
- [ ] No files outside the declared ownership changed

```yaml agent-plan
version: 1
kind: story
story: S2
epic: "#11"
issue: "#13"
branch: feat/13-export-endpoint
acs: [AC1, AC2]
ac_text:
  AC1: Given a report with data, when the reader chooses Export, then a PDF downloads and the response carries a job id.
  AC2: Given a report with no data, when the reader chooses Export, then the PDF carries the empty-state line instead of failing.
depends_on: [S1]
owns: [src/report/routes.py, tests/report/test_export.py, web/src/report/ExportButton.tsx, web/src/report/ExportButton.test.tsx]
verify: pytest tests/report/test_export.py -q && (cd web && npm test -- ExportButton)
tracks:
  - id: api
    kind: contract
    owns: [src/report/routes.py, tests/report/test_export.py]
    verify: pytest tests/report/test_export.py -q
  - id: web
    kind: track
    depends_on: [api]
    owns: [web/src/report/ExportButton.tsx, web/src/report/ExportButton.test.tsx]
    verify: cd web && npm test -- ExportButton
tasks:
  - id: T1
    track: api
    do: Add POST /reports/{id}/export returning a job id, in src/report/routes.py
    files: [src/report/routes.py, tests/report/test_export.py]
    verify: pytest tests/report/test_export.py -q -k endpoint
    acs: [AC1]
  - id: T2
    track: api
    do: Cover the empty report case
    files: [tests/report/test_export.py]
    depends_on: [T1]
    verify: pytest tests/report/test_export.py -q -k empty
    acs: [AC2]
  - id: T3
    track: web
    do: Add the Export button that calls the endpoint and polls the job
    files: [web/src/report/ExportButton.tsx, web/src/report/ExportButton.test.tsx]
    verify: cd web && npm test -- ExportButton
    acs: [AC1]
integration:
  merge_order: [api, web]
  verify: pytest tests/report -q && (cd web && npm test -- ExportButton)
```
