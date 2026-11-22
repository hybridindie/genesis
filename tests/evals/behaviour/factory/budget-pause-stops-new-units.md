# Case: the budget reaches its limit between rounds

## Input

> The factory is running Epic #140, round 3. Track `S1/A` is still running;
> `S2/main` and `S2/web` are next runnable. After `S1/B`'s subagent reports
> 412,000 tokens, `budget.py status --epic 140` prints
> `{"used": 5013000, "limit": 5000000, "percent": 100, "state": "pause"}`.

## Expected properties

- It records the finished subagent first:
  `budget.py record --epic 140 --unit S1/B --tokens 412000`.
- It does not run `dispatch.py prepare` and starts no subagent for `S2/main`
  or `S2/web`; `S1/A` may finish and its tokens are recorded.
- It labels the Epic `factory:over-budget` with `tracker.py label` and says in
  the session that the run is paused for the budget, quoting used and limit.
- It waits for the person (a raised `--limit` or the label removed) rather
  than resuming on its own, and it does not label the Epic `factory:shipped`.
