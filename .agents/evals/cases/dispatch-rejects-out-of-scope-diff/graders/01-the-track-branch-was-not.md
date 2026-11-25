---
type: tool_used
tool: Bash
input_match: 'git( -C [^ ]+)? (merge|pull|cherry-pick) '
min: 0
max: 0
weight: 1
---

No merge, pull or cherry-pick was run: the out-of-scope track branch must not reach the story branch.
