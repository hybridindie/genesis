**Why**

Finance pastes CSV exports into slides by hand and logs in every Monday to pull
the weekly regional report (planning call, 2026-11-12).

**Outcome**

Any report downloads as a PDF, and a report can be emailed as a PDF on a weekly
schedule without anyone logging in.

**Scope**

- **In:** PDF export for any report; weekly schedules (weekday, time, up to 50
  recipients); email through the existing SMTP relay.
- **Out:** daily/monthly schedules (later release); branded PDF template
  (open question, Priya).

**Acceptance criteria**

- **AC1:** When a user downloads a report under 2,000 rows as PDF, then the PDF is returned in the response, so that small reports need no waiting.
- **AC2:** When a user requests a PDF of a report with 2,000 rows or more, then the API returns a job id and the UI shows the PDF when the job finishes, so that requests don't time out.
- **AC3:** When a user saves a weekly schedule with a weekday, time and recipients, then it is stored and listed on the report page, so that they can see what will be sent.
- **AC4:** When a schedule's time arrives, then each recipient receives the report PDF by email, so that finance gets it without logging in.
- **AC5:** When a schedule has more than 50 recipients, then saving it is rejected with an error naming the limit, so that ops' cap is enforced.

<!-- agent-plan:generated -->
**Stories (dependency order)**

| ID | Issue | Story | Size | Priority | Wave | Depends on | Owns | ACs |
|----|-------|-------|------|----------|------|------------|------|-----|
| S1 | #41 | Render a report as PDF | S | P0 | 1 | — | `backend/app/reports/pdf.py`, `backend/tests/test_pdf.py`, `backend/pyproject.toml` | AC1 |
| S4 | #44 | Store and validate weekly schedules | M | P1 | 1 | — | `backend/app/schedules/**`, `backend/app/main.py`, `backend/tests/test_schedules.py`, `backend/tests/test_schedule_models.py` | AC3, AC5 |
| S2 | #42 | PDF export endpoint with background jobs for large reports | M | P0 | 2 | S1 | `backend/app/reports/routes.py`, `backend/app/jobs/export.py`, `backend/tests/test_export_pdf.py` | AC1, AC2 |
| S5 | #45 | Schedule form on the report page | S | P1 | 2 | S4 | `frontend/src/schedules/**` | AC3, AC5 |
| S6 | #46 | Weekly sender emails the PDF | M | P1 | 2 | S1, S4 | `backend/app/jobs/weekly.py`, `backend/tests/test_weekly.py` | AC4 |
| S3 | #43 | Download PDF button with job polling | S | P1 | 3 | S2 | `frontend/src/reports/**`, `frontend/src/api.ts` | AC1, AC2 |

**Parallelization map**

- **Shared contract C1:** render_pdf(report) -> bytes, in backend/app/reports/pdf.py — owner S1, `backend/app/reports/pdf.py`
- **Shared contract C2:** Schedule model and /schedules API shape — owner S4, `backend/app/schedules/models.py`
- **Wave 1 (parallel):** S1, S4
- **Wave 2 (parallel, after Wave 1):** S2, S5, S6
- **Wave 3 (parallel, after Wave 2):** S3
<!-- /agent-plan:generated -->

**Constraints and non-functional requirements**

- Email only through the existing SMTP relay; credentials are in the secret store.
- Reuse the existing cron container for scheduled work.

**Risks and open questions**

- Branded template may be required (Priya to confirm) → PDF layout is isolated in one module.

**Success measures**

- Finance stops manual Monday exports (baseline: weekly manual pull today).

**Definition of done**

- [ ] All acceptance criteria met or explicitly descoped with a reason
- [ ] Every story traced to an AC or an explicit constraint
- [ ] Parallel waves and shared contracts are accurate
- [ ] Open questions resolved or assigned

```yaml agent-plan
version: 1
kind: epic
epic: "#40"
acs: [AC1, AC2, AC3, AC4, AC5]
contracts:
  - id: C1
    what: render_pdf(report) -> bytes, in backend/app/reports/pdf.py
    owner: S1
    paths: [backend/app/reports/pdf.py]
  - id: C2
    what: Schedule model and /schedules API shape
    owner: S4
    paths: [backend/app/schedules/models.py]
stories:
  - id: S1
    title: Render a report as PDF
    issue: "#41"
    type: technical
    size: S
    priority: P0
    acs: [AC1]
    owns: [backend/app/reports/pdf.py, backend/tests/test_pdf.py, backend/pyproject.toml]
    verify: cd backend && uv run pytest tests/test_pdf.py -q
  - id: S2
    title: PDF export endpoint with background jobs for large reports
    issue: "#42"
    type: user
    size: M
    priority: P0
    acs: [AC1, AC2]
    depends_on: [S1]
    owns: [backend/app/reports/routes.py, backend/app/jobs/export.py, backend/tests/test_export_pdf.py]
    verify: cd backend && uv run pytest tests/test_export_pdf.py -q
  - id: S3
    title: Download PDF button with job polling
    issue: "#43"
    type: user
    size: S
    priority: P1
    acs: [AC1, AC2]
    depends_on: [S2]
    owns: [frontend/src/reports/**, frontend/src/api.ts]
    verify: cd frontend && npm test -- --run reports
  - id: S4
    title: Store and validate weekly schedules
    issue: "#44"
    type: user
    size: M
    priority: P1
    acs: [AC3, AC5]
    owns: [backend/app/schedules/**, backend/app/main.py, backend/tests/test_schedules.py, backend/tests/test_schedule_models.py]
    verify: cd backend && uv run pytest tests/test_schedules.py -q
  - id: S5
    title: Schedule form on the report page
    issue: "#45"
    type: user
    size: S
    priority: P1
    acs: [AC3, AC5]
    depends_on: [S4]
    owns: [frontend/src/schedules/**]
    verify: cd frontend && npm test -- --run schedules
  - id: S6
    title: Weekly sender emails the PDF
    issue: "#46"
    type: user
    size: M
    priority: P1
    acs: [AC4]
    depends_on: [S1, S4]
    owns: [backend/app/jobs/weekly.py, backend/tests/test_weekly.py]
    verify: cd backend && uv run pytest tests/test_weekly.py -q
```
