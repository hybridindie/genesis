# Epic Scoping Skills — Architecture

On-demand section — read when understanding the skill/harness architecture.

Shared content lives in `.agents/` as plain markdown — no frontmatter, no
harness-specific fields. Each harness has its own thin wrapper files with
only the frontmatter that harness recognizes. The wrappers reference the
shared content by path.

```
.agents/   Shared content — skills, doctrine, templates, evals   (EDIT HERE)
   │  ├── skills/     epic-* skills + bootstrap-harness (the harness install/tailor flow)
   │  ├── doctrine/   shared rules referenced by multiple skills and rubrics
   │  │               (acceptance-criteria, parallelization, AI-readable specs,
   │  │                source discipline, review checkpoint, context discovery)
   │  ├── templates/  epic/story/traceability shells
   │  └── evals/      readiness rubrics
   │
   │  wrapped by thin, frontmatter-only pointers per harness:
   ├── Opencode        .opencode/skills/<name>/SKILL.md   + opencode.json commands
   └── Claude Code     .claude/skills/<name>/SKILL.md     (skills double as /commands)
                       .claude/agents/<name>.md           (agents point at the same bodies)
```

Both the epic-scoping skills **and** the genesis meta-flow follow this rule.
`bootstrap-harness` is the single canonical body for installing/tailoring a
harness; the `install-harness` agent (Claude Code) is just another
thin entry point pointing at that same file. Only genesis template *output*
(the rendered `.claude/rules/` and `.opencode/` files) is exempt — that is
deduped by `templates/_shared/`, not `.agents/`.

**Golden rule:** Edit content in `.agents/`. Edit frontmatter in the harness
wrappers. Never duplicate content into a wrapper.

**Doctrine layer:** `.agents/doctrine/` holds rules shared across multiple
skills and rubrics (acceptance-criteria linting, parallelization, AI-readable
specs, source discipline, review checkpoint, context discovery). Skills
reference these via `Applies .agents/doctrine/<name>.md` instead of restating
the rules; rubrics assess against them. When adding a new skill, check
whether its rules already live in `doctrine/` and reference rather than
restate — this is what prevents the duplication the refactor removed.