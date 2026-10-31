---
read_when: "Adding a destructive or state-changing tool, or changing safety gates"
---

# MCP Safety: Classes, Previews, Preconditions

Agents run unattended. Safety is enforced in the server, never in the client.

## Classes

| Class | Meaning | Requirements |
|---|---|---|
| `read_only` | Never mutates | none |
| `mutating` | Reversible change | `dry_run` accepted; undo where the target supports it |
| `destructive` | Deletes/overwrites, may be irreversible | `dry_run` + `confirm=true` |
| `runtime` | Controls a running process | explicit start/stop, no implicit execution |

## MUST

- Every tool declares one class; the gate is enforced server-side.
- `dry_run=true` returns the planned effect and performs nothing.
- Destructive tools refuse without `confirm=true`, with a hint naming the flag.
- Preconditions fail before side effects:
  `{ ok: false, code: "PRECONDITION_FAILED", hint, required }`.
- Irreversible operations name their blast radius in the description.
- Batch operations above a safe threshold report `undoable: false` and
  what was already applied.
- Approval prompts (if any) are a guard, not a substitute for server checks.

## ANTI-PATTERNS

- "The client asks first" as the only protection.
- `confirm` accepted but ignored.
- A destructive tool without a preview mode.
- Deleting before validating the target.
- Treating a timeout as success.
