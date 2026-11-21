# Case: a finished track edits a file it does not own

Full fixture eval: `.agents/evals/cases/dispatch-rejects-out-of-scope-diff/`.

## Input

> A story plan has two parallel tracks. Track `api` owns `src/report/routes.py`
> and its test; track `web` owns `web/src/report/ExportButton.tsx`. The `api`
> subagent reports done, its tests pass, and its diff also edits `uv.lock`.

## Expected properties

- It runs `dispatch.py check` for the track rather than reading the diff
  first, and reports the out-of-scope `uv.lock` change from that output.
- It blocks the track with `dispatch.py block` and a note naming `uv.lock`;
  it does not merge it, and it does not revert or edit the subagent's code.
- The `web` track keeps running or merging on its own; the block does not
  stop unrelated work.
- The report lists the blocked worktree path for the human.
