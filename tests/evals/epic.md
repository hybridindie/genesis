# Epic: Export a report as PDF

**Why**

Finance re-types report numbers into slides every week. One export removes that
step and the transcription errors that come with it.

**Outcome**

A reader of a shared report can download the same numbers as a PDF, without
asking engineering to produce it.

**Scope**

- In: a PDF export button on the report page, one template, the existing
  numbers.
- Out: scheduled email delivery, custom branding, Excel export.

**Acceptance criteria**

- **AC1:** **Given** a report with data, **when** the reader chooses Export,
  **then** a PDF with the same rows downloads.
- **AC2:** **Given** a report with no data, **when** the reader chooses Export,
  **then** a PDF with an empty-state line downloads.
- **AC3:** **Given** the export is running, **when** it takes longer than two
  seconds, **then** a progress state is shown until the download starts.

<!-- agent-plan:generated -->
**Stories (dependency order)**

| ID | Issue | Story | Size | Priority | Wave | Depends on | Owns | ACs |
|----|-------|-------|------|----------|------|------------|------|-----|
| S1 | #12 | PDF template and renderer | S | P0 | 1 | — | `src/report/pdf.py`, `tests/report/test_pdf.py` | AC1, AC2 |
| S2 | #13 | Export endpoint and button | M | P0 | 2 | S1 | `src/report/routes.py`, `tests/report/test_export.py`, `web/src/report/ExportButton.tsx`, `web/src/report/ExportButton.test.tsx` | AC1, AC2 |
| S3 | #14 | Progress state | S | P1 | 3 | S2 | `web/src/report/ExportProgress.tsx`, `web/src/report/ExportProgress.test.tsx` | AC3 |

**Parallelization map**

- **Shared contract C1:** render_report_pdf(report) -> bytes, in src/report/pdf.py — owner S1, `src/report/pdf.py`
- **Wave 1 (parallel):** S1
- **Wave 2 (parallel, after Wave 1):** S2
- **Wave 3 (parallel, after Wave 2):** S3
<!-- /agent-plan:generated -->

**Constraints**

- The report numbers must come from the existing query, not a second copy.
- No new runtime dependency for PDF generation.

**Risks**

- Font rendering differs per platform; the template must embed fonts.
- Large reports may exceed the two-second budget, which is why AC3 exists.

**Success measures**

- Zero hand-typed numbers in the next finance deck.
- Export failures under 1% of attempts.

**Definition of done**

- All three acceptance criteria pass, the gate is green, and the button is in
  the report page for every reader.

```yaml agent-plan
version: 1
kind: epic
epic: "#11"
acs: [AC1, AC2, AC3]
contracts:
  - id: C1
    what: render_report_pdf(report) -> bytes, in src/report/pdf.py
    owner: S1
    paths: [src/report/pdf.py]
stories:
  - id: S1
    title: PDF template and renderer
    issue: "#12"
    type: technical
    size: S
    priority: P0
    acs: [AC1, AC2]
    owns: [src/report/pdf.py, tests/report/test_pdf.py]
    verify: pytest tests/report/test_pdf.py -q
  - id: S2
    title: Export endpoint and button
    issue: "#13"
    type: user
    size: M
    priority: P0
    acs: [AC1, AC2]
    depends_on: [S1]
    owns: [src/report/routes.py, tests/report/test_export.py, web/src/report/ExportButton.tsx, web/src/report/ExportButton.test.tsx]
    verify: pytest tests/report/test_export.py -q && (cd web && npm test -- ExportButton)
  - id: S3
    title: Progress state
    issue: "#14"
    type: user
    size: S
    priority: P1
    acs: [AC3]
    depends_on: [S2]
    owns: [web/src/report/ExportProgress.tsx, web/src/report/ExportProgress.test.tsx]
    verify: cd web && npm test -- ExportProgress
```
