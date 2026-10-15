# GitHub Copilot Project Instructions – InfluencerSync

Authoritative context for AI code suggestions in this repository. Keep guidance concise in generated code; do not restate this whole file inside source. Use it to influence *how* you suggest code.

Scope: This document is self-contained for GitHub Copilot; the only shared authoritative source across agents is `/.claude/rules/` (Articles I-IX).

---
## GitHub Interaction Policy
- Use GitHub MCP server tools for all GitHub interactions.
- Do not use `gh` CLI for issues, pull requests, branches, commits, labels, or reviews.
- Use MCP issue/PR listing and search tools to gather project context.

---
## 1. Core Mission
Baseline for Python / TypeScript in an ML setting. All new or refactored code MUST comply with the Constitutional Articles below, grouped by concern:

- **Structure** (I–II): library-first, service isolation
- **Quality** (III, VIII): TDD, CI/CD determinism
- **Reliability** (IV–V): structured errors, async-first
- **API & Security** (VI–VII): OpenAPI docs, auth/encryption
- **Traceability** (IX): inline Article references in non-trivial logic

---
## 2. Constitutional Articles (Enforce in Suggestions)
| Article | Requirement (Summarized for Code Generation) |
|---------|----------------------------------------------|
| I | Every feature = standalone library (in `backend/src/libs/<service_name>`). No business logic inside API route modules. `src/libs/` MUST NOT import from `app.*`. |
| II | Service isolation: all business logic testable independently of HTTP layer. Services accept dependency-injected clients, return typed results. No FastAPI imports in service layer. |
| III | TDD mandatory. Always propose/expect a failing test first. Maintain coverage per constitution. Prefer contract/integration tests over excessive mocking. |
| IV | Structured error handling: domain exceptions inherit from a common base (e.g., `DomainError`). Never `print` raw tracebacks; return structured error objects. |
| V | Async‑first. Use `async def`, `httpx.AsyncClient`, async SQL layers. No shared mutable global state. Inject dependencies explicitly. |
| VI | All FastAPI endpoints documented (summary, description, response models) and included in OpenAPI. Provide explicit response model classes. |
| VII | Auth via OAuth2/JWT. Sensitive data encrypted (AES‑256) and secrets never hard‑coded. Redact tokens in logs. Token lifetimes: access ≤ 15min, refresh ≤ 7d. |
| VIII | CI/CD ready: deterministic tests, type safety, lint cleanliness. Avoid flaky time/network dependent code unless controlled. |
| IX | Reference the constitution when adding non‑trivial logic in docstrings or comments (e.g., `# Article V: async-first, no blocking call`). |

---
## 3. Architectural Directives
- Backend structure: service libraries in `backend/src/libs/` (e.g., `auth_manager`, `analytics_engine`, `content_manager`, `scheduler_service`, `ai_coach`).
- FastAPI layer (`backend/app/`) = thin orchestration + request/response translation + dependency wiring only.
- Libraries expose:
  - Domain models (Pydantic) – stable contracts.
  - Service layer (pure async functions) – no framework imports.
  - Error types (structured hierarchy) & mappers.
- State management: ephemeral per request; use PostgreSQL (pgmq for queues, LISTEN/NOTIFY for events, UNLOGGED tables for cache)—never in‑memory globals.
- MLflow Prompt Registry: All AI/LLM prompts are versioned in MLflow and loaded at runtime.
- MLflow Prompt Registry is the REQUIRED source in normal operation; prompt updates must be published there before rollout.
- Python constants are seed material and degraded-state fallback only (not a primary runtime source).
- Prompts cached in Postgres (`app_cache`) with process-local mirror.

---
## 4. Testing Hierarchy (Generate in This Order)
1. Contract tests (`tests/contract/`): interface & payload shapes.
2. Integration tests (`tests/integration/`): real adapters (DB, message bus) where feasible.
3. E2E tests (`tests/e2e/`): full API/user flows.
4. Unit tests (`tests/unit/`): focused logic; avoid mocking entire subsystems.

