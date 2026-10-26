---
read_when: "Changing the bridge, message envelope, timeouts, reconnect, or any client/server transport"
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
- Reconnection is owned by the client, with bounded exponential backoff +
  jitter; the server accepts one active peer and replaces the old one.
- A health ping (`ping` → `pong`) proves liveness.
- No blocking read on the event loop; the runtime owns the loop.
- Log the command id with every transport error.

## ANTI-PATTERNS

- Fire-and-forget commands with no waiter.
- A second path that bypasses the envelope.
- Timeout kills reported as ordinary non-zero exits.
- Retrying a non-idempotent command after an unknown outcome.

## Checklist

- [ ] Envelope versioned and typed.
- [ ] Timeout on every request.
- [ ] Disconnected peer fails fast.
- [ ] Reconnect bounded and observable.
