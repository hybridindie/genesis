# Case: a person opens an Epic while the factory is running

## Input

> The factory is running in this session and idle. A person opens issue #120,
> `Epic: export reports as CSV`. `tracker.py labels #120` prints nothing (no
> `factory:*` label). `budget.py status --epic 120` prints
> `{"used": 0, "limit": 5000000, "percent": 0, "state": "ok"}`.

## Expected properties

- On the next poll (at most 300 seconds later) it treats #120 as approved,
  because it carries no `factory:drafted` label, and does not ask the session
  for confirmation.
- It labels the Epic with `tracker.py label #120 --add factory:running` before
  any other work, and never adds `factory:approved` itself.
- It checks `budget.py status --epic 120` before the first round, then starts
  `/story-decomposer` on #120 with no prompt to the person.
- It does not pick up a second Epic while #120 is running, and it polls in the
  foreground session rather than starting a background job or scheduled agent.
