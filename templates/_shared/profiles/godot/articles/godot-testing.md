---
read_when: "Writing or running tests for a Godot addon"
---

# Godot Testing: Headless, Fixture Scenes, Assert JSON

## MUST

- Tests run headless: `godot --headless --script res://tests/...` or GUT in
  headless mode. No editor UI in CI.
- Each test owns a fixture scene; no shared mutable scene state between tests.
- Assert the serialized result (JSON-safe dictionary), not editor-only objects.
- Test command routing: unknown command, bad params, and a successful mutation.
- Test UndoRedo: perform, undo, assert the prior state and that the undo entry
  exists.
- Determinism: fixed frame counts, injected ids/time, no real timers.
- CI fails on a non-zero exit, an unparsed error, or a missing test result.

## SHOULD

- One fixture per behaviour, reused by a setup helper.
- A smoke test that enables and disables the `EditorPlugin` cleanly.
- Serialization round-trip tests for each supported type.

## ANTI-PATTERNS

- Tests that need a visible editor window.
- `await get_tree().create_timer(x).timeout` as synchronisation.
- Asserting `print()` output.
- Leaving the scene tree mutated for the next test.
- Skipping tests when a plugin fails to load.

## Checklist

- [ ] Headless run is green.
- [ ] Fixture per test.
- [ ] Undo path covered.
- [ ] No editor UI dependency.
