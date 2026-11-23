# Case: a story whose tracks each fit but together exceed the PR budget

## Input

> Epic story S2 adds a dispatch command: a contract track (~120 lines), an
> `api` track (~250 lines with tests) and a `skill` track that only edits
> `.agents/skills/wave-dispatcher/SKILL.md` and adds a behavioural case.

## Expected properties

- It estimates the integrated story, tests included, at about 600 lines and
  says this is over the PR budget (≤ 400 lines, ≤ 25 files); it does not
  leave one story that ships as a single over-budget PR.
- It either splits the story in the Epic plan (re-check, re-scaffold) or sets
  `ship: per-track` on it, and says which and why.
- The `skill` track's verify can fail before the work: a `grep -q` for the
  new behaviour in the skill body, or a lint rule; not only the behavioural
  case, which is checked for format and cannot go red. A pure rewording would
  declare `verify_baseline: pass` instead.
- The plan passes `plan.py check`, and it reports that output.
