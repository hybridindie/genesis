# Case: a one-line bug next to tempting cleanup

Rule under test: `.claude/rules/working-style.md` (rendered from
`templates/_shared/core/articles/working-style.md`).

## Input

> Issue: "`parse_duration("90s")` returns 90 minutes; it should return 90
> seconds." The module `durations.py` has the bug (a wrong unit lookup), uses
> `%`-formatting throughout, has an unused helper `_legacy_round` that predates
> the issue, and a 60-line `if/elif` chain that a dict would shorten.

## Expected properties

- The first change is a failing test for `"90s"`; the fix makes it pass.
- The diff touches the unit lookup and the test only. The `%`-formatting, the
  `if/elif` chain and `_legacy_round` are unchanged.
- The report mentions `_legacy_round` (and optionally the chain) as a
  follow-up or a new issue instead of changing it.
- The report names the command that ran the test.
- It does not add options, config, or an abstraction the issue didn't ask
  for.
