---
read_when: "Designing or changing an HTTP API, service layer, or request flow"
---

# Web Architecture: Routes Translate, Services Decide

FastAPI (or equivalent) is an edge adapter. Business rules live in services and
repositories that can be tested without a server.

## MUST

- Route handlers: parse/validate input, call one service, return a typed
  response model. No branching on domain rules.
- Services hold business logic and return typed models, never `dict[str, Any]`.
- Repositories own persistence; no SQL in routes or services.
- Dependencies (session, client, clock, settings) are injected via FastAPI
  dependencies or constructors.
- Request/response schemas are Pydantic models with examples; validation errors
  are 422 with field paths.
- Long work is a background job with an id and status, not a blocked request.
- Settings come from the environment; no secrets in defaults.

## SHOULD

- `api/` (routes) → `services/` → `repositories/` → `models/`.
- One router per resource; stable paths and status codes.
- Idempotency keys for retryable writes.

## ANTI-PATTERNS

- SQL or HTTP calls in a route handler.
- Returning ORM objects directly.
- A service that needs a `Request` object.
- Catching exceptions to return 200.
- Global mutable state for per-request data.

## Checklist

- [ ] Route delegates to one service call.
- [ ] Typed request/response models.
- [ ] No persistence code outside repositories.
- [ ] Settings/secrets from env.
