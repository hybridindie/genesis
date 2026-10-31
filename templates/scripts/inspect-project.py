#!/usr/bin/env python3
"""Detect a project's stacks and tooling for the harness renderer.

Read-only. Walks the project to a shallow depth (skipping dependency, build
and hidden directories), reads manifests, and prints one JSON object:

  {
    "project_name": "...", "project_slug": "...",
    "stacks": ["python", "mcp", "godot", "godot-addon"],
    "packs_suggested": ["production"],
    "evidence": {"mcp": "pyproject.toml depends on fastmcp", ...},
    "paths": {"python": ".", "frontend": null, "godot": "godot", "rust": null},
    "python": {...}, "frontend": {...}, "godot": {...},
    "ci_platform": "github" | "gitea",
    "confidence": "high" | "medium" | "low"
  }

Usage: python3 templates/scripts/inspect-project.py <project_root>
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None  # type: ignore[assignment]

MAX_DEPTH = 3
SKIP_DIRS = {
    "node_modules", "venv", "env", "dist", "build", "target", "out",
    "graphify-out", "__pycache__", "site-packages", "mlruns", "coverage",
    "htmlcov", "vendor", "third_party",
}
THIRD_PARTY_ADDONS = {"gut", "gdunit4", "godot-git-plugin", "dialogic", "phantom_camera", "beehave"}

AGENT_DEPS = {"langgraph", "langchain", "langchain-core", "mlflow", "crewai",
              "autogen", "pyautogen", "pydantic-ai", "dspy", "dspy-ai", "llama-index"}
LLM_DEPS = {"openai", "anthropic", "ollama", "litellm", "google-genai"}
MCP_DEPS = {"mcp", "fastmcp"}
FRONTEND_DEPS = {"react", "next", "vue", "svelte", "solid-js", "@angular/core"}
PY_TOOLING_ONLY = {"gdtoolkit", "pre-commit", "pip", "setuptools", "wheel"}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def norm(name: str) -> str:
    return re.split(r"[\s\[<>=!~;@]", name.strip(), maxsplit=1)[0].lower().replace("_", "-")


def walk(root: Path) -> list[Path]:
    """Directories to depth MAX_DEPTH, skipping hidden, dependency and build dirs."""
    found: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = 0 if str(rel) == "." else len(rel.parts)
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".") and d not in SKIP_DIRS and depth < MAX_DEPTH
        )
        found.append(Path(dirpath))
    return found


def shallowest(dirs: list[Path], marker: str) -> Path | None:
    hits = [d for d in dirs if (d / marker).is_file()]
    return min(hits, key=lambda d: (len(d.parts), str(d))) if hits else None


def rel(root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    r = path.relative_to(root).as_posix()
    return "." if r in ("", ".") else r


# ── Python ────────────────────────────────────────────────────────────────


def pyproject_data(path: Path) -> dict[str, Any]:
    text = read(path)
    if tomllib is not None:
        try:
            return tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            pass
    # Fallback: crude scan of quoted requirement strings.
    deps = re.findall(r'^\s*"([A-Za-z0-9_.\-\[\]]+)[^"]*",?\s*$', text, re.MULTILINE)
    return {"project": {"dependencies": deps}, "_raw": text}


def python_deps(data: dict[str, Any]) -> set[str]:
    deps: list[str] = []
    project = data.get("project", {})
    deps += project.get("dependencies", []) or []
    for group in (project.get("optional-dependencies") or {}).values():
        deps += group
    for group in (data.get("dependency-groups") or {}).values():
        deps += [d for d in group if isinstance(d, str)]
    deps += ((data.get("tool") or {}).get("uv") or {}).get("dev-dependencies", []) or []
    poetry = (data.get("tool") or {}).get("poetry") or {}
    deps += list((poetry.get("dependencies") or {}).keys())
    for grp in (poetry.get("group") or {}).values():
        deps += list((grp.get("dependencies") or {}).keys())
    return {norm(d) for d in deps if isinstance(d, str) and d.strip()}


def requirements_deps(path: Path) -> set[str]:
    out = set()
    for line in read(path).splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            out.add(norm(line))
    return out


def python_version(root: Path, py_root: Path, data: dict[str, Any]) -> str:
    for candidate in (py_root / ".python-version", root / ".python-version"):
        if candidate.is_file():
            m = re.match(r"(\d+\.\d+)", read(candidate).strip())
            if m:
                return m.group(1)
    spec = (data.get("project") or {}).get("requires-python", "")
    m = re.search(r"(\d+\.\d+)", spec)
    return m.group(1) if m else "3.12"


def python_info(root: Path, py_root: Path) -> dict[str, Any]:
    pyproject = py_root / "pyproject.toml"
    data = pyproject_data(pyproject) if pyproject.is_file() else {}
    deps = python_deps(data)
    for req in ("requirements.txt", "requirements-dev.txt"):
        if (py_root / req).is_file():
            deps |= requirements_deps(py_root / req)
    tool = data.get("tool") or {}

    if (py_root / "uv.lock").is_file() or "uv" in tool:
        manager = "uv"
    elif (py_root / "poetry.lock").is_file() or "poetry" in tool:
        manager = "poetry"
    else:
        manager = "pip"
    run = {"uv": "uv run ", "poetry": "poetry run ", "pip": ""}[manager]
    sync = {
        "uv": "uv sync --locked" if (py_root / "uv.lock").is_file() else "uv sync",
        "poetry": "poetry install",
        "pip": "python -m pip install -r requirements.txt"
        if (py_root / "requirements.txt").is_file() else "python -m pip install -e .",
    }[manager]

    type_checker = "pyright" if ("pyright" in deps or "pyright" in tool) else "mypy"
    target = "src/" if (py_root / "src").is_dir() else "."
    type_cmd = f"{run}pyright" if type_checker == "pyright" else f"{run}mypy {target}"

    db = None
    if (root / "supabase").is_dir() or "supabase" in deps:
        db = "supabase"
    elif "sqlalchemy" in deps or "sqlmodel" in deps:
        db = "SQLAlchemy"
    elif deps & {"asyncpg", "psycopg", "psycopg2", "psycopg2-binary"}:
        db = "Postgres"

    return {
        "deps": sorted(deps),
        "version": python_version(root, py_root, data),
        "pkg_manager": manager,
        "type_checker": type_checker,
        "sync_cmd": sync,
        "lint_cmd": f"{run}ruff check .",
        "type_cmd": type_cmd,
        "test_cmd": f"{run}pytest",
        "has_mlflow": "mlflow" in deps,
        "has_langgraph": "langgraph" in deps,
        "db_provider": db,
    }


# ── Frontend ──────────────────────────────────────────────────────────────


def frontend_root(dirs: list[Path]) -> tuple[Path | None, dict[str, Any]]:
    best: tuple[Path | None, dict[str, Any]] = (None, {})
    for d in dirs:
        pkg = d / "package.json"
        if not pkg.is_file():
            continue
        try:
            data = json.loads(read(pkg))
        except json.JSONDecodeError:
            continue
        deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        if FRONTEND_DEPS & set(deps):
            if best[0] is None or len(d.parts) < len(best[0].parts):
                best = (d, data)
    return best


def major(version: str | None) -> str:
    m = re.search(r"(\d+)", version or "")
    return m.group(1) if m else ""


def frontend_info(fe_root: Path, data: dict[str, Any]) -> dict[str, Any]:
    deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
    scripts = data.get("scripts") or {}
    if any((fe_root / f).is_file() for f in ("bun.lockb", "bun.lock")):
        manager = "bun"
    elif (fe_root / "pnpm-lock.yaml").is_file():
        manager = "pnpm"
    else:
        manager = "npm"
    runner = {"npm": "npm run", "pnpm": "pnpm run", "bun": "bun run"}[manager]
    npx = {"npm": "npx", "pnpm": "pnpm exec", "bun": "bunx"}[manager]

    lint = f"{runner} lint" if "lint" in scripts else f"{npx} eslint ."
    type_script = next((s for s in ("type-check", "typecheck", "types", "tsc") if s in scripts), None)
    type_cmd = f"{runner} {type_script}" if type_script else f"{npx} tsc --noEmit"
    unit = "vitest" if "vitest" in deps else "jest" if "jest" in deps else None
    if "test" in scripts:
        test = f"{npx} vitest run" if unit == "vitest" and "run" not in scripts["test"] else f"{runner} test"
    else:
        test = f"{npx} vitest run" if unit == "vitest" else f"{npx} jest" if unit == "jest" else f"{runner} test"

    parts = []
    if "next" in deps:
        parts.append(f"Next {major(deps['next'])}".strip())
    for name, label in (("react", "React"), ("vue", "Vue"), ("svelte", "Svelte")):
        if name in deps:
            parts.append(f"{label} {major(deps[name])}".strip())
    if "typescript" in deps:
        parts.append("TypeScript")
    if "tailwindcss" in deps:
        parts.append("Tailwind")
    if "vite" in deps and "next" not in deps:
        parts.append("Vite")
    tests = [t for t in (unit.capitalize() if unit else None,
                         "Playwright" if "@playwright/test" in deps else None,
                         "Cypress" if "cypress" in deps else None) if t]
    summary = ", ".join(parts) + (f"; tests: {' + '.join(tests)}" if tests else "")
    return {
        "pkg_manager": manager,
        "lint_cmd": lint,
        "type_cmd": type_cmd,
        "test_cmd": test,
        "unit_runner": unit,
        "stack_summary": summary or "see package.json",
    }


# ── Godot ─────────────────────────────────────────────────────────────────


def godot_info(g_root: Path) -> dict[str, Any]:
    text = read(g_root / "project.godot")
    m = re.search(r'config/features=PackedStringArray\("(\d+\.\d+)', text)
    addons = g_root / "addons"
    own_addons = sorted(
        p.parent.name for p in addons.glob("*/plugin.cfg")
        if p.parent.name.lower() not in THIRD_PARTY_ADDONS
    ) if addons.is_dir() else []
    if (addons / "gut").is_dir():
        test_cmd = "godot --headless -s addons/gut/gut_cmdln.gd -gexit"
    elif (addons / "gdUnit4").is_dir():
        test_cmd = "godot --headless -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests"
    else:
        test_cmd = "godot --headless --script res://tests/run_tests.gd"
    return {"version": m.group(1) if m else "4", "own_addons": own_addons, "test_cmd": test_cmd}


# ── Decision ──────────────────────────────────────────────────────────────


def inspect(root: Path) -> dict[str, Any]:
    dirs = walk(root)
    stacks: list[str] = []
    evidence: dict[str, str] = {}
    out: dict[str, Any] = {
        "project_name": root.name,
        "project_slug": re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-"),
    }

    py_root = shallowest(dirs, "pyproject.toml")
    if py_root is None:
        req_root = shallowest(dirs, "requirements.txt")
        if req_root is not None and requirements_deps(req_root / "requirements.txt") - PY_TOOLING_ONLY:
            py_root = req_root
    fe_root, fe_pkg = frontend_root(dirs)
    g_root = shallowest(dirs, "project.godot")
    rs_root = shallowest(dirs, "Cargo.toml")

    if py_root is not None:
        py = python_info(root, py_root)
        deps = set(py.pop("deps"))
        out["python"] = py
        stacks.append("python")
        evidence["python"] = f"{rel(root, py_root)}/pyproject.toml or requirements.txt"
        if deps & MCP_DEPS:
            stacks.append("mcp")
            evidence["mcp"] = f"depends on {', '.join(sorted(deps & MCP_DEPS))}"
        has_evals = any((py_root / d).is_dir() for d in ("evals", "eval", "evaluations"))
        if deps & AGENT_DEPS or (deps & LLM_DEPS and has_evals):
            stacks.append("agent")
            evidence["agent"] = f"depends on {', '.join(sorted((deps & AGENT_DEPS) or (deps & LLM_DEPS)))}" + (
                " with an evals directory" if not deps & AGENT_DEPS else "")
        if "fastapi" in deps:
            stacks.append("fastapi")
            evidence["fastapi"] = "depends on fastapi"
    if fe_root is not None:
        out["frontend"] = frontend_info(fe_root, fe_pkg)
        stacks.append("frontend")
        evidence["frontend"] = f"{rel(root, fe_root)}/package.json ({out['frontend']['stack_summary']})"
    if g_root is not None:
        out["godot"] = godot_info(g_root)
        stacks.append("godot")
        evidence["godot"] = f"{rel(root, g_root)}/project.godot"
        if out["godot"]["own_addons"]:
            stacks.append("godot-addon")
            evidence["godot-addon"] = f"addons/{', '.join(out['godot']['own_addons'])}/plugin.cfg"
    if rs_root is not None:
        stacks.append("rust")
        evidence["rust"] = f"{rel(root, rs_root)}/Cargo.toml"

    packs = []
    deploy = [p for p in ("Dockerfile", "docker-compose.yml", "docker-compose.prod.yml", "k8s", "helm", "deploy")
              if (root / p).exists()]
    if deploy and ({"fastapi", "mcp"} & set(stacks)):
        packs.append("production")
        evidence["production (pack)"] = f"deploy files: {', '.join(deploy)}"

    out.update({
        "stacks": stacks,
        "packs_suggested": packs,
        "evidence": evidence,
        "paths": {
            "python": rel(root, py_root),
            "frontend": rel(root, fe_root),
            "godot": rel(root, g_root),
            "rust": rel(root, rs_root),
        },
        "ci_platform": "gitea" if (root / ".gitea" / "workflows").is_dir() else "github",
        "has_ci": any((root / d / "workflows").is_dir() and any((root / d / "workflows").iterdir())
                      for d in (".github", ".gitea")),
        "confidence": "high" if stacks else "low",
    })
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: inspect-project.py <project_root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 1
    print(json.dumps(inspect(root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
