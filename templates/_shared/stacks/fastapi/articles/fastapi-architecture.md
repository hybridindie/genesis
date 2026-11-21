---
read_when: "Designing or changing FastAPI routes, services, repositories, or request flow"
paths:
  - "{{BACKEND_PATH}}/**/*.py"
---

# FastAPI Architecture: Routes Translate, Services Decide

Applies `architecture.md` to FastAPI: routes are the entry layer, services the
domain, repositories the adapters. Contract details are in `api-design.md`.

## MUST

- Route handlers call one service and return a `response_model`.
- Services hold business logic and return typed models, never `dict[str, Any]`.
- Repositories own persistence; no SQL in routes or services.
- Inject session, client, clock and settings with `Depends` or constructors.
- Long work is a background job with an id and status, not a blocked request.
- Settings are a `pydantic-settings` model with no secret defaults.

## SHOULD

- `api/` (routes) → `services/` → `repositories/` → `models/`.
- One router per resource; stable paths and status codes.
- Idempotency keys for retryable writes.

## ANTI-PATTERNS

- SQL or HTTP calls in a route handler.
- A service that needs a `Request` object.
