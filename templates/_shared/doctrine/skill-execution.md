# Deterministic Skill Execution

Repeatability and token cost are part of correctness. Every skill does the
mechanical work deterministically and reserves the model for synthesis,
planning, and semantic judgment.

## Execution order

1. **Resolve inputs.** Use the arguments, paths, and commands named by the skill.
   Do not guess a path or ask for something a probe can answer.
2. **Read narrowly.** Open only the files listed under `Inputs`; use the named
   `rg` patterns instead of listing or reading a directory.
3. **Run the mechanical steps.** Execute the fixed commands in order. Scripts,
   templates, and checks own discovery, scaffolding, parsing, and validation.
4. **Use the LLM zone.** Only after the deterministic inputs are assembled:
   synthesize, resolve ambiguity, choose trade-offs, plan, and review meaning.
5. **Validate before emitting.** Run the skill's validation command. A failed
   check is a stop condition, not a suggestion.
6. **Emit the smallest complete artifact.** Use the named template or output
   shape. Do not restate the skill, the inputs, or the validation output.

## Required sections

Every skill body has these sections, in this order:

- `## Inputs` — required/optional arguments, files to read, files to avoid.
- `## Deterministic Steps` — numbered, with exact commands and paths.
- `## LLM Judgment` — the only semantic decisions the model makes.
- `## Output` — exact shape, path, or template.
- `## Stop Conditions` — when to stop, ask, or escalate.
- `## Token Budget` — read limit, output limit, and forbidden context expansion.

## LLM zone

Use judgment for:

- problem/outcome synthesis and prioritization;
- resolving genuine contradictions or missing intent;
- semantic review (fit, quality, risk, trade-offs);
- planning waves and ownership when the constraints conflict.

Do not use judgment for:

- finding files, symbols, or existing tests;
- choosing a command or a timestamp format;
- parsing JSON/TOML/YAML that a script can parse;
- validating required headings, counts, links, or placeholders;
- repeating source text in the output.

## Token budget

- Read at most the files named in `Inputs`; no repository tours.
- Prefer `rg`, `sed -n`, `jq`, and project scripts over broad reads.
- Do not load a directory to find one file.
- Do not restate a template or doctrine file; cite it and follow it.
- Keep the emitted artifact within the budget named by the skill. If it is
  longer, split the work rather than padding.

## Stop conditions

Stop and report when:

- a required input is missing and no named probe can recover it;
- a deterministic validation fails;
- two sources contradict and the choice changes scope or acceptance;
- the work needs a decision only the user can make.

Ask one small batch of blocking questions, then stop. Do not continue on a
guess.
