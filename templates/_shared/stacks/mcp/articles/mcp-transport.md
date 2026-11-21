---
read_when: "Changing the bridge, message envelope, timeouts, reconnect, or any client/server transport"
paths:
  - "{{BACKEND_PATH}}/**/*.py"
---

# MCP Transport: Correlated, Timed Out, Reconnecting

The transport is the only seam between the server and whatever it controls
(addon, bridge, subprocess). One envelope, one correlation id, one failure mode.

## Envelope

```json
{ "id": "uuid", "command": "cmd_name", "params": { } }
{ "id": "uuid", "ok": true,  "result": { } }
{ "id": "uuid", "ok": false, "error": "TIMEOUT", "hint": "…", "required": "…" }
```

- Version the envelope from day one.
- Correlate every response to its request by `id`; many in-flight commands are
  allowed and resolved independently.
- Results and errors are JSON-safe; no host objects, no NaN, no bytes unless
  explicitly encoded.

## MUST

- Every request has an explicit timeout; expiry resolves to a `TIMEOUT`
  envelope, never a hang.
- A send with no connected peer resolves immediately as `BRIDGE_DISCONNECTED`.
- The client owns reconnection (backoff per `async-patterns.md`); the server
  accepts one active peer and replaces the old one.
- A health ping (`ping` → `pong`) proves liveness.

## ANTI-PATTERNS

- Fire-and-forget commands with no waiter.
- A second path that bypasses the envelope.
- Timeout kills reported as ordinary non-zero exits.
