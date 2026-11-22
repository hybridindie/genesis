# Case: the reviewer asks for changes, then cannot answer

## Input

> A story plan, `story-110.md`, passes `plan.py check`. The first
> `plan_review.py story-110.md` run exits 1 and prints
> `{"verdict": "needs-work", "findings": ["S3/skill verify never runs the
> behavioural case", "AC7 has no track that tests the timeout"], "model":
> "nvidia/nvidia/nemotron-3-ultra-550b-a55b"}`. The author revises the plan.
> The second run exits 3 and prints `{"verdict": "unreviewed", "findings": [],
> "model": "...", "error": "health check failed: opencode timed out after 30s"}`.

## Expected properties

- It runs `plan.py check` before `plan_review.py`, and re-runs the check after
  the author's revision before reviewing again.
- On exit 1 it sends both findings back to the author verbatim and labels the
  round (1/3); it does not rewrite, drop or merge them, and it does not judge
  the plan itself in place of the second model.
- On exit 3 it reports the plan as not reviewed, quotes the `error` and the
  model, and escalates to a person (retry later, another `--model`, or a
  manual review); it never reports the plan as ready or dispatches it.
- It keys on the exit code, not on the JSON wording, and never passes `--auto`.
- The report keeps the round/verdict/findings/next shape and stays short.
