@../AGENTS.md

# Claude Code — Epic Scoping Skills

Each skill lives once, at `.agents/skills/<name>/SKILL.md`. Claude Code reads
the generated pointer in `.claude/skills/<name>/SKILL.md`, which loads that
file and passes `$ARGUMENTS`. Edit the skill in `.agents/`, then run
`python3 scripts/sync-skill-wrappers.py`; never edit a pointer.

Invoke with `/epic-composer`, `/epic-acceptance-linter`, `/epic-interview`,
`/story-decomposer`, `/task-decomposer`, `/bootstrap-harness` or `/ship-pr`, or let Claude load them when relevant.
