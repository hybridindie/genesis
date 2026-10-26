---
name: e2e-assertion-audit
description: Scan E2E tests for no-op assertions, overly permissive checks, missing negative cases, and fragile selectors.
when_to_use: >
  Run before trusting an E2E suite or after adding a journey. Trigger phrases:
  "audit e2e assertions", "find no-op tests", "check test confidence", "review
  Playwright tests".
user-invocable: true
disable-model-invocation: true
---

# E2E Assertion Audit

<!--
  contract: .claude/rules/doctrine/skill-execution.md
  version: 2.0.0, owner: John D
-->

Run fixed searches over `tests/e2e/**`, then judge whether each hit is a real
confidence gap. Do not edit tests unless asked.

## Inputs

- Required: the E2E test root (`tests/e2e/**` or the project's configured path).
- Read: only the matching file and the surrounding assertion block.
- Do not read: unit tests, production source, or unrelated repositories.

## Deterministic Steps

1. **Scan once.**
   ```bash
   python3 .claude/skills/e2e-assertion-audit/scripts/scan.py tests/e2e
   ```
   The script owns the no-op, permissive, and fragile-selector patterns.
2. **Missing negative cases.** For each journey file, list the tested actions and
   check whether there is at least one rejection, unauthorized, empty, or failure
   assertion. Use `rg -n 'unauthorized|forbidden|404|422|error|invalid' tests/e2e 2>/dev/null || true`.
3. **Triage each hit** as:
   - `ERROR` — the assertion can pass without validating the feature.
   - `WARNING` — it may be too permissive or fragile.
   - `CLEAN` — specific and intentional.
4. **Emit the report** with a concrete replacement per finding.

## LLM Judgment

Use judgment only for:

- whether a selector is genuinely ambiguous in context;
- whether a negative case is material to the journey;
- the concrete replacement assertion.

Do not invent tests or rewrite clean assertions. If a hit reveals an
out-of-scope product bug, add a one-line note; do not expand the audit.

## Output

```markdown
## E2E Assertion Audit

### No-Op Assertions
- ERROR|WARNING `<file>:<line>` — <why> — replace with: <assertion>

### Permissive Checks
- …

### Missing Negative Cases
- `<file>` — missing <case> — add: <assertion>

### Fragile Selectors
- …

**Clean:** <file list or none>
```

## Stop Conditions

- Stop if `tests/e2e/` does not exist; report the configured path instead.
- Do not audit unit tests or production code.
- Do not apply fixes without an explicit request.

## Token Budget

- Run the four searches once; no per-file rescans.
- Default: open at most 20 assertion blocks. If there are more hits, triage the
  highest-severity 20 and report the remaining count as untriaged.
- Target ≤ 700 words; cite file:line and one replacement, not full files.
