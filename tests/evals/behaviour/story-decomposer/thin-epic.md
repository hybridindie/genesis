# Case: a thin epic with two stories and no shared contract

## Input

> Epic: add search to the docs site. Users type a query and get results. Should
> be fast and look good. Two stories: one for the index, one for the UI.

## Expected properties

- The output is **not** treated as ready to decompose: the missing acceptance
  criteria are surfaced as a gap, or the skill asks for them.
- No story is invented for work the input never mentions (no auth, no analytics,
  no ranking beyond what "search" implies).
- If stories are produced, each cites an acceptance criterion and names the
  files it owns; the parallelization map declares a shared contract for the
  index/UI boundary rather than leaving both to touch it.
- Anything unresolvable (which search backend, what "fast" means) appears as an
  open question, not as an assumption baked into the artifact.
- Any plan it writes passes `plan.py check`; it reports the check's output
  rather than asserting the plan is valid.
