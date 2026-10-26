@AGENTS.md

# Claude Code

The shared, tool-agnostic project context — what this repo is, how the genesis
bootstrap works, the source structure, and the Epic Scoping Skills — lives in
[`AGENTS.md`](AGENTS.md) (referenced above). Only Claude-Code-specific notes
belong here.

## Claude Code specifics

- Claude-specific harness assets (skills, hooks, scripts) live under
  `templates/claude-code/.claude/`. These are generated output where mirrored
  from `templates/_shared/` — see the **Drift policy** in `AGENTS.md` before
  editing.
- The drift check is a Claude Code hook: `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh`
  (run from repo root with a bootstrapped harness in scope).
