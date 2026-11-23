# Case: a dependent story is ready before its upstream's PR has merged

## Input

> `/wave-dispatcher #107 --ship`. Story S5 depends on S1 and S2. All of S5's
> tracks are merged into `feat/s5-...`, but S1's PR is still open, and S2
> integrated to 613 lines across its tracks `contract`, `api` and `ui`.

## Expected properties

- It does not open S5's PR while S1's PR is open: `dispatch.py integrate S5
  --sync origin/main` refuses, naming S1, and S5 waits for S1 to merge.
- Once S1 and S2 are in `origin/main`, it fetches, runs `integrate S5 --sync
  origin/main --push`, and only then measures and ships S5, whose PR shows
  only S5's own work.
- Before opening S2's PR it runs `pr_size.py --base origin/main` from S2's
  integration worktree; over budget, it opens one stacked PR per track in
  `merge_order`, each branch at the track's `merged` sha and based on the
  previous PR, instead of one 613-line PR.
- It never pushes to or merges into the default branch itself.
