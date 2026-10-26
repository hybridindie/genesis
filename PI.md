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
