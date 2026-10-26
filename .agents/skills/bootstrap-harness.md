# Bootstrap / Install Harness

Fetch (if needed), detect, tailor, and render a complete AI assistant harness
— OpenCode + Claude Code, with core rules plus one archetype profile —
into a target project.

This one flow backs every entry point:

- `/bootstrap-harness` — Claude Code & Opencode slash command (interactive, run from the target project)
- `install-harness` — Claude Code / Copilot agent (same flow, autonomous via @mention)
- `install.sh` — non-interactive shortcut (fetch + auto-detect render, no interview)

The flow: **locate/fetch genesis → identify target → discover stack → review plan
→ render → validate → report.**

---

## Phase 0 — Locate or fetch the genesis repo

You need the genesis template repo available locally. Determine `GENESIS`:

1. If `templates/scripts/bootstrap.sh` exists relative to the current directory,
   you are already inside genesis → set `GENESIS` to the repo root and skip fetching.
2. Otherwise fetch it into a cache directory:

```bash
CACHE="${GENESIS_CACHE:-$HOME/.cache/instructions-and-rules}"
REF="${GENESIS_REF:-main}"
if [ -d "$CACHE/.git" ]; then
  git -C "$CACHE" pull --ff-only --quiet origin "$REF"
else
  git clone --quiet --depth 1 --branch "$REF" \
    https://github.com/hybridindie/instructions-and-rules.git "$CACHE"
fi
GENESIS="$CACHE"
```

The repo is public, so the HTTPS clone needs no authentication. If it fails,
stop and report a network/git problem.

> `install.sh` at the genesis root performs exactly this fetch. If it is already
> on disk you may run `bash "$GENESIS/install.sh" --fetch-only` instead — it
> prints the cache path.

All `templates/…` paths below are relative to `$GENESIS`. Run bootstrap from `$GENESIS`.

> **Command execution:** If your harness runs shell commands directly, execute the
> commands below. If it cannot, show the user each command and wait for the output
> before continuing.

---

## Phase 0.5 — Identify the target project

- `TARGET` = the `output-dir` argument if supplied, else the current directory (`$PWD`).
  When invoked from the project you want to tailor, that is just the current directory.
- Verify it exists (`ls "$TARGET"`); if not, stop.
- Check whether a harness is already installed:

```bash
ls "$TARGET/.claude/rules" "$TARGET/.github/instructions" 2>/dev/null
```

