# Epic Scoping Skills — Architecture

On-demand section — read when understanding the skill/harness architecture.

Every primitive both harnesses can share lives once, in `.agents/`. Each skill
is a real skill folder — frontmatter, body, and any scripts or references —
at `.agents/skills/<name>/SKILL.md`. OpenCode discovers `.agents/skills/`
natively. Claude Code only reads `.claude/skills/`, so each skill gets a
generated pointer there (`scripts/sync-skill-wrappers.py`; CI fails if one is
stale). Nothing is written twice.

```
.agents/   Shared primitives                               (EDIT HERE)
   ├── skills/<name>/SKILL.md   the skills (epic-*, story/task decomposers,
   │                            plan-reviewer, wave-dispatcher, factory,
   │                            bootstrap-harness)
   ├── doctrine/                shared rules referenced by several skills
   ├── templates/               epic/story/traceability shells
   ├── evals/                   rubrics, plus test cases for the skills
   └── scripts/                 plan.py, dispatch.py, tracker.py, budget.py, ...

.claude/skills/<name>/SKILL.md  generated pointers → .agents/skills/<name>/SKILL.md
.claude/agents/<name>.md        agents (Claude format)
.opencode/agents/<name>.md      generated mirror of .claude/agents (OpenCode has
                                no compatibility path for agents)
.opencode/opencode.json         `commands` give the skills a slash path in OpenCode
.opencode/plugins/*.ts          call the matching .claude/hooks/*.sh, never reimplement
```

| Primitive | One copy at | Claude Code | OpenCode |
|---|---|---|---|
| Skills | `.agents/skills/` | generated pointer in `.claude/skills/` | reads `.agents/skills/` |
| Instructions | `AGENTS.md` | `CLAUDE.md` imports it | reads it |
| Agents | `.claude/agents/` | reads it | generated mirror |
| Hooks | `.claude/hooks/*.sh` | runs it | plugin shells out to it |

Rendered projects use the same layout: `bootstrap.sh` writes skills to
`.agents/skills/` and a pointer to `.claude/skills/`. Every project also gets
the pipeline listed by `scripts/pipeline.py`: every `.agents/skills/` skill
except `bootstrap-harness`, plus `scripts/`, `doctrine/`, `templates/` and the
eval rubrics (not tests, fixtures or eval cases), at the same `.agents/` paths.
Scripts are copied byte for byte. Nothing is installed per user: each repo carries its own copy.

**Golden rule:** Edit content in `.agents/`. Never hand-edit a generated pointer
or mirror; regenerate it.

**Doctrine layer:** `.agents/doctrine/` holds rules shared across multiple
skills and rubrics (acceptance-criteria linting, parallelization, AI-readable
specs, source discipline, review checkpoint, context discovery). Skills
reference these via `Applies .agents/doctrine/<name>.md` instead of restating
the rules; rubrics assess against them. When adding a new skill, check
whether its rules already live in `doctrine/` and reference rather than
restate — this is what prevents the duplication the refactor removed.