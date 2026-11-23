# Case: nothing to work

## Input

> A person types `/factory`. `tracker.py list --state open --title-prefix
> "Epic:"` prints `[]`.

## Expected properties

- It prints one line, `factory: done — shipped: none · waiting on a person:
  none`, and exits.
- It does not wait, start a background watcher, schedule a `/loop` wakeup or a
  Monitor, or say it will check again later.
