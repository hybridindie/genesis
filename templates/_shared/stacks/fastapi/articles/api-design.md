---
read_when: "Designing HTTP endpoints, request/response schemas, or OpenAPI docs"
paths:
  - "{{BACKEND_PATH}}/**/api/**/*.py"
  - "{{BACKEND_PATH}}/**/routes/**/*.py"
---

# API Contract

The OpenAPI schema is the contract the frontend and other clients build
against.

## MUST

- Every route has a typed request model and `response_model`; no raw `dict`
  payloads in or out.
- Routes have a `summary`; non-obvious ones have a `description` and an
  example on the model.
- Validation errors return 422 with field paths; other errors follow
  `error-handling.md`.
- A breaking change to a path, field, or status code is called out in the PR
  and either versioned or coordinated with every client in the same change.
- A contract test covers each new or changed route.

## ANTI-PATTERNS

- Silent shape changes (renamed or retyped fields) without a client update.
- Returning ORM/DB rows directly instead of a response model.
