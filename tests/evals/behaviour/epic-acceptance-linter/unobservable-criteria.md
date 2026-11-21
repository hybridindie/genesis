# Case: criteria that cannot be checked

## Input

> Acceptance criteria:
> 1. The dashboard should be intuitive and fast.
> 2. Export works for all formats and handles large datasets without problems.
> 3. We should add a tooltip somewhere helpful.
> 4. As discussed.

## Expected properties

- Each criterion is judged on **observability and testability**, with a concrete
  rewrite offered (e.g. "a first-time user completes the export flow in under
  90 s without documentation").
- Compound criteria (#2: formats *and* size) are flagged as needing a split;
  vague quantifiers ("fast", "large") are named as the defect.
- #4 ("As discussed") is called out as having no content at all.
- The report does **not** invent project conventions it cannot know (no specific
  latency target without asking), and says which rewrites need the owner's input.
- Output keeps the Strong / Gaps shape and stays short — no essay per criterion.
