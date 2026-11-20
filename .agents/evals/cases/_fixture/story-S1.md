Part of #40 · Story S1

**What** Add a PDF renderer for reports. **Why** Both the export endpoint (S2) and the weekly sender (S6) need the same PDF bytes.

**Context**

`backend/app/reports/service.py` has `Report` (id, title, rows) and `to_csv`. There is no PDF code yet. Use `reportlab` (add it to `backend/pyproject.toml` dependencies). The function signature is the contract C1 other stories build on.

**Acceptance criteria**

- [ ] **Given** a report with rows, **when** `render_pdf(report)` is called, **then** it returns bytes starting with `%PDF` that contain the report title.

<!-- agent-plan:generated -->
**Parallelization**

| Track | Kind | Owns | Depends on | Parallel with | Verify | Status |
|-------|------|------|------------|---------------|--------|--------|
| main | track | `backend/app/reports/pdf.py`, `backend/tests/test_pdf.py`, `backend/pyproject.toml` | — | — | `cd backend && uv run pytest tests/test_pdf.py -q` | todo |

**Tasks**

_main_
- [ ] **T1** — Add reportlab to backend/pyproject.toml and render_pdf(report) -> bytes in backend/app/reports/pdf.py (new) — files `backend/pyproject.toml`, `backend/app/reports/pdf.py` — AC1 — verify `cd backend && uv run python -c "from app.reports.pdf import render_pdf"`
- [ ] **T2** — Test that render_pdf output starts with %PDF and contains the title, in backend/tests/test_pdf.py (new) — files `backend/tests/test_pdf.py` — after T1 — AC1 — verify `cd backend && uv run pytest tests/test_pdf.py -q`
<!-- /agent-plan:generated -->

**Notes and risks**

- Branded template may be required later; keep layout in one function.

**Done when**

- [ ] Acceptance criteria pass
- [ ] Every track's verify passes and the integration check is green
- [ ] No files outside the declared ownership changed

```yaml agent-plan
version: 1
kind: story
story: S1
epic: "#40"
issue: "#41"
branch: feat/41-render-pdf
acs: [AC1]
ac_text:
  AC1: Given a report with rows, when render_pdf(report) is called, then it returns bytes starting with %PDF that contain the report title.
owns: [backend/app/reports/pdf.py, backend/tests/test_pdf.py, backend/pyproject.toml]
verify: cd backend && uv run pytest tests/test_pdf.py -q
context: >-
  backend/app/reports/service.py defines Report(id, title, rows). Add
  render_pdf(report: Report) -> bytes in backend/app/reports/pdf.py (new) using
  reportlab, added to backend/pyproject.toml dependencies.
tracks:
  - id: main
    kind: track
    owns: [backend/app/reports/pdf.py, backend/tests/test_pdf.py, backend/pyproject.toml]
    verify: cd backend && uv run pytest tests/test_pdf.py -q
tasks:
  - id: T1
    track: main
    do: Add reportlab to backend/pyproject.toml and render_pdf(report) -> bytes in backend/app/reports/pdf.py (new)
    files: [backend/pyproject.toml, backend/app/reports/pdf.py]
    verify: cd backend && uv run python -c "from app.reports.pdf import render_pdf"
    acs: [AC1]
  - id: T2
    track: main
    do: Test that render_pdf output starts with %PDF and contains the title, in backend/tests/test_pdf.py (new)
    files: [backend/tests/test_pdf.py]
    depends_on: [T1]
    verify: cd backend && uv run pytest tests/test_pdf.py -q
    acs: [AC1]
```
