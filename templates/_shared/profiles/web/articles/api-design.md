---
read_when: "Designing HTTP endpoints, request/response schemas, or OpenAPI docs"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
---

# API Contract & Documentation (Article VI)

- Every endpoint fully documented with OpenAPI (FastAPI auto-generates)
- Provide `summary`, `description` (if non-trivial), and `response_model` for each route
- Version or document breaking changes prior to merging
- Validate all inbound payloads using Pydantic models (no raw dict handling)
- Add examples to model `model_config` or `json_schema_extra` for clarity
- Route handlers: parsing + dependency injection + delegation only

ANTI-PATTERNS:
- Silent shape changes without migration notes
- Business logic in route handlers (delegate to service layer)
