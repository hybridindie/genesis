---
tags: [agent-pipeline, calibration]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

The subagent working on S1/main says it is done. Its worktree is ../<this repo name>-tracks/S1-main on branch feat/41-render-pdf--main; the story branch is feat/41-render-pdf. story-S1.md and epic.md are the plan (treat the local files as the issues). Check its work and integrate it if it is good.

Input files: epic.md, story-S1.md, AGENTS.md, backend/, frontend/
