# reports-app

Internal reporting tool: FastAPI backend, React (Vite) frontend.

## Commands
- Backend tests: `cd backend && uv run pytest -q`
- Backend lint: `cd backend && uv run ruff check .`
- Frontend tests: `cd frontend && npm test -- --run`
- Frontend types: `cd frontend && npx tsc --noEmit`

## Layout
- `backend/app/main.py` — FastAPI app, mounts routers
- `backend/app/reports/` — report queries (`service.py`) and routes (`routes.py`)
- `backend/tests/` — pytest suites, one file per module
- `frontend/src/reports/` — report list and view components
- `frontend/src/api.ts` — typed fetch client for the backend
