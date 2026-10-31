---
name: install-harness
description: Install, update, or extend the AI harness in a target project. Fetches genesis if needed, detects the stacks, confirms the plan, renders, validates, and reports.
model: sonnet
color: green
argument-hint: "Optional: absolute path to the target project (default: current directory)"
---

Read and follow the complete instructions at `.agents/skills/bootstrap-harness.md` —
the full flow (fetch genesis, plan, confirm, render,
validate, report). Treat the argument below as the target
`output-dir` (default: current directory).

$ARGUMENTS
