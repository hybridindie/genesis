# Story #13 — Export endpoint and button

**What**

**As a** report reader, **I want** an Export action on the report page, **so
that** I can download the numbers without asking engineering.

Part of #11

**Estimate:** 3 points · **Wave:** 2

**Acceptance criteria**

- [ ] **Given** a report with data, **when** the reader chooses Export,
  **then** a PDF downloads and the response is a `job` id.
- [ ] **Given** a report with no data, **when** the reader chooses Export,
  **then** the PDF carries the empty-state line instead of failing.

**Parallelization**

- Depends on: #12 (the template).
- Unblocks: #14 (progress state).

**Files**

Owns `src/report/routes.py` and `web/src/report/Export.tsx`. Does not touch
`src/report/pdf.py` (owned by #12).

**Tasks**

- [ ] **T1** Add `POST /reports/{id}/export` returning a job id — verify:
  `pytest tests/report/test_export.py -k endpoint`
- [ ] **T2** Add the Export button that calls it — verify:
  `cd web && npm test -- Export`
- [ ] **T3** Cover the empty report case — verify:
  `pytest tests/report/test_export.py -k empty`

**Done when**

Both criteria pass, the endpoint and button are exercised by tests, and the
route is listed in the OpenAPI output.
