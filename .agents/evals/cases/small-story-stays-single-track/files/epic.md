**Why**

An empty report exports a zero-byte CSV, and finance's spreadsheet import rejects it (support ticket #311).

**Outcome**

Empty reports export a CSV with just the header row.

**Scope**

- **In:** CSV export of a report with no rows.
- **Out:** PDF export; any change to non-empty exports.

**Acceptance criteria**

- **AC1:** When a report with no rows is exported as CSV, then the file contains the header row, so that spreadsheet imports accept it.
- **AC2:** When a report with rows is exported as CSV, then the output is unchanged, so that existing consumers keep working.
- **AC3:** When a report with no rows is exported, then the response is still 200 text/plain, so that the download link keeps working.

<!-- agent-plan:generated -->
**Stories (dependency order)**

| ID | Issue | Story | Size | Priority | Wave | Depends on | Owns | ACs |
|----|-------|-------|------|----------|------|------------|------|-----|
| S1 | #61 | Empty reports export a header-only CSV | S | P1 | 1 | — | `backend/app/reports/service.py`, `backend/tests/test_reports.py` | AC1, AC2, AC3 |

**Parallelization map**

- **Shared contract:** none
- **Wave 1 (parallel):** S1
<!-- /agent-plan:generated -->

**Constraints and non-functional requirements**

- none known

**Risks and open questions**

- The header for an empty report must come from the report's column definition, which `service.py` does not expose yet.

**Success measures**

- Ticket #311 closed; no new import failures.

**Definition of done**

- [ ] All acceptance criteria met or explicitly descoped with a reason
- [ ] Every story traced to an AC or an explicit constraint
- [ ] Parallel waves and shared contracts are accurate
- [ ] Open questions resolved or assigned

```yaml agent-plan
version: 1
kind: epic
epic: "#60"
acs: [AC1, AC2, AC3]
contracts: []
stories:
  - id: S1
    title: Empty reports export a header-only CSV
    issue: "#61"
    type: bug
    size: S
    priority: P1
    acs: [AC1, AC2, AC3]
    owns: [backend/app/reports/service.py, backend/tests/test_reports.py]
    verify: cd backend && uv run pytest tests/test_reports.py -q
```
