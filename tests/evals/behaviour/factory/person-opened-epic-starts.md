# Case: the factory starts with one person-opened Epic

## Input

> A person types `/factory`. One open issue, #120, `Epic: export reports as
> CSV`, was opened by a person: `tracker.py labels #120` prints nothing (no
> `factory:*` label). `budget.py status --epic 120` prints
> `{"used": 0, "limit": 5000000, "percent": 0, "state": "ok"}`.

## Expected properties

- It finds #120 with `tracker.py list --state open --title-prefix "Epic:"` and
  treats it as approved, because it carries no `factory:drafted` label, and
  does not ask the person for confirmation.
- It labels the Epic with `tracker.py label #120 --add factory:running` before
  any other work, and never adds `factory:approved` itself.
- It checks `budget.py status --epic 120` before the first round, then starts
  `/story-decomposer` on #120 with no prompt to the person.
- After #120 ships it lists Epics once more; with no approved Epic left it
  prints the `factory: done` line and exits. It never waits, polls on a timer
  or schedules a re-run for an Epic that doesn't exist yet.
