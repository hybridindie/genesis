---
read_when: "Building or changing an MCP server's tool surface, transport, or safety gates"
---

# MCP Server Architecture: One Seam, One Contract

A server has three parts: the protocol edge (MCP), the domain libraries, and
the transport to anything it controls. Keep them separate.

## MUST

- Tool/resource/prompt handlers validate arguments, call one domain function,
  and return a typed result. No domain branching in handlers.
- Domain libraries import no MCP SDK types.
- Every tool declares typed input and output models; never raw `dict`.
- Tool names are stable, verb-first, and namespaced (`godot_scene_create`,
  not `do_create`). Renames need a deprecation path.
- The server owns safety: read-only / mutating / destructive / runtime classes,
  `dry_run` previews, `confirm=True` for destructive actions.
- The transport is the only path to the controlled process. No second code path.
- Long operations are cancellable and report progress.
- Toolset gating: core tools always on; everything else opt-in per category.

## SHOULD

- One category per tool; prefer fewer richer tools over micro-tools.
- Descriptions written for an agent: what it does, when to use it, what it
  returns, what can fail.
- Idempotent reads; explicit idempotency notes on writes.

## ANTI-PATTERNS

- A single `do(action, params)` dispatcher.
- Editor/UI knowledge inside the MCP layer.
- Safety checks in the client/addon instead of the server.
- Returning framework objects or non-serialisable values.
- Hidden global state in a long-lived server.

## Checklist

- [ ] Handler delegates; domain has no MCP imports.
- [ ] Typed input/output.
- [ ] Safety class + dry-run/confirm honoured.
- [ ] Transport is the only side-effect path.
