---
read_when: "Writing async code, transports, background jobs, or anything with timeouts"
---

# Async: Never Block, Always Time Out

## MUST

- Every awaitable call that crosses a process, network, or disk boundary has a
  timeout with a defined failure mode.
- No blocking calls inside an async path: no `time.sleep`, sync HTTP/DB/file IO,
  or CPU-bound work. Wrap unavoidable sync calls in an executor.
- No `asyncio.run()` inside a running loop; the runtime owns the loop.
- Concurrency is explicit: bound fan-out, cancel on first error, and never share
  mutable state across tasks without a lock.
- Background work is owned and observable: tracked task, cancellation path,
  shutdown hook.
- Reconnect loops use bounded exponential backoff with jitter and a clear
  give-up condition.

## SHOULD

- Prefer structured concurrency (`asyncio.TaskGroup`, `anyio`, equivalent).
- Propagate a request/command id through logs, errors, and retries.
- Make retries idempotent or explicitly non-retryable.

## ANTI-PATTERNS

- A timeout with no message or hint.
- Fire-and-forget tasks with no reference (silent failures, lost exceptions).
- Unbounded `gather` over user input.
- Holding a lock across an `await` that performs IO.
- Retrying a non-idempotent write.

## Checklist

- [ ] Every external call has a timeout.
- [ ] No blocking call in async code.
- [ ] Failures surface, never disappear.
- [ ] Shutdown cancels and awaits tasks.
