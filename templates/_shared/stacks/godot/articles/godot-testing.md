---
read_when: "Writing or running Godot tests, or wiring them into CI"
---

# Godot Testing: Headless and Deterministic

`testing.md` applies; this adds the Godot specifics.

## MUST

- Tests run headless (`godot --headless …`) with the project's runner (GUT
  or a project suite script). No editor window in CI.
- Each test builds its own scene or fixture and frees it; no state leaks
  into the next test.
- Assert on data (dictionaries, typed results, node properties), not on
  `print()` output.
- Deterministic: fixed seeds, fixed frame counts, injected time. Don't wait on
  real timers to synchronise.
- The runner exits non-zero on any failure, script error, or missing result,
  and CI checks the exit code.

## SHOULD

- Logic tests on plain classes; scene tests only for wiring.
- A smoke test that loads the main scene (or enables the plugin) and exits
  cleanly.
- Golden files for generated or serialised output.
