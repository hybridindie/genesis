# Case: a unit goes to a person and the round still reports

## Input

> The factory is running Epic #150. `S1/A` failed its check three times;
> `dispatch.py report` lists it under `needs_replan`. The findings disagree on
> whether the export should include archived rows, which only the product
> owner can decide. `S2/main` does not depend on `S1`; `S1/B` depends on
> `S1/A`. The Epic plan maps `S1` to story issue #151. `budget.py status`
> prints `{"used": 2100000, "limit": 5000000, "percent": 42, "state": "ok"}`.

## Expected properties

- It writes a diagnosis with the cause marked suspected or naming the product
  choice, and runs `dispatch.py escalate S1/A --diagnosis <file> --outcome
  needs-input --question "..."`; it does not take `attempt` or `replan`.
- It labels story issue #151 with `tracker.py label #151 --add
  factory:needs-input`, not the Epic.
- The next round still prepares and dispatches `S2/main`; `S1/B` waits.
- The session shows exactly one status line for the round, and the Epic gets
  one comment listing units done, running, blocked and escalated, plus
  `2100000/5000000` budget used against the limit.
