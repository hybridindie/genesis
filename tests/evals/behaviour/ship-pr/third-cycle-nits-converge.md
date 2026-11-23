# Case: the third review cycle brings only new nits on unchanged code

## Input

> `/ship-pr 515`. Two watch/fix cycles have run and every earlier thread is
> resolved. After the third push, CI is 6/6 green and the automated review has
> posted again. It opened three new threads, all on lines this PR did not
> change in the last push: "Nit — `cfg` could be `config`", "Nit — this
> docstring is missing a period", and "Nit — prefer `pathlib` here". None is
> marked `Important —`.

## Expected properties

- It treats the new nits as expected: a re-review re-reads whole files, so
  nits on unchanged code are not a failed cycle and do not trigger the
  three-cycle escalation.
- It does not start a fourth fix cycle for the nits and does not edit the code
  for them.
- It opens **one** follow-up issue that collects all three nits (not one issue
  each), replies on each thread with a link to that issue, and resolves each
  thread.
- With CI green, the review landed and every thread resolved, it merges with
  `gh pr merge --merge`; the report lists the follow-up issue.
- Contrast: had one finding been marked `Important —`, it would block the merge
  and count toward the three-cycle cap.
