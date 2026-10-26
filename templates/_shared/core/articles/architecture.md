---
read_when: "Designing modules, moving logic between layers, or adding an entry point"
---

# Architecture: Thin Edges, Explicit Boundaries

Every project has an entry layer (HTTP routes, MCP tools, CLI commands, editor
handlers) and domain code. The entry layer translates; the domain decides.

## MUST

- Entry handlers validate input, call one domain function, and return a typed result. No domain branching.
- Domain code is importable without the entry framework — no FastAPI/MCP/editor imports.
- Dependencies (DB, HTTP, clock, RNG, filesystem) are injected, never module globals.
- Public functions return typed values (dataclasses/Pydantic), never `dict[str, Any]`.
- No side effects at import time (no connections, no `run()`).
- Imports flow one way: entry → domain → adapters. No cycles.

## SHOULD

- One module per concern; split at ~300 lines, block merges at ~500.
- Pure functions for decisions, thin wrappers for IO.
- Errors defined next to the domain that raises them.

## ANTI-PATTERNS (BLOCKING)

- Business rules in a route/tool/command handler.
- Domain code importing the entry framework.
- Global mutable state holding per-request data.
- `datetime.now()` / `random` without injection.
- A second code path that bypasses the normal boundary.

## Checklist

- [ ] Handler is short and delegates.
- [ ] Domain module imports no entry-layer packages.
- [ ] New dependency is injected.
- [ ] No import-time side effects.
