---
read_when: "Building or changing a Godot EditorPlugin/addon, its commands, or its UI"
---

# Godot Addon Architecture: Editor-Only, Router, Undo

An addon is an `EditorPlugin` that owns a command surface. The editor is the
only runtime; treat its API as the boundary.

## MUST

- Every script is `@tool`; the entry script extends `EditorPlugin`.
- `_enter_tree()` and `_exit_tree()` set up and tear down cleanly. Enabling and
  disabling the plugin never crashes or leaks.
- Commands are one handler each, named `cmd_<verb>_<noun>`, reached through a
  single router. No ad-hoc entry points.
- Every mutation is wrapped in `EditorUndoRedoManager` so a human can undo it.
- Never block the editor thread: no long loops, sleeps, or synchronous network
  work in a handler.
- The dock is read-only status; it never mutates the project.
- Values crossing the boundary are JSON-safe (see the serialization rule).

## SHOULD

- Handlers under ~40 lines; domain logic in plain `RefCounted` helpers.
- One status/log surface; no `print()` spam.
- Explicit error results for the router, not just `push_error`.

## ANTI-PATTERNS

- A handler that mutates without UndoRedo.
- Editor singletons captured at import/module load.
- Returning Godot objects or non-serialisable values.
- Blocking the editor waiting for a client/agent.
- Two routers or a second way to invoke a command.

## Checklist

- [ ] `@tool` on every script; clean enable/disable.
- [ ] Single router; one handler per command.
- [ ] UndoRedo on every mutation.
- [ ] No blocking work on the editor thread.
