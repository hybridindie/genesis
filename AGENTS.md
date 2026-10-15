# AI Harness Template Repository

This is the **genesis repository**. It generates AI assistant harnesses for
`.claude/`, `.github/`, and `.opencode/` from a single set of shared
constitutional articles. It also hosts the **Epic Scoping Skills** as its own
installed harness.

## Architecture (summary)

Two systems share the same single-source/thin-wrapper pattern:

- **Genesis harness**: `templates/_shared/` → rendered into target projects by `bootstrap.sh`. Constitutional articles, agents, commands, doctrine, and shippable skills.
- **Epic Scoping Skills**: `.agents/` → thin wrappers in `.claude/`, `.opencode/`, `.github/`. Skills, doctrine, templates, evals.

**Golden rule:** Edit content in `.agents/` (epic skills) or `templates/_shared/` (genesis). Edit frontmatter in the harness wrappers. Never duplicate content into a wrapper. Shared rules referenced by multiple files live in a `doctrine/` layer — reference, don't restate.

## On-demand reference sections

Read these when you need the detail — they are not auto-loaded:

| Section | File | Read when |
|---|---|---|
| What it does / Install / Key flags | [`docs/agents-sections/genesis-overview.md`](docs/agents-sections/genesis-overview.md) | Installing or bootstrapping a harness |
| Source structure (file tree) | [`docs/agents-sections/source-structure.md`](docs/agents-sections/source-structure.md) | Editing the genesis repo structure |
| Epic skills architecture | [`docs/agents-sections/architecture.md`](docs/agents-sections/architecture.md) | Understanding the `.agents/` layout |
| Workflow (pipeline diagram) | [`docs/agents-sections/workflow.md`](docs/agents-sections/workflow.md) | Running the epic → story → task pipeline |
| Skills, templates, evals, doctrine, wrappers, response states | [`docs/agents-sections/skills-and-references.md`](docs/agents-sections/skills-and-references.md) | Invoking a skill or checking references |
| Full usage guide | [`prompts-skills.md`](prompts-skills.md) | Per-harness setup, hooks table, worked examples |
| Editing contract (versioning, drift, hooks) | [`CONTRIBUTING-HARNESS.md`](CONTRIBUTING-HARNESS.md) | Editing this repo |

## Skills at a glance

| Skill | Invoke | Shared content |
|---|---|---|
| epic-composer | `/epic-composer` | `.agents/skills/epic-composer.md` |
| epic-interview | `/epic-interview` | `.agents/skills/epic-interview.md` |
| epic-acceptance-linter | `/epic-acceptance-linter` | `.agents/skills/epic-acceptance-linter.md` |
| story-decomposer | `/story-decomposer` | `.agents/skills/story-decomposer.md` |
| task-decomposer | `/task-decomposer` | `.agents/skills/task-decomposer.md` |
| bootstrap-harness | `/bootstrap-harness` | `.agents/skills/bootstrap-harness.md` |

Post-bootstrap flow: `bootstrap.sh` (render) → `/harness-eval` (trim + suggest)
→ `/customize-harness` (domain tailoring). The harness-eval prompt lives at
[`docs/harness-eval.md`](docs/harness-eval.md).

Each skill wrapper is a thin pointer; the model reads the `.agents/` body
on-demand when the skill is invoked. Doctrine files (`.agents/doctrine/`) are
read on-demand when a skill references them.

## wiki-fabric (claude)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace). It costs you 0 tokens to read and saves you exploration — every rule below is about doing LESS work, not more.

While coding:
- **Knowledge first, once.** If a `# Context Manifest` is already in your context, use it — do NOT run `wf context` again. Otherwise run `wf context --task "<task>"` once, before exploring. The delivered knowledge is BINDING: follow it and cite the `[[id]]` you relied on. A `where:` line under an item is the code location — open that file directly instead of searching for it.
- For a "why / what was decided / what broke before" question, `wf query "<question>"` answers from recorded evidence (0 tokens) — use it instead of grepping history.
- **At most one log call, at the very end, only for a non-trivial lesson** (a surprise, a gotcha, a rejected approach — not a routine change): `wf log --project <slug> --problem "<one sentence>" --intervention "<one sentence>"`. It is a single non-interactive command; never pipe input into it, and skip it entirely for routine work.

Do NOT run fabric maintenance during a coding task (`wf inbox`, `wf lint`, `wf status`, `wf ingest`, `wf promote`, `wf review`) unless the user asks you to work on the fabric itself — those are human-review workflows (`wf skill --list` describes them when needed).

