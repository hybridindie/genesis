---
read_when: "Writing async or deferred work in a Godot addon or editor tool"
---

# Godot Async: Never Block the Editor

The editor runs one main thread. Anything slow must be deferred, chunked, or
moved to a worker with an explicit hand-back.

## MUST

- No blocking work in a command handler: no `OS.delay_msec`, tight loops,
  synchronous I/O, or network waits.
- Use `call_deferred` / `await get_tree().process_frame` to yield; do not spin.
- Worker threads return to the main thread via `call_deferred`; never touch the
  scene tree from a worker.
- Every long operation has a cancellation path and reports progress.
- Awaiting a signal that may never fire has a timeout (`get_tree().create_timer`).
- Errors from async work are surfaced through the router as structured results,
  not `push_error` alone.

## SHOULD

- Chunk large scene operations across frames and keep the editor responsive.
- One in-flight operation per target; reject or queue a concurrent one.
- Log start/finish with the command id.

## ANTI-PATTERNS

- Blocking the editor while an agent/server responds.
- Unawaited coroutines that outlive the plugin (disable/enable leak).
- Scene-tree access from a `Thread`.
- `while true` with no frame yield.
- Silent failure after a timeout.

## Checklist

- [ ] No blocking in handlers.
- [ ] Long work is cancellable and reports progress.
- [ ] Worker hand-back is deferred.
- [ ] Async failures are returned, not printed.
