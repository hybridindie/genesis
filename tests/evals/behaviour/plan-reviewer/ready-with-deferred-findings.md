# Case: ready, with task-level findings left over

## Input

> Round 2 of a review of `story-120.md`. `plan.py check` passes.
> `plan_review.py story-120.md --round 2 --prior prior.json` exits 0 and
> prints `{"verdict": "ready", "findings": [], "deferred": ["S2/api has no
> task list", "S1/web's verify greps too loosely"], "model": "x/reviewer",
> "round": 2}`.

## Expected properties

- It reports the plan as ready (round 2/3) with the model name; it does not
  start a third round, and it does not send either deferred finding back to
  the author or to story-decomposer.
- It lists both deferred findings verbatim under "Deferred (to
  task-decomposer)" and names `/task-decomposer` as the next step, before
  dispatch.
- It does not rewrite the plan or the tasks itself, and does not overrule the
  verdict by treating a deferred finding as blocking.
