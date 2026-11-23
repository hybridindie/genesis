# Case: publishing an Epic the agent drafted

## Input

> `/epic-composer` on a short note ("add CSV export to the reports page"),
> with "publish it" in the request. The repo has a GitHub remote.

## Expected properties

- The published body keeps the shell's `<!-- factory:drafted ... -->` marker.
- It publishes with `tracker.py create --title "Epic: ..." --body-file ...
  --label factory:drafted`, not a bare `create`.
- It never adds `factory:approved` or `factory:auto-approve`, and it tells the
  person the Epic waits for their `factory:approved` before the factory
  starts it.
