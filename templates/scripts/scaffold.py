#!/usr/bin/env python3
"""Create the small repo-hygiene skeleton a new project needs.

This is deliberately minimal: README, LICENSE, .gitignore, Makefile, and for
Python profiles a package + smoke test. It never overwrites an existing file.
The harness itself is rendered by bootstrap.sh; this runs afterwards.

Usage:
  python3 templates/scripts/scaffold.py --root ../my-project [--license MIT] [--author "Name"]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

MIT = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

PYTHON_PROFILES = {"mcp", "python", "agent"}


def write_if_missing(path: Path, text: str, written: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    written.append(str(path))


def git_author(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "config", "user.name"], text=True
        ).strip() or "The Authors"
    except (OSError, subprocess.CalledProcessError):
        return "The Authors"


def gitignore(profile: str) -> str:
    lines = [
        "# OS / editor",
        ".DS_Store",
        ".idea/",
        ".vscode/",
        "",
        "# Secrets",
        ".env",
        ".env.*",
        "!.env.example",
    ]
    if profile in PYTHON_PROFILES:
        lines += [
            "",
            "# Python",
            ".venv/",
            "__pycache__/",
            "*.py[cod]",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            "dist/",
            "build/",
            "*.egg-info/",
            "htmlcov/",
            ".coverage",
        ]
    if profile == "web":
        lines += [
            "",
            "# Node",
            "node_modules/",
            "dist/",
            "coverage/",
            "*.local",
        ]
    if profile == "godot":
        lines += [
            "",
            "# Godot",
            ".godot/",
            ".import/",
            "export/",
        ]
    return "\n".join(lines) + "\n"


def readme(profile: str, name: str) -> str:
    quickstart = {
        "mcp": "Add the server package under `src/`, then run:\n\n```bash\nuv sync\nmake check\n```",
        "python": "Add the package under `src/`, then run:\n\n```bash\nuv sync\nmake check\n```",
        "agent": "Add the graph/state package under `src/`, then run:\n\n```bash\nuv sync\nmake check\n```",
        "web": "Put the FastAPI app in `backend/` and the React app in `frontend/`, then run:\n\n```bash\nmake check\n```",
        "godot": "Open the project in Godot 4.4+, enable the addon, then run:\n\n```bash\nmake check\n```",
    }[profile]
    return f"""# {name}

{name} is scaffolded with the [genesis](https://github.com/hybridindie/genesis)
AI harness. The harness lives in `AGENTS.md`, `.claude/`, and `.opencode/`; the
project code starts here.

## Quick start

{quickstart}

## Checks

- `make check` — the local equivalent of CI.
- `bash .claude/hooks/install-git-hooks.sh` — install the fast pre-commit and
  pre-push gates once per clone.
- Run `/preflight` in Claude Code or OpenCode before pushing.

## Layout

The project owns `README.md`, `LICENSE`, `.gitignore`, `Makefile`, the application
code, and `.github/workflows/ci.yml`. Edit the harness in place; there is no
`templates/` directory here.
"""


def pyproject(slug: str, module: str, python: str) -> str:
    return f"""[project]
name = "{slug}"
version = "0.1.0"
description = "TODO: one sentence"
requires-python = ">={python}"
dependencies = []

[dependency-groups]
dev = [
  "mypy>=1.13",
  "pytest>=8",
  "ruff>=0.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{module}"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "{python}"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
"""


def makefile(profile: str) -> str:
    if profile in PYTHON_PROFILES:
        return (
            ".PHONY: check\n"
            "check:\n"
            "\tuv run ruff check .\n"
            "\tuv run mypy src/\n"
            "\tuv run pytest tests -q\n"
        )
    if profile == "web":
        return (
            ".PHONY: check\n"
            "check:\n"
            "\tcd backend && uv run ruff check . && uv run mypy src/ && uv run pytest\n"
            "\tcd frontend && npm run lint && npm run type-check && npx vitest run\n"
        )
    return ".PHONY: check\ncheck:\n\tgdformat --check .\n\tgdlint .\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold repo hygiene for a new project")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--license", default="MIT", help="MIT or none")
    parser.add_argument("--author", default="", help="copyright holder")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / ".claude" / "harness.json"
    if not manifest_path.is_file():
        print("scaffold: .claude/harness.json is missing; run bootstrap first", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = manifest.get("profile")
    name = manifest.get("project_name") or root.name
    slug = manifest.get("project_slug") or root.name
    module = slug.replace("-", "_")
    python = str(manifest.get("python_version") or "3.12")
    author = args.author or git_author(root)

    written: list[str] = []
    skipped: list[str] = []

    write_if_missing(root / ".gitignore", gitignore(profile), written, skipped)
    write_if_missing(root / "README.md", readme(profile, name), written, skipped)
    write_if_missing(root / "Makefile", makefile(profile), written, skipped)
    if args.license.lower() != "none":
        write_if_missing(
            root / "LICENSE",
            MIT.format(year=date.today().year, author=author),
            written,
            skipped,
        )

    if profile in PYTHON_PROFILES:
        write_if_missing(root / "pyproject.toml", pyproject(slug, module, python), written, skipped)
        write_if_missing(
            root / "src" / module / "__init__.py",
            '"""Project package."""\n\n__version__ = "0.1.0"\n',
            written,
            skipped,
        )
        write_if_missing(
            root / "tests" / "unit" / "test_smoke.py",
            f"from {module} import __version__\n\n\ndef test_version() -> None:\n    assert __version__\n",
            written,
            skipped,
        )

    for path in written:
        print(f"  wrote {Path(path).relative_to(root)}")
    for path in skipped:
        print(f"  kept  {Path(path).relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
