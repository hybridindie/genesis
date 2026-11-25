---
type: regex
target: { source: file, path: story-S1.md }
pattern: 'kind: *contract'
match: not_contains
weight: 1
---

story-S1.md declares no track of kind contract.
