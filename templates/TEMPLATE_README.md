# Template System

How `templates/` produces a project harness. For the product view, see the
top-level [`README.md`](../README.md); for the file tree, see
[`docs/agents-sections/source-structure.md`](../docs/agents-sections/source-structure.md).

## Pipeline

```
templates/_shared/core/articles/          → .claude/rules/        (all profiles)
templates/_shared/profiles/<p>/articles/  → .claude/rules/        (overrides by path)
templates/_shared/AGENTS.md               → AGENTS.md             (rule index filled in)
templates/claude-code/                    → CLAUDE.md, .claude/
templates/opencode/                       → .opencode/            (config)
shared commands/agents/skills + profile    → .claude/* + .opencode/* (mirrored)
shared my-workflows.md                    → my-workflows.md
process-conditionals.py                   → strips profile/feature blocks
```

`generate-rule-index.py` rebuilds the `<!-- RULE_INDEX -->` table in `AGENTS.md`
from each rendered rule's `read_when:` frontmatter. `generate-harness-mirrors.py`
mirrors Claude agents/commands into `.opencode/` (frontmatter adapted, body
identical).

## Profiles

| Profile | Rules added |
|---------|-------------|
| `mcp` | MCP contract, safety, transport, fake-peer testing |
| `python` | CLI behaviour, packaging |
| `agent` | Agent system + ACD workflow |
| `web` | API, database, frontend, auth, operational articles |
| `godot` | Addon lifecycle, serialization, headless testing |

An article with the same relative path in a profile overrides the core one
(e.g. `profiles/web/articles/architecture.md` replaces
`core/articles/architecture.md`).

## Templates

- **Core articles** — `_shared/core/articles/*.md`. Every rule starts with
  `read_when:` (required) and optionally `paths:` (Claude scoping).
- **Profile articles** — `_shared/profiles/<profile>/articles/**`.
- **Agents** — `_shared/agents/*.md` (shared) or `profiles/<p>/agents/*.md`.
  OpenCode mirrors are generated; never edit `.opencode/agents/` by hand.
- **Commands** — same split; body is the prompt, `$ARGUMENTS` is user input.
- **Doctrine** — `_shared/doctrine/*.md`, routed by `mirror-pairs.json` to
  `.claude/rules/doctrine/`; referenced by rules, not indexed.
- **Skills** — `_shared/skills/<name>/SKILL.md` and profile variants; rendered
  into both `.claude/skills/` and `.opencode/skills/`.

.github/ belongs to the project; this repo only keeps its own CI workflow.

## Checks

```bash
for p in mcp python agent web godot; do
  bash templates/scripts/bootstrap.sh --profile "$p" \
    --project-name Test --project-slug test --output-dir "/tmp/render-$p"
  python3 templates/scripts/check-harness-sync.py templates "/tmp/render-$p"
done
```

CI additionally verifies: no orphan placeholders, profile isolation, the rule
index matches the rendered rules, OpenCode mirrors match their Claude sources,
hook syntax, and valid JSON/YAML.