Rules:
- New functionality: propose a failing test stub first with an assertion that currently fails.
- Coverage target: tiered by criticality (Security 90%+, Revenue 85%+, Business logic 70%+, AI/ML 50%+, Utilities 50%+; aggregate 70%). See constitution Article III.
- Use `pytest` async patterns (`pytest.mark.asyncio`).

---
## 5. Error Handling Blueprint
Create a shared base, e.g.:
```python
class DomainError(Exception):
    def __init__(self, code: str, message: str, *, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
```
Map these to HTTP responses in FastAPI routers with consistent JSON shape:
```json
{"error": {"code": "RESOURCE_NOT_FOUND", "message": "...", "details": {}}}
```
Never leak stack traces or internal identifiers. For HTTP status mapping of DomainError codes, see the constitution (Article IV).

---
## 6. Async & Concurrency
- Use async DB drivers / clients.
- No blocking I/O inside async functions (wrap legacy sync calls in `run_in_executor` ONLY if unavoidable, and mark with Article V reference).
- Avoid shared mutable containers; prefer function parameters and return values.
- Idempotent operations for retriable actions.
- Always set explicit timeouts for external I/O (HTTP/DB/cache/message bus).
- Batch‑process large datasets asynchronously — no synchronous loops over unbounded collections.
- Multi‑step workflows that must be atomic: use outbox/saga pattern, not fire‑and‑forget.

---
## 7. Security & Compliance
- JWT handling: short‑lived access (≤ 15min), refresh ≤ 7d. Verify signature & expiry.
- Encryption: if generating suggestions for encryption utilities, use AES‑256 GCM mode (libsodium/cryptography) with secure random nonce.
- Sanitize all external inputs; never trust client JSON.
- Do NOT log PII or secrets.
- Prefer actively maintained libraries; audit dependencies for CVEs before adoption.
- Validate security‑critical config at application startup — reject missing/weak secrets in production.

---
## 8. FastAPI Endpoint Style
```python
@router.post("/resource", response_model=ResourceOut, summary="Create resource")
async def create_resource(payload: ResourceIn, deps=Depends(...)):
    # Article I: delegate to library
    result = await resource_service.create(payload)
    return result
```
No domain calculations inline; ALWAYS delegate to a library function.

---
## 9. Pydantic Model Conventions
- Separate input (`FooIn`), internal/domain (`FooModel`), and output (`FooOut`) when transformations occur.
- Use `field_validator` (Pydantic v2) for domain invariants.
- Include explicit `Config` / model config (e.g., `json_schema_extra`) for OpenAPI clarity when needed.

---
## 10. Logging & Observability
- Use structured logging (suggest `structlog` or standard library `logging` with JSON formatter) at the boundary layers only.
- Library core code should return rich error objects instead of logging.

---
## 11. Frontend (If Suggesting Full‑Stack Changes)
- React 19 + Zustand stores only for client state (auth, analytics, platforms, content).
- Service calls go through dedicated service modules – no direct fetch in components.
- Error boundaries & typed error envelopes.
- Avoid adding global mutable singletons outside Zustand.
- No `as any` casts — use proper generics, type widening, or `as never` for test mocks.
- No `dangerouslySetInnerHTML` or raw `innerHTML` — use DOMPurify or text content.
- No `console.log` in production code — remove or gate behind `import.meta.env.DEV`.
- Zustand stores ≤ 300 lines; split into sub‑stores with `immer` middleware when larger.

---
## 12. Suggestion Do / Do Not
Do:
- For all new functionality or refactored code, propose a failing test first before implementation.
- Reference Articles in critical comments.
- Keep functions small, pure, and side‑effect minimal.
- Use dependency injection patterns.
- Provide type annotations everywhere.
- Favor composition over inheritance (except error base class).

Do NOT:
- Insert blocking `time.sleep` or synchronous DB calls in async code.
- Embed secrets, keys, tokens, or raw credentials.
- Add business logic directly into FastAPI routes.
- Write print statements for operational logging.
- Suggest code without corresponding tests (unless user explicitly requests exploratory snippet).
- Use bare `except Exception` — catch specific DomainError subclasses.
- Use `asyncio.sleep()` in tests — use deterministic waits or condition polling.
- Return `dict[str, Any]` from service methods — define Pydantic response models.

