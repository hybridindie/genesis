# Contributing to the Harness

Editing contract for this repo. Read this when modifying articles, agents,
commands, skills, doctrine, or the bootstrap pipeline. Not auto-loaded into
sessions — open it on demand when editing.

## Design principles

- **Keep always-loaded context lean.** A long `AGENTS.md`/`CLAUDE.md` gets
  skimmed or ignored. Put detail in rules that load on demand (via the rule
  index or `paths:`), and keep status and history out.
- **Three layers, each for its own job.** Rules hold persistent, path-scoped
  guidance. Skills hold procedures, loaded on demand. Hooks and CI are the
  deterministic gates. Anything that must never be skipped belongs in a gate,
  not in prose.
- **Drift is the main maintenance cost.** Generate everything that can be
  generated (OpenCode mirrors, rule index, command and skill lists) and check
  the rest in CI, rather than keeping copies in sync by hand.

## Working on the genesis repo

- **System layer**: edit `system/`. Test with
  `bash system/install.sh --home /tmp/syshome --all --no-tools` then run
  `zsh -n` on the rendered files. Never put machine-specific paths in `system/`;
  they come from `--dev-root` / `--machine-label`.
- **Add a core rule**: add `.md` to `templates/_shared/core/articles/` with `read_when:` frontmatter (required; the AGENTS.md rule index is generated from it) and optional `paths:` for Claude scoping. Re-render to test.
- **Add a stack or pack rule**: add `.md` under `templates/_shared/stacks/<id>/articles/` or `packs/<id>/articles/`. Rule paths must be unique across core, stacks and packs (a collision fails the render). A new stack also needs an entry in `STACKS` in `render.py`, a marker in `check-project-drift.py`, and detection in `inspect-project.py`.
- **Canonical context**: edit `templates/_shared/AGENTS.md`. Keep `templates/claude-code/CLAUDE.md` thin (`@AGENTS.md` + Claude-only notes); never copy the project context into it.
- **Add a new agent**: add `.md` to `templates/_shared/agents/` (every project) or `stacks/<id>/agents/`. The OpenCode mirror is generated.
- **Add an epic-pipeline skill**: create `.agents/skills/<name>/SKILL.md` (frontmatter with `name` and a `description` that includes the trigger phrases, then the body; scripts beside it), run `python3 scripts/sync-skill-wrappers.py` to generate the `.claude/skills` pointer, and it then renders into every project automatically (the list is derived in `scripts/pipeline.py`; add the name to `GENESIS_ONLY` there to keep a skill genesis-only). Never add an `.opencode/skills` copy — OpenCode reads `.agents/skills/`.
- **Add a shipped skill**: add `templates/_shared/skills/<name>/` (or under a stack/pack). It renders once, to `.agents/skills/<name>/`, plus a generated `.claude/skills` pointer; its scripts are called as `.agents/skills/<name>/scripts/...`.
- **Add a new command**: add `.md` to `templates/_shared/commands/` or `stacks/<id>/commands/` / `packs/<id>/commands/`. The mirror and the AGENTS.md command list are generated.
- **Add shared doctrine** (rare — prefer one canonical rule file that others link to): add `.md` to `templates/_shared/doctrine/` and a `doctrine_entries` entry in `mirror-pairs.json`.
- **Skills are deterministic**: every body uses the six sections in `templates/_shared/doctrine/skill-execution.md` — Inputs, Deterministic Steps, LLM Judgment, Output, Stop Conditions, Token Budget. Run `python3 scripts/lint-skills.py` before committing; CI runs it too.
- **Check for drift**: `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh` from the genesis root (or `bash .claude/hooks/check-primitive-drift.sh` in a rendered project), then `python3 templates/scripts/check-harness-sync.py templates <rendered-project>`.
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

The hooks matter only when **editing** this repo — they don't affect using
the skills. Each harness ships a non-blocking "pointer-edit" guardrail that
fires a reminder (warns, never blocks) when you edit:

- a generated `.claude/skills` pointer (edit `.agents/skills/` and regenerate),
  or another `.claude/`/`.opencode/` pointer, instead of the canonical
  `.agents/` content;
- a harness-specific template in `templates/claude-code/` or
  `templates/opencode/` that may belong in `templates/_shared/`;
- a load-bearing `.agents/doctrine/` or `templates/_shared/doctrine/` file —
  both are referenced by path from many skills, rubrics or articles, so edits
  propagate everywhere.

| Harness | File | Event | Output |
|---|---|---|---|
| OpenCode | `.opencode/plugins/warn-pointer-edit.ts` — runs the shell hook below, so the rules exist once | `execute.before` on `edit`/`write` | `console.warn` |
| Claude Code | `.claude/hooks/warn-pointer-edit.sh` | `PreToolUse` (Edit\|Write) | `additionalContext` reminder |

Claude Code also runs an `InstructionsLoaded` hook that logs which instruction
files load (to `.claude/hooks/instructions-loaded.log`); it is for
observability only and safe to remove.
