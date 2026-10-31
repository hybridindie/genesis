---
name: bootstrap-harness
description: >
  Install, update, or extend the AI harness (OpenCode + Claude Code) in a
  project: core rules plus every detected stack (python, mcp, agent, fastapi,
  frontend, godot, godot-addon, rust) and opt-in packs (production, acd).
when_to_use: >
  Trigger phrases: "bootstrap harness", "generate harness", "install harness",
  "scaffold AI rules", "set up Claude and Opencode rules", "add the rust stack",
  "add the production pack", "update the harness". Use when the user wants to
  install, update, or extend the harness in a target project.
---

Read and follow the complete instructions at `.agents/skills/bootstrap-harness.md` —
all five phases (discovery, interview, render, validation, report) and the rules.

Render the harness into the following output directory (default: current directory):

$ARGUMENTS
