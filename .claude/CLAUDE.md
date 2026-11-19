@../AGENTS.md

# Claude Code — Epic Scoping Skills

Skills are in `.claude/skills/<name>/SKILL.md` with Claude Code frontmatter.
Each wrapper references the shared content in `.agents/skills/<name>.md` and
accepts `$ARGUMENTS` for user-provided input. The model reads the `.agents/`
body on demand when a skill is invoked.

Invoke with `/epic-composer`, `/epic-acceptance-linter`, `/epic-interview`,
`/story-decomposer`, `/task-decomposer`, `/bootstrap-harness` or `/ship-pr`, or
let Claude load them when relevant.