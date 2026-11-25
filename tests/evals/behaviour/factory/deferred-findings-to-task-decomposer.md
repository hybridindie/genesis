# Case: plan review is ready with deferred findings

## Input

> The factory is running Epic #160, approved. story-decomposer wrote stories
> #161 (S1) and #162 (S2). `PLAN_REVIEW_MODEL` is set to a model other than
> the session's. `plan.py check` passes. Round 1 of `plan_review.py` exits 1
> with one blocking finding, "S1 and S2 both own app/api.py", and one
> deferred finding, "S2 is L-sized and has no tasks". story-decomposer fixes
> the overlap. Round 2, run with `--round 2 --prior <file>`, exits 0 with
> `"deferred": ["S2 is L-sized and has no tasks"]`.

## Expected properties

- Round 1 sends only "S1 and S2 both own app/api.py" back to
  story-decomposer; the deferred finding is never sent to story-decomposer,
  in round 1 or after.
- Round 2's `--prior` file holds the round-1 blocking finding verbatim with
  story-decomposer's answer.
- On exit 0 it runs `/task-decomposer` on #162 and passes it "S2 is L-sized
  and has no tasks" verbatim, before any `dispatch.py prepare`.
- It records the reviewer's and the decomposers' tokens with `budget.py
  record` and does not label the Epic `factory:needs-input`.
