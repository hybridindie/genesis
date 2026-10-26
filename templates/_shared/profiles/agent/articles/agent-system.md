---
read_when: "Building an LLM agent system, graph, prompt flow, or evaluation"
---

# Agent Systems: Deterministic Runs, Versioned Prompts, Real Evals

An agent system is a program with a probabilistic component. Make everything
around the model deterministic and observable.

## MUST

- The graph/flow is explicit: nodes, edges, state schema, and termination
  conditions are code, not prose.
- Prompts are versioned and loaded by name; no inline strings scattered through
  nodes. A prompt change is a reviewable change.
- Tool calls use typed schemas and validate arguments before execution; tool
  errors are returned to the model, not raised as crashes.
- Every run is reproducible: seed, model id, prompt versions, tool versions,
  and inputs recorded.
- Budgets are enforced: max steps, token/cost ceiling, wall-clock timeout.
- Evals are executable and versioned: a dataset, a grader, and a pass threshold.
  "It looked good" is not an eval.
- Untrusted model output is data: never `eval`, never shell-interpolate, never
  grant it filesystem/network scope beyond the tool contract.

## SHOULD

- Persist run traces (inputs, tool calls, outputs, costs) for debugging/evals.
- Separate orchestration from domain tools; tools are plain typed functions.
- Fail closed on unknown state transitions.

## ANTI-PATTERNS

- Infinite retry loops with no step/cost budget.
- Prompt text duplicated between code and MLflow/registry.
- Evals that only check "did not crash".
- Letting the model choose arbitrary tool names/paths without validation.
- Hidden global conversation state shared across runs.

## Checklist

- [ ] Explicit state machine with termination.
- [ ] Prompts versioned and reviewed.
- [ ] Run record is reproducible.
- [ ] Budgets enforced.
- [ ] Eval suite runs in CI or nightly.
