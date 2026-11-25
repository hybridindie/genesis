---
type: regex
target: { source: file, path: epic.md }
pattern: "^```yaml agent-plan"
flags: m
match: "count:1"
weight: 1
---

epic.md contains exactly one fenced `yaml agent-plan` block.
