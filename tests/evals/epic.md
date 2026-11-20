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

**Stories**

| # | Story | ACs | Wave | Files |
|---|---|---|---|---|
| #12 | PDF template and renderer | AC1 | 1 | `src/report/pdf.py` |
| #13 | Export endpoint and button | AC1, AC2 | 2 | `src/report/routes.py` |
| #14 | Progress state | AC3 | 3 | `web/src/report/Export.tsx` |

**Parallelization map**

Shared contract: `POST /reports/{id}/export` returns a job id; the client polls
`GET /exports/{job}`.

- Wave 1: #12 (template) — owns `src/report/pdf.py`.
- Wave 2: #13 (endpoint + button) — owns `src/report/routes.py`.
- Wave 3: #14 (progress) — owns `web/src/report/Export.tsx`.

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
