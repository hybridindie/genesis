---
read_when: "Structuring an MCP server: tool surface layout, toolset gating, or where safety and transport live"
paths:
  - "{{BACKEND_PATH}}/**/*.py"
---

# MCP Server Architecture: One Seam, One Contract

Builds on `architecture.md`: the MCP layer is the entry layer. Contract,
safety, transport, and testing details are in the other `mcp-*` rules.

## MUST

- Domain libraries import no MCP SDK types; tool handlers validate, delegate,
  and return a documented result shape.
- The server owns safety (`mcp-safety.md`); clients and addons are never the
  only guard.
- The transport is the only path to the controlled process
  (`mcp-transport.md`).
- Toolsets are gated server-side (`mcp-contract.md`).
- The server stays harness-agnostic: no assumptions about which agent or
  client calls it.

## SHOULD

- Fewer, richer tools over many micro-tools; one category per tool.
- Long operations report progress and can be cancelled.

## ANTI-PATTERNS

- Editor or UI knowledge inside the MCP layer.
- Hidden global state in a long-lived server.
