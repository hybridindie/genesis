---
name: ship-pr
description: >
  Open or update a pull request, watch CI and the PR-agent review, address the
  review threads, and merge with --merge when the gates are green. Trigger
  words: open a PR, ship this PR, watch the PR, address the review, merge when
  green.
---

Read and follow the canonical skill at `templates/_shared/skills/ship-pr/SKILL.md`
(this repo is the template source; rendered projects get a local copy).

The watcher is at `templates/_shared/skills/ship-pr/scripts/watch_pr.py`.

Arguments: `$ARGUMENTS` (PR number/URL; `--merge` to allow merging).
