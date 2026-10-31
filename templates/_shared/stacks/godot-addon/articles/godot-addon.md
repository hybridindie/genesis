---
read_when: "Building or changing a Godot EditorPlugin/addon, its commands, or its dock"
paths:
  - "{{GODOT_PATH}}/addons/**"
---

# Godot Addon: Editor-Only, One Router, Undoable

An addon is an `EditorPlugin` that owns a command surface. Builds on
`godot.md`.

## MUST

- Editor scripts are `@tool`; the entry script extends `EditorPlugin`.
- `_enter_tree()` / `_exit_tree()` set up and tear down everything;
  enabling and disabling the plugin never errors or leaks.
- Commands are one handler each (`cmd_<verb>_<noun>`), reached through a
  single router.
- Every project mutation goes through `EditorUndoRedoManager`.
- Values leaving the addon are JSON-safe (`godot-serialization.md`).
- Router errors are structured results (`error-handling.md`), not just
  `push_error`.

## SHOULD

- Handlers stay short; logic lives in `RefCounted` helpers.
- The dock shows status and does not mutate the project itself.

## ANTI-PATTERNS

- A mutation without an undo entry.
- Editor singletons captured at load time.
- A second way to invoke a command that skips the router.
