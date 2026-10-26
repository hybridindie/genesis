---
read_when: "Adding or changing an MCP tool, resource, prompt, or its schema"
---

# MCP Contract: Tools, Resources, Prompts

The tool surface is the product. Every schema, description, and error is a
public contract an agent will call without a human.

## Tools

- Typed input and output models; defaults documented.
- Name: `surface_verb_object` (`k8s_pod_list`), stable, no verbs like `do`.
- Docstring is the client-facing description: what it does, when to use it,
  what it returns, what fails. Written for an agent.
- Validate before side effects. Unknown arguments are an error, not ignored.
- Return the minimum useful payload; no raw SDK objects.
- Mutations return the concrete effect (path written, node created), not just
  `ok: true`.

## Resources

- Read-only. No side effects in a resource handler.
- Stable URI scheme; JSON-serialisable bodies.
- Large payloads are paginated or depth-limited (`max_depth`, cursors).

## Prompts

- Parameterised templates, typed arguments, no hidden state.
- Prompt text is versioned with the code that consumes it.

## Gating

- Core tools always exposed; domains opt-in per category.
- Enforce gating server-side, not by hiding docs.
- A disabled tool returns a structured "toolset disabled" error with the flag
  to enable it.

## ANTI-PATTERNS

- A single dispatcher tool.
- Returning `dict[str, Any]`.
- Side effects in a resource or prompt.
- Renaming a tool without a deprecation alias.
- Description that restates the name ("lists pods").

## Checklist

- [ ] Typed input/output.
- [ ] Stable name + agent-facing description.
- [ ] Side effects only in tools, validated first.
- [ ] Gating enforced server-side.
