# Case: a track that only changes a skill body

## Input

> Story S3, track `doc`, owns `.agents/skills/story-decomposer/SKILL.md` and
> `tests/evals/behaviour/story-decomposer/**`. Its verify is
> `python3 scripts/lint-skills.py`, which already passes. The work adds a rule
> that stories are sized to the PR budget.

## Expected properties

- It does not keep a verify that already passes as the track's only proof:
  the task's verify asserts the new rule, for example
  `grep -q 'Size the story to one PR' .agents/skills/story-decomposer/SKILL.md`.
- It does not count the new behavioural case as a failing test, since cases
  are checked for format only.
- If the change were a pure rewording, it would say so and mark the track
  `verify_baseline: pass` rather than invent an assertion.
- The tasks' files stay inside the track's `owns`, and `plan.py check` passes.
