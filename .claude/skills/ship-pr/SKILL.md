---
name: ship-pr
description: >
  Open or update a pull request on GitHub or Gitea, watch CI and the automated review,
  address the review threads, and merge once CI is green and every finding is addressed,
  if the repo's merge policy allows it. Trigger phrases: "open a
  PR", "ship this PR", "watch the PR", "address the review", "merge when green", "push
  this and open a PR". Use when the current branch is ready to ship.
---

Read and follow the canonical skill at `templates/_shared/skills/ship-pr/SKILL.md`
(this repo is the template source; rendered projects get a local copy). OpenCode
reads this pointer through its `.claude/skills` compatibility, so there is no
OpenCode copy.

Its scripts are in `templates/_shared/skills/ship-pr/scripts/`.

Arguments: `$ARGUMENTS` (PR number/URL; `--no-merge` to stop before merging).
