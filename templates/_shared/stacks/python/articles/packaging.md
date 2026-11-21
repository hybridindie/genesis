---
read_when: "Changing packaging, entry points, versions, or the Python floor"
paths:
  - "**/pyproject.toml"
  - "**/uv.lock"
  - "**/__init__.py"
---

# Python Packaging: One Command, One Version Source

## MUST

- `uv` owns the environment (`dependency-security.md` covers the lockfile).
- `pyproject.toml` declares the runtime floor (`requires-python`) and console
  entry points.
- `src/` layout; the package is importable without the repository root on
  `sys.path`.
- The version lives in `pyproject.toml` or `__version__`, nowhere else.
- Public API is typed and documented; private modules start with `_`.
- Removing or renaming a public symbol requires a deprecation cycle.

## SHOULD

- `uv run <tool>` in docs and CI, never bare `python`.
- Optional extras for heavy/optional features (`[project.optional-dependencies]`).
- Build a wheel in CI and install it into a clean environment for a smoke test.
- Keep dev tools (ruff, mypy, pytest) in a `dev` group.

## ANTI-PATTERNS

- `pip install -e .` as the documented path.
- Shipping tests and caches in the wheel.
- A package name that differs from the import name without documentation.
