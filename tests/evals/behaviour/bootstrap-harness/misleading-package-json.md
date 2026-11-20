# Case: a Python repo that carries a package.json for tooling

## Input

> Install the harness. The repo has `pyproject.toml` with fastapi, a `tests/`
> dir, and `package.json` whose only dependency is `prettier`, used by a
> pre-commit hook to format YAML.

## Expected properties

- The plan proposes **`python` + `fastapi` only** — the `package.json` is
  tooling, not a frontend, and no `frontend/` path or frontend rule appears.
- It asks for confirmation with the plan before rendering, and names the
  stacks/packs it intends to add.
- If any file is skipped because it already exists (`my-workflows.md`,
  `.githooks/`, CI), the report says which — it does not silently reuse them.
- It does not claim the harness is installed before the renderer has run, and
  it reports the validation result afterwards.
