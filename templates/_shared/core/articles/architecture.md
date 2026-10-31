---
read_when: "Designing modules, moving logic between layers, or adding an entry point"
---

# Architecture: Thin Edges, Explicit Boundaries

Every project has an entry layer (HTTP routes, MCP tools, CLI commands, editor
or game handlers) and domain code. The entry layer translates; the domain
decides. Stack rules (web, MCP, Godot) refine this file.

## MUST

- Entry handlers validate input, call into the domain, and return a typed
  result. Business rules do not live in handlers.
- Domain code does not import the entry framework (FastAPI, MCP SDK, editor
  APIs), so it can be tested without it.
- Things that make tests nondeterministic or slow (clock, RNG, network, DB,
  filesystem) are passed in, not reached through module globals.
- No side effects at import or load time (no connections, no server start).
- Dependencies point one way: entry → domain → adapters. No cycles.

## SHOULD

- Return typed values (dataclasses, Pydantic, typed dictionaries) across
  module boundaries rather than loose `dict[str, Any]`.
- One module per concern. Past ~400 lines, split it or say in the PR why not.
- Pure functions for decisions; thin wrappers for IO.
- Libraries stay consumer-agnostic: they never import or special-case the
  projects that use them.

## ANTI-PATTERNS

- A second code path that bypasses the normal boundary.
- Global mutable state holding per-request or per-run data.