- **Neither exists** → fresh install; continue to Phase 1.
- **Either exists** → update; jump to the [Update path](#update-path) at the end.

---

## Phase 1 — Discovery

Run auto-detect first; use the manual probes only to fill gaps it leaves.

```bash
python3 "$GENESIS/templates/scripts/inspect-project.py" "$TARGET"
```

Parse the JSON and record what it emits: `mode` (full / backend-only / frontend-only),
`profile` (mcp / python / agent / web / godot), `project_name` /
`project_slug`, `python_version`, `react_version`, `typescript_version`, `vite_version`,
`state_manager`, `pkg_manager_backend`, `pkg_manager_frontend`, `has_mlflow`,
`has_langgraph`, `db_extensions`, `ui_library`, `tailwind`, `zod_validation`,
`cicd_platform`, `confidence`. Some keys are conditional — e.g. `fastapi_version`
appears only for FastAPI projects, and frontend keys only when a frontend exists.
Treat any missing key as "let bootstrap use its default."

**Manual fallback probes** (only for anything auto-detect returned empty). Run
silently against `$TARGET`; record findings, don't dump raw output:

- **Name/slug:** `package.json` `.name`, `pyproject.toml` `name`, else the repo basename.
- **Profile:** `project.godot` → godot; `langgraph|mlflow` deps → agent; `package.json` + `pyproject.toml` → web; `fastmcp|mcp` deps → mcp; else python.
- **Backend/Python:** grep `pyproject.toml` / `requirements.txt` for the framework; `python3 --version`.
- **Frontend:** `package.json` for `react`, `typescript`, `vite`.
- **State manager:** grep for `zustand|redux|mobx|recoil|jotai`.
- **Database:** `supabase/config.toml` → supabase; `psycopg|sqlalchemy|prisma` → postgres (warn: SQLAlchemy is discouraged by the template).
- **Package managers:** `uv.lock` → uv; `package-lock.json` → npm; `yarn.lock` → yarn; `pnpm-lock.yaml` → pnpm.
- **Tests:** grep `package.json` and configs for `vitest|jest|playwright|cypress`.
- **UI:** grep for `shadcn|tailwind|mui|antd|chakra`.
- **Special infra:** grep for `mlflow` (→ HAS_MLFLOW=yes), `langgraph|langchain` (→ HAS_LANGGRAPH=yes).
- **Layout:** separate `backend/` + `frontend/` vs a single `src/` (if ambiguous, ask monorepo vs single-stack).

---

## Phase 2 — Plan review + interview

Show a concise discovery summary and the install plan, then ask **only** the
questions the probes could not answer.

```
🔍 Discovery — <TARGET>
Project:  <name> (<slug>)      Profile: <mcp|python|agent|web|godot>
Backend:  <python + framework + pkg mgr>
Frontend: <react/ts/vite + pkg mgr>   (omit if backend-only)
State/DB/Tests/UI/Special: <as detected>

Install plan
  WILL INSTALL:
    ✓ Core rules: architecture, testing, error-handling, security, cicd,
      enforcement, documentation, workflow, async, logging, dependency-security
    ✓ Canonical AGENTS.md with a generated rule index + thin CLAUDE.md
    ✓ Preflight/session commands, article-compliance reviewer, hooks
    [mcp]    ✓ MCP contract, safety, transport, fake-peer tests
    [python] ✓ CLI UX, packaging
    [agent]  ✓ Agent system (graph, prompts, evals) + ACD workflow
    [web]    ✓ API, SQL, frontend, auth + operational articles
    [godot]  ✓ Addon lifecycle, serialization, headless tests
  WILL OMIT:
    ✗ GitHub Copilot harness (removed)
    ✗ Every other profile's rules, commands, agents and skills

❓ Unresolved (ask only what applies)
  1. Project domain? (e.g. "SaaS analytics", "e-commerce")
  2. Custom compliance rules? (GDPR, HIPAA, SOC2, …)
  3. Confirm coverage tiers (defaults: security-critical 90 / business 70 / AI-ML 50)
```

Ask: "Proceed with this plan? Reply yes, or describe any changes."
If the user requests changes (e.g. "also skip MLflow"), adjust the flags before rendering.
If the user says "just use defaults," skip the questions and render immediately.

---

## Phase 3 — Render

```bash
bash "$GENESIS/templates/scripts/bootstrap.sh" \
  --auto-detect \
  --output-dir "$TARGET" \
  [+ any flag overrides from Phase 2]
```

`--auto-detect` re-runs inspection against `$TARGET`; layer the interview answers
on top as explicit flags (`--has-mlflow`, `--custom-instructions`, `--mode`, …).
Omit any flag you have no value for — the script falls back to its defaults.
Capture stdout; if the exit code is non-zero, show the error and stop.

The script performs placeholder substitution, then runs `process-conditionals.py`
to strip `{{#FLAG}}…{{/FLAG}}` blocks when a flag is `no`.

---

## Phase 4 — Validation

```bash
# 1. Zero orphaned placeholders (must print 0)
grep -ro '{{[A-Z_]*}}' "$TARGET" | wc -l
# 2. Copilot mirrors present with frontmatter
python3 "$GENESIS/templates/scripts/generate-copilot-mirrors.py" "$TARGET"
# 3. Hooks parse without syntax errors
find "$TARGET/.claude/hooks" -name '*.sh' -exec bash -n {} \;
# 4. Key files present
test -f "$TARGET/CLAUDE.md" && test -f "$TARGET/AGENTS.md" \
  && test -f "$TARGET/.github/copilot-instructions.md" \
  && test -d "$TARGET/.claude/rules/backend" && test -d "$TARGET/.opencode/skills"
```

If placeholders remain, list the files and missing substitutions — that is a bug
in this skill or a template, not user error.

---

## Phase 4.5 — Harness Evaluation (semantic trim + gap detection)

The render is deterministic — it substitutes placeholders and adds the selected
profile's rules, but cannot read the project's actual code. A `harness-eval` command
ships into `$TARGET` (at `.claude/commands/harness-eval.md`), backed by the
evaluation prompt at `$TARGET/docs/harness-eval.md`.

- Load and run the **`harness-eval`** command against `$TARGET`. It reads the
  project's actual code, evaluates whether each rendered rule fits the stack,
  trims rules that don't apply, and suggests rules the project needs but
  doesn't have.
- Always show the evaluation report and get confirmation before any files are
  trimmed.
- This runs **before** `customize-harness` (Phase 5) because trimming and
  gap-filling should happen before domain tailoring.

If the user skipped the interactive interview (e.g. `install.sh --no-interview`),
skip this phase too — they can run `/harness-eval` manually later.

## Phase 5 — Customize (tailor to the project + the user's workflows)

The render produces a generic harness. Now tailor it. The bootstrap ships a
`customize-harness` skill and an editable `my-workflows.md` into `$TARGET`, so:

- Load and run the **`customize-harness`** skill against `$TARGET` (it is now at
  `$TARGET/.claude/skills/customize-harness/`). It rewrites example names to the
  project's domain, adjusts coverage tiers, and weaves the conventions from
  `$TARGET/my-workflows.md` into `CLAUDE.md` / `AGENTS.md` / rules.
- Always show its plan and get confirmation before it edits.
- If `$TARGET/my-workflows.md` is unfilled (all placeholders), it skips the
  workflow-weaving and just does domain tailoring — tell the user they can fill
  it in and re-run `/customize-harness` anytime.

This is the same skill the project keeps for repeatable re-tailoring — running it
here is simply its first pass.

---

## Phase 6 — Report

```
✅ Harness installed in: <TARGET>

Created:
  CLAUDE.md, AGENTS.md
  .claude/rules/ (<N>), .claude/agents/ (<N>), .claude/commands/ (<N>)
  .github/instructions/ (<N>), .github/agents/ (<N>), .github/prompts/ (<N>), copilot-instructions.md
  .opencode/skills/ (<N>)
  docs/harness-eval.md (evaluation prompt for /harness-eval)

Next steps:
  1. cd <TARGET>
  2. Fill in my-workflows.md with your conventions, then re-run /customize-harness
  3. Review CLAUDE.md — confirm the domain tailoring and any placeholder values
  4. Run: bash .claude/hooks/check-primitive-drift.sh
  5. Commit: git add . && git commit -m "chore: install AI harness"
  6. Re-run /harness-eval after major stack changes to re-trim and detect gaps
```

---

## Update path

Used when a harness already exists in `$TARGET`.

**U1 — Show current state**

```bash
ls "$TARGET/.claude/rules/" "$TARGET/.claude/agents/" "$TARGET/.claude/commands/"
```

Report the current rule/agent/command counts.

**U2 — Show what will change**

Run Phase 1 auto-detect and compare. Report:

```
Update plan:
  ~ <N> rule files refreshed from source
  ~ <N> agents regenerated
  ~ <N> commands regenerated
  ~ Copilot mirrors (.github/instructions/, agents/, prompts/) regenerated
  ! Any manual edits to generated files will be overwritten
```

Warn if the user customized placeholder values:
> "Update replaces ALL generated files. Placeholder values in CLAUDE.md will be
> overwritten. Back up local customizations first."

**U3 — Confirm and run**

Ask "Proceed with update? Reply yes." On confirmation, render exactly as in Phase 3,
then report as in Phase 5 with the header `Harness updated in: <TARGET>`.

---

## Rules & constraints

- **Never overwrite existing files** in `$TARGET` without confirmation — show a diff first.
- **Do NOT modify anything in `$GENESIS/templates/`** during an install or update.
- **Do NOT run bootstrap** if `$TARGET` does not exist.
- **Never skip the plan review** (Phase 2 or U2) — always show it before rendering.
- **Use defaults** for anything left blank; the defaults target a TS/React + Python/FastAPI + Supabase + Zustand stack.
- **Be concise** in the interview — ask only genuinely ambiguous questions.
