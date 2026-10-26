---
name: gen-contract-test
description: Scaffold one contract test for a backend or frontend service, then confirm the RED phase.
when_to_use: >
  Run when adding a contract test before implementation. Trigger phrases:
  "generate a contract test", "scaffold the API test", "add a service contract
  test", "start TDD for this endpoint".
user-invocable: true
disable-model-invocation: true
arguments:
  - name: target
    description: "Service or module to test (e.g., 'analytics-service', 'auth/login')"
    required: true
  - name: stack
    description: "backend or frontend (default: backend)"
    required: false
---

# Generate Contract Test

<!--
  contract: .claude/rules/doctrine/skill-execution.md
  version: 2.0.0, owner: John D
-->

Scaffold one contract test with the skill's deterministic asset, then run it to
prove the RED phase. The model chooses the contract cases; the script owns paths
and boilerplate.

## Inputs

- Required: `target`; optional `stack` (`backend` default, or `frontend`).
- Read: the target's public surface and one existing contract test for style.
- Do not read: the whole test suite, implementation internals, or unrelated
  modules.

## Deterministic Steps

1. **Normalize.** `STACK="${stack:-backend}"`; accept only `backend` or
   `frontend`.
2. **Locate the target.** Use `rg -n` for the service/router/module in the
   stack's source root; record the exact file and public methods.
3. **Check existing coverage.** Run
   `rg -n "<target>" {{BACKEND_PATH}}/tests/contract {{FRONTEND_PATH}}/tests/contract 2>/dev/null || true`.
   If the same contract exists, report it and scaffold only uncovered surface.
4. **Choose the output path.**
   - backend: `{{BACKEND_PATH}}/tests/contract/test_<target_snake>_contract.py`
   - frontend: `{{FRONTEND_PATH}}/tests/contract/<target-kebab>-contract.test.ts`
5. **Scaffold deterministically.**
   ```bash
   python3 .claude/skills/gen-contract-test/scripts/scaffold_contract.py \
     --stack "$STACK" --target "<target>" --path "<route-or-module>" \
     --method "<get|post|…>" --status "<expected>" --out "<output path>"
   ```
   The script refuses to overwrite an existing file.
6. **Replace the TODO cases** with the contract surface: success schema,
   validation error envelope, and auth requirement. Do not add skips.
7. **Prove RED.** Run the stack's test command for that one file; the test must
   fail for the missing behavior, not for a syntax/import error. Report the
   failure output.
8. **Report** the file path, cases added, and the RED result.

## LLM Judgment

Use judgment only for:

- the endpoint/module contract and expected status codes;
- valid/invalid payloads and auth cases;
- the assertions that prove the envelope.

Do not invent routes or implementation details.

## Output

- The created test file path.
- The RED-phase command and its failure summary.
- Uncovered surface or an explicit “none”.

## Stop Conditions

- Stop if the target cannot be located.
- Stop if the output file already exists; do not overwrite it.
- Stop if the test passes immediately (not RED) or fails on import/syntax.
- Do not add `pytest.mark.skip`, `xfail`, `it.skip`, `.todo`, `xit`, or
  `xdescribe`.

## Token Budget

- Read the target and at most one existing contract test.
- Do not list the whole test tree; use the named `rg` command.
- Output ≤ 250 words plus the test file.
