---
name: bootstrap-harness
description: >
  Scan a project, interview the user about unknowns, and generate a complete
  AI harness (OpenCode + Claude Code) with core rules and one archetype profile.
  Trigger words: bootstrap harness, generate harness, install harness, scaffold
  AI rules, set up Claude and Opencode rules, tailor this repo for my project.
when_to_use: >
  Trigger phrases: "bootstrap harness", "generate harness", "install harness",
  "scaffold AI rules", "set up Claude and Opencode rules", "tailor this repo
  for my project". Use when the user wants to install or tailor an AI harness
  into a target project.
---

Read and follow the complete instructions at `.agents/skills/bootstrap-harness.md` —
all five phases (discovery, interview, render, validation, report) and the rules.

Render the harness into the following output directory (default: current directory):

$ARGUMENTS