CLI: `wf help` | With graphify installed: graphify owns code-symbol/call-graph questions; the fabric owns recorded knowledge (decisions, gotchas, history).
<!-- /wiki-fabric:claude -->

## wiki-fabric (opencode)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace). It costs you 0 tokens to read and saves you exploration — every rule below is about doing LESS work, not more.

While coding:
- **Knowledge first, once.** If a `# Context Manifest` is already in your context, use it — do NOT run `wf context` again. Otherwise run `wf context --task "<task>"` once, before exploring. The delivered knowledge is BINDING: follow it and cite the `[[id]]` you relied on. A `where:` line under an item is the code location — open that file directly instead of searching for it.
- For a "why / what was decided / what broke before" question, `wf query "<question>"` answers from recorded evidence (0 tokens) — use it instead of grepping history.
- **At most one log call, at the very end, only for a non-trivial lesson** (a surprise, a gotcha, a rejected approach — not a routine change): `wf log --project <slug> --problem "<one sentence>" --intervention "<one sentence>"`. It is a single non-interactive command; never pipe input into it, and skip it entirely for routine work.

Do NOT run fabric maintenance during a coding task (`wf inbox`, `wf lint`, `wf status`, `wf ingest`, `wf promote`, `wf review`) unless the user asks you to work on the fabric itself — those are human-review workflows (`wf skill --list` describes them when needed).

CLI: `wf help` | With graphify installed: graphify owns code-symbol/call-graph questions; the fabric owns recorded knowledge (decisions, gotchas, history).
<!-- /wiki-fabric:opencode -->

## wiki-fabric (codex)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace). It costs you 0 tokens to read and saves you exploration — every rule below is about doing LESS work, not more.

While coding:
- **Knowledge first, once.** If a `# Context Manifest` is already in your context, use it — do NOT run `wf context` again. Otherwise run `wf context --task "<task>"` once, before exploring. The delivered knowledge is BINDING: follow it and cite the `[[id]]` you relied on. A `where:` line under an item is the code location — open that file directly instead of searching for it.
- For a "why / what was decided / what broke before" question, `wf query "<question>"` answers from recorded evidence (0 tokens) — use it instead of grepping history.
- **At most one log call, at the very end, only for a non-trivial lesson** (a surprise, a gotcha, a rejected approach — not a routine change): `wf log --project <slug> --problem "<one sentence>" --intervention "<one sentence>"`. It is a single non-interactive command; never pipe input into it, and skip it entirely for routine work.

Do NOT run fabric maintenance during a coding task (`wf inbox`, `wf lint`, `wf status`, `wf ingest`, `wf promote`, `wf review`) unless the user asks you to work on the fabric itself — those are human-review workflows (`wf skill --list` describes them when needed).

CLI: `wf help` | With graphify installed: graphify owns code-symbol/call-graph questions; the fabric owns recorded knowledge (decisions, gotchas, history).
<!-- /wiki-fabric:codex -->

## wiki-fabric (pi)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace). It costs you 0 tokens to read and saves you exploration — every rule below is about doing LESS work, not more.

While coding:
- **Knowledge first, once.** If a `# Context Manifest` is already in your context, use it — do NOT run `wf context` again. Otherwise run `wf context --task "<task>"` once, before exploring. The delivered knowledge is BINDING: follow it and cite the `[[id]]` you relied on. A `where:` line under an item is the code location — open that file directly instead of searching for it.
- For a "why / what was decided / what broke before" question, `wf query "<question>"` answers from recorded evidence (0 tokens) — use it instead of grepping history.
- **At most one log call, at the very end, only for a non-trivial lesson** (a surprise, a gotcha, a rejected approach — not a routine change): `wf log --project <slug> --problem "<one sentence>" --intervention "<one sentence>"`. It is a single non-interactive command; never pipe input into it, and skip it entirely for routine work.

Do NOT run fabric maintenance during a coding task (`wf inbox`, `wf lint`, `wf status`, `wf ingest`, `wf promote`, `wf review`) unless the user asks you to work on the fabric itself — those are human-review workflows (`wf skill --list` describes them when needed).

CLI: `wf help` | With graphify installed: graphify owns code-symbol/call-graph questions; the fabric owns recorded knowledge (decisions, gotchas, history).
<!-- /wiki-fabric:pi -->
