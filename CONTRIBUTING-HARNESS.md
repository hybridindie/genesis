# Contributing to the Harness

Editing contract for this repo. Read this when modifying articles, agents,
commands, skills, doctrine, or the bootstrap pipeline. Not auto-loaded into
sessions — open it on demand when editing.

## Working on the genesis repo

- **System layer**: edit `system/`. Test with
  `bash system/install.sh --home /tmp/syshome --all --no-tools` then run
  `zsh -n` on the rendered files. Never put machine-specific paths in `system/`;
  they come from `--dev-root` / `--machine-label` / `--wiki-fabric-dir`.
- **Add a new article**: add `.md` to `templates/_shared/articles/`, add an entry in `mirror-pairs.json`, run bootstrap to test.
- **Canonical context**: edit `templates/_shared/AGENTS.md`. Keep `templates/claude-code/CLAUDE.md` thin (`@AGENTS.md` + Claude-only notes); never copy the project context into it.
- **Add a new agent**: add `.md` to `templates/_shared/agents/`, add an `agent_entries` entry in `mirror-pairs.json`.
- **Add a new command**: add `.md` to `templates/_shared/commands/`, add a `command_entries` entry in `mirror-pairs.json`.
- **Add shared doctrine**: add `.md` to `templates/_shared/doctrine/`, add a `doctrine_entries` entry in `mirror-pairs.json` (with `source_file` + `render_dir` = `.claude/rules/doctrine`). Doctrine is referenced by articles/agents, not mirrored to Copilot.
- **Check for drift**: `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh` (must be run from repo root with a bootstrapped harness in scope).
- **Test a bootstrap**: `bash templates/scripts/bootstrap.sh --project-name Test --project-slug test --output-dir /tmp/test-harness`.

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

`templates/_shared/` is the single source. Platform-specific files in `templates/claude-code/.claude/agents/`, `templates/claude-code/.claude/commands/`, and `templates/github-copilot/.github/agents/` + `templates/github-copilot/.github/prompts/` are **generated output** — do not edit them directly. Edit the shared source and re-run bootstrap.

## Hooks

The hooks matter only when **editing** this content — they don't affect using
the skills. Each harness ships a non-blocking "pointer-edit" guardrail that
fires a reminder (warns, never blocks) in three cases: editing a thin wrapper
instead of the canonical `.agents/` content, editing a load-bearing
`.agents/doctrine/` file, and editing a load-bearing
`templates/_shared/doctrine/` file. Both doctrine layers are referenced by
path from multiple skills/rubrics (epic side) or articles/agents (genesis
side), so edits there propagate everywhere. Configs:
`.opencode/plugins/warn-pointer-edit.ts`, `.claude/hooks/warn-pointer-edit.sh`,
`.github/hooks/warn-pointer-edit.json`.