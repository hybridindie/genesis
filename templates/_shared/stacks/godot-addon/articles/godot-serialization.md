---
read_when: "Returning data from an addon command or parsing data into the editor"
---

# Godot Serialization: JSON-Safe, One Coercion Layer

## MUST

- Values crossing the addon boundary are JSON-safe: `String`, `int`, `float`,
  `bool`, `Array`, `Dictionary`, `null`. Nothing else.
- Godot types (`Vector2/3`, `Color`, `Rect2`, `NodePath`, `Transform*`) are
  converted in one helper (`type_coerce.gd`), never inline per handler.
- Coercion is round-trippable: convert out and back without loss for supported
  types; document the encoding.
- Scene trees serialize to a stable shape: `{ name, type, script, children }`
  with an explicit `max_depth`; no cycles.
- Node paths are absolute from the scene root; missing nodes are an error, not
  an empty object.
- Large payloads are paginated or truncated with an explicit marker and count.

## SHOULD

- A version field on complex payloads.
- Golden fixtures for each supported type.
- Fail loudly on an unknown type rather than stringifying it silently.

## ANTI-PATTERNS

- Returning a `Node`, `Resource`, or `Object` across the boundary.
- `str(value)` as a fallback encoding.
- Duplicated conversion code in multiple handlers.
- Unbounded recursion over the scene tree.
- Silent `null` for a missing node.