---
## 13. Common Templates (For Copilot Prompt Bias)
Test First Skeleton:
```python
# tests/contract/test_<service>_<action>.py
import pytest
from libs.<service>.models import <Model>

@pytest.mark.asyncio
async def test_<action>_contract__fails_without_required_field():
    # Arrange
    payload = {...}  # Missing required field
    # Act / Assert
    with pytest.raises(ValueError):
        await <service>_service.<action>(payload)
```
Domain Service Function Skeleton:
```python
# Article I, III, V
async def create_resource(payload: ResourceIn) -> ResourceOut:
    # Validate (Article III tests enforce these contracts)
    # Interact with persistence via injected repository
    # Return pure Pydantic model
    ...
```

---
## 14. Coverage & Quality Hooks
- Always suggest adding an additional edge case test (empty input, large input, unauthorized, race condition) after main path.
- Encourage property‑based tests for invariant‑heavy logic (but keep minimal when first introducing).

---
## 15. Migration / Refactor Guidance
When modernizing legacy code:
- Extract pure functions to `libs/<service>/core/`.
- Wrap legacy sync calls behind async facades with explicit TODO + Article reference.
- Replace inline validation with Pydantic model validators.

---
## 16. Acceptance Checklist (Apply Mentally Before Suggesting Final Code)
- Test exists & fails initially? (Article III)
- Business logic isolated in library? (Article I)
- Async and non‑blocking? (Article V)
- Structured error paths? (Article IV)
- Endpoint documented & typed? (Article VI)
- Security considerations addressed? (Article VII)
- No global mutable singletons? (Article V)

---
## 17. When User Requests a Quick Hack
Politely steer toward constitutional compliance. If they explicitly insist, annotate generated code with `# WARNING: Non-compliant (explain)` so it is easy to refactor later.

---
## 18. Referencing the Constitution
Use concise inline references, e.g.:
```python
# Article V: ensure async DB interaction
```
Do not paste the full constitution text.

---
## 19. Evolution
If future changes require updating these instructions: create a PR modifying ONLY this file and reference rationale + impacted Constitution Articles. These instructions stand alone; do not couple changes here to other agent prompt files.

---
## 20. Final Principle
Every suggestion should reduce future refactor cost while increasing reliability, clarity, and verifiability.

---
## Versioning Policy (CalVer)
All version references and bumps MUST follow CalVer (YYYY.MM.DD[-N]). When suggesting or applying a version change, ensure:
- The authoritative constitution rules live in `/.claude/rules/`.
- Changelog entries reflect the CalVer date.
- Refer to the Constitution's Versioning Policy for specifics.

---
End of Copilot Instructions.

## wiki-fabric (copilot)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace). It costs you 0 tokens to read and saves you exploration — every rule below is about doing LESS work, not more.

While coding:
- **Knowledge first, once.** If a `# Context Manifest` is already in your context, use it — do NOT run `wf context` again. Otherwise run `wf context --task "<task>"` once, before exploring. The delivered knowledge is BINDING: follow it and cite the `[[id]]` you relied on. A `where:` line under an item is the code location — open that file directly instead of searching for it.
- For a "why / what was decided / what broke before" question, `wf query "<question>"` answers from recorded evidence (0 tokens) — use it instead of grepping history.
- **At most one log call, at the very end, only for a non-trivial lesson** (a surprise, a gotcha, a rejected approach — not a routine change): `wf log --project <slug> --problem "<one sentence>" --intervention "<one sentence>"`. It is a single non-interactive command; never pipe input into it, and skip it entirely for routine work.

Do NOT run fabric maintenance during a coding task (`wf inbox`, `wf lint`, `wf status`, `wf ingest`, `wf promote`, `wf review`) unless the user asks you to work on the fabric itself — those are human-review workflows (`wf skill --list` describes them when needed).

CLI: `wf help` | With graphify installed: graphify owns code-symbol/call-graph questions; the fabric owns recorded knowledge (decisions, gotchas, history).
<!-- /wiki-fabric:copilot -->
