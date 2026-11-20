---
tags: [agent-pipeline]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We had a planning call about adding PDF export and scheduled emails to this reports app — my notes are in notes.md. Can you write up an epic for it? I want to hand the work to several agents at once, so it has to be clear which pieces can run in parallel and what each one is allowed to touch. Save it as epic.md in the repo root.

Input files: notes.md, AGENTS.md, backend/, frontend/
