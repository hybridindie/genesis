---
tags: [agent-pipeline]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

epic.md is the epic for PDF export and weekly report emails in this repo. Break it into stories I can hand straight to subagents — they will only see their own story, so each one has to stand on its own. Save each as story-<id>.md (e.g. story-S1.md) in the repo root and update epic.md if anything in the plan changes.

Input files: epic.md, AGENTS.md, backend/, frontend/
