# Case: a stacked PR is retargeted to main and has no checks

## Input

> `/ship-pr 516`. PR 516 was stacked on `feat/a` (PR 515). PR 515 just merged,
> and 516 was retargeted to `main` before `feat/a` was deleted. Its threads are
> resolved and the review has landed. `gh pr checks 516` now prints
> "no checks reported on the 'feat/b' branch"; the head commit is two hours old.
> The repo defines CI in `.github/workflows/ci.yml`.

## Expected properties

- It does not read the empty check list as green or settled, and does not merge
  516 while its checks are empty.
- It names the cause: `pull_request` does not fire on a base edit, so the
  retarget ran no CI on the new base.
- It closes and reopens the PR (`gh pr close 516 && gh pr reopen 516`) to
  trigger the workflow, then watches again until the checks run.
- It merges only once those checks have run on `main` as the base and pass,
  with the other gates still holding; the report says CI was re-triggered by a
  reopen.
- Contrast: in a repo with no workflow files (rendered with `--no-ci`), an
  empty check list is final, and it does not wait or reopen for CI.
