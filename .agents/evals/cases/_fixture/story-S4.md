Part of #40 · Story S4

**As a** finance analyst, **I want** to save a weekly schedule for a report, **so that** it is emailed without me logging in.

**Context**

There is no schedules code yet. Add a `schedules` package under `backend/app/schedules/` (new): a SQLAlchemy `Schedule` model (report_id, weekday 0–6, time HH:MM, recipients list), and a router mounted at `/schedules` in `backend/app/main.py`. The model and request/response schema are contract C2: S5 (UI) and S6 (sender) build on them.

**Acceptance criteria**

- [ ] **Given** a valid weekday, time and up to 50 recipients, **when** POST /schedules is called, **then** it returns 201 and GET /schedules?report_id= lists it.
- [ ] **Given** 51 recipients, **when** POST /schedules is called, **then** it returns 422 with a message naming the 50-recipient limit.

<!-- agent-plan:generated -->
**Parallelization**

| Track | Kind | Owns | Depends on | Parallel with | Verify | Status |
|-------|------|------|------------|---------------|--------|--------|
| contract | contract | `backend/app/schedules/models.py`, `backend/app/schedules/__init__.py`, `backend/tests/test_schedule_models.py` | — | — | `cd backend && uv run pytest tests/test_schedule_models.py -q` | todo |
| api — Schedules API | track | `backend/app/schedules/routes.py`, `backend/app/main.py`, `backend/tests/test_schedules.py` | contract | — | `cd backend && uv run pytest tests/test_schedules.py -q` | todo |

- **Integration:** merge contract → api, then `cd backend && uv run pytest -q`

**Tasks**

_contract_
- [ ] **T1** — Define Schedule model and ScheduleIn/ScheduleOut schemas (recipients max 50) in backend/app/schedules/models.py (new) — files `backend/app/schedules/models.py`, `backend/app/schedules/__init__.py` — AC3, AC5 — verify `cd backend && uv run python -c "from app.schedules.models import ScheduleIn"`
- [ ] **T2** — Test the 50-recipient validation in backend/tests/test_schedule_models.py (new) — files `backend/tests/test_schedule_models.py` — after T1 — AC5 — verify `cd backend && uv run pytest tests/test_schedule_models.py -q`

_api_
- [ ] **T3** — Add POST /schedules and GET /schedules?report_id= in backend/app/schedules/routes.py (new) and mount it in backend/app/main.py — files `backend/app/schedules/routes.py`, `backend/app/main.py` — after T1 — AC3, AC5 — verify `cd backend && uv run pytest tests/test_schedules.py -q`
- [ ] **T4** — Test create, list and the 422 for 51 recipients in backend/tests/test_schedules.py (new) — files `backend/tests/test_schedules.py` — after T3 — AC3, AC5 — verify `cd backend && uv run pytest tests/test_schedules.py -q`
<!-- /agent-plan:generated -->

**Notes and risks**

- Mounting the router edits `backend/app/main.py`, which no parallel story owns.

**Done when**

- [ ] Acceptance criteria pass
- [ ] Every track's verify passes and the integration check is green
- [ ] No files outside the declared ownership changed

```yaml agent-plan
version: 1
kind: story
story: S4
epic: "#40"
issue: "#44"
branch: feat/44-weekly-schedules
acs: [AC3, AC5]
ac_text:
  AC3: Given a valid weekday, time and up to 50 recipients, when POST /schedules is called, then it returns 201 and GET /schedules?report_id= lists it.
  AC5: Given 51 recipients, when POST /schedules is called, then it returns 422 with a message naming the 50-recipient limit.
owns: [backend/app/schedules/**, backend/app/main.py, backend/tests/test_schedules.py, backend/tests/test_schedule_models.py]
verify: cd backend && uv run pytest tests/test_schedules.py tests/test_schedule_models.py -q
context: >-
  No schedules code exists. Add backend/app/schedules/ (new) with a SQLAlchemy
  Schedule model and pydantic schemas (contract C2), and a router mounted at
  /schedules in backend/app/main.py. Max 50 recipients per schedule.
tracks:
  - id: contract
    kind: contract
    owns: [backend/app/schedules/models.py, backend/app/schedules/__init__.py, backend/tests/test_schedule_models.py]
    verify: cd backend && uv run pytest tests/test_schedule_models.py -q
  - id: api
    kind: track
    name: Schedules API
    owns: [backend/app/schedules/routes.py, backend/app/main.py, backend/tests/test_schedules.py]
    depends_on: [contract]
    verify: cd backend && uv run pytest tests/test_schedules.py -q
tasks:
  - id: T1
    track: contract
    do: Define Schedule model and ScheduleIn/ScheduleOut schemas (recipients max 50) in backend/app/schedules/models.py (new)
    files: [backend/app/schedules/models.py, backend/app/schedules/__init__.py]
    verify: cd backend && uv run python -c "from app.schedules.models import ScheduleIn"
    acs: [AC3, AC5]
  - id: T2
    track: contract
    do: Test the 50-recipient validation in backend/tests/test_schedule_models.py (new)
    files: [backend/tests/test_schedule_models.py]
    depends_on: [T1]
    verify: cd backend && uv run pytest tests/test_schedule_models.py -q
    acs: [AC5]
  - id: T3
    track: api
    do: Add POST /schedules and GET /schedules?report_id= in backend/app/schedules/routes.py (new) and mount it in backend/app/main.py
    files: [backend/app/schedules/routes.py, backend/app/main.py]
    depends_on: [T1]
    verify: cd backend && uv run pytest tests/test_schedules.py -q
    acs: [AC3, AC5]
  - id: T4
    track: api
    do: Test create, list and the 422 for 51 recipients in backend/tests/test_schedules.py (new)
    files: [backend/tests/test_schedules.py]
    depends_on: [T3]
    verify: cd backend && uv run pytest tests/test_schedules.py -q
    acs: [AC3, AC5]
integration:
  merge_order: [contract, api]
  verify: cd backend && uv run pytest -q
```
