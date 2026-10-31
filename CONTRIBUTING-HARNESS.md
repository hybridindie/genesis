# Contributing to the Harness

Editing contract for this repo. Read this when modifying articles, agents,
commands, skills, doctrine, or the bootstrap pipeline. Not auto-loaded into
sessions — open it on demand when editing.

## Working on the genesis repo

- **System layer**: edit `system/`. Test with
  `bash system/install.sh --home /tmp/syshome --all --no-tools` then run
  `zsh -n` on the rendered files. Never put machine-specific paths in `system/`;
  they come from `--dev-root` / `--machine-label`.
- **Add a core rule**: add `.md` to `templates/_shared/core/articles/` with `read_when:` frontmatter (required; the AGENTS.md rule index is generated from it) and optional `paths:` for Claude scoping. Re-render to test.
- **Add a stack or pack rule**: add `.md` under `templates/_shared/stacks/<id>/articles/` or `packs/<id>/articles/`. Rule paths must be unique across core, stacks and packs (a collision fails the render). A new stack also needs an entry in `STACKS` in `render.py`, a marker in `check-project-drift.py`, and detection in `inspect-project.py`.
- **Canonical context**: edit `templates/_shared/AGENTS.md`. Keep `templates/claude-code/CLAUDE.md` thin (`@AGENTS.md` + Claude-only notes); never copy the project context into it.
- **Add a new agent**: add `.md` to `templates/_shared/agents/` (every project) or `stacks/<id>/agents/`. The OpenCode mirror is generated.
- **Add a new command**: add `.md` to `templates/_shared/commands/` or `stacks/<id>/commands/` / `packs/<id>/commands/`. The mirror and the AGENTS.md command list are generated.
- **Add shared doctrine** (rare — prefer one canonical rule file that others link to): add `.md` to `templates/_shared/doctrine/` and a `doctrine_entries` entry in `mirror-pairs.json`.
- **Skills are deterministic**: every body uses the six sections in `templates/_shared/doctrine/skill-execution.md` — Inputs, Deterministic Steps, LLM Judgment, Output, Stop Conditions, Token Budget. Run `python3 scripts/lint-skills.py` before committing; CI runs it too.
- **Check for drift**: `bash .claude/hooks/check-primitive-drift.sh` in a rendered project (or run the cross-harness checker from the repo), then `python3 templates/scripts/check-harness-sync.py templates <rendered-project>`.
- **Test a render**: `python3 templates/scripts/render.py --output-dir /tmp/test-harness --project-name Test --stacks mcp,godot-addon --packs production`.

## Versioning

Epic-scoping files under `.agents/` carry a `version: x.y.z` field in their
header comment. Policy:

- **Patch** (`x.y.z` → `x.y.(z+1)`): typo, wording, or formatting fixes that do
  not change behavior.
- **Minor** (`x.y.z` → `x.(y+1).0`): content additions or behavioral changes
  (new phase, new rule, new response state, a doctrine reference added/removed).
- **Major** (`x.y.z` → `(x+1).0.0`): a workflow restructure that breaks
  existing handoffs or response-state contracts.

Each file versions independently. The `doctrine/` files and the `skills/`
files are versioned separately — bumping a skill does not require bumping
the doctrine it references, and vice versa. The header `invokes:` and
`doctrine:` lists are metadata for humans; they are not parsed.

## Drift policy

`templates/_shared/` is the single source. The OpenCode agents and commands are generated from their Claude counterparts by `generate-harness-mirrors.py` — do not edit `.opencode/agents/` or `.opencode/commands/` directly in a rendered project without updating the shared source.

## Hooks

The hooks matter only when **editing** this content — they don't affect using
the skills. Each harness ships a non-blocking "pointer-edit" guardrail that
fires a reminder (warns, never blocks) in three cases: editing a thin wrapper
instead of the canonical `.agents/` content, editing a load-bearing
`.agents/doctrine/` file, and editing a load-bearing
`templates/_shared/doctrine/` file. Both doctrine layers are referenced by
path from multiple skills/rubrics (epic side) or articles/agents (genesis
side), so edits there propagate everywhere. Configs:
`.opencode/plugins/warn-pointer-edit.ts`, `.claude/hooks/warn-pointer-edit.sh`.