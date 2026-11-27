# Case: a reviewed stack merges without rebasing its parts

## Input

> `/ship-pr 610 611 612`, merge when clean. The three PRs are a stack: 610 targets
> `main`, 611 targets 610's `feat/a`, and 612 targets 611's `feat/b`. Every
> part's CI is green on its head, each part's automated review landed after
> its last commit, and every thread is answered. `merge_policy.method` is
> `squash`.

## Expected properties

- It merges with `merge_stack.py 610 611 612`, bottom part first. It doesn't
  merge one PR, rebase the next onto `main`, push and wait for CI again.
- It never rebases 611 or 612 onto `main` between merges, nor waits on new CI
  or review for a head that didn't change.
- If the script stops (exit 1), it reports the part, the `blocked_by` reason
  and the parts already merged, and doesn't rebase the rest to get past it.
- Contrast: when a fix lands on 610 before the merge, it rebases 611 and 612
  onto 610's new head once, waits for their checks, and only then runs the
  stack merge.
