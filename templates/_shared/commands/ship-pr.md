---
description: Open or update a PR, watch CI and the automated review, address the review, and merge with --merge when green
---

Read and follow the ship-pr skill:

`.agents/skills/ship-pr/SKILL.md` (Claude Code reaches it through the
`.claude/skills/ship-pr` pointer; OpenCode reads it directly).

Arguments: `$ARGUMENTS`

- empty — use the pull request for the current branch
- a PR number or URL — target that PR
- `--merge` — allow merging after the gates pass (default: never merge)
