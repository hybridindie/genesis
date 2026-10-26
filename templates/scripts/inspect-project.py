#!/usr/bin/env python3
r"""
Project Introspection Engine — auto-detect tech stack and recommend harness params.

Scans a project directory and emits a JSON blob that `bootstrap.sh`
(and the customize-harness skill) can consume directly.

Detection heuristics (ordered by reliability):
  1. Lockfile / deps file contents (pyproject.toml, package.json, go.mod, Cargo.toml)
  2. Directory structure (src/ layout, framework-specific dirs)
  3. Source code imports (first 5 .py / .ts files matching framework patterns)
  4. Config files (vite.config.ts, supabase/config.toml, next.config.js, etc.)

Usage:
  python3 templates/scripts/inspect-project.py <project_root>

Output (JSON examples):
  Full SaaS (default):
  {
    "mode": "full",
    "profile": "web",
    "project_name": "acme",
    "project_slug": "acme",
    "python_version": "3.12",
    "fastapi_version": "0.119+",
    "react_version": "19",
    "typescript_version": "5.9",
    "vite_version": "7.3",
    "db_provider": "supabase",
    "state_manager": "zustand",
    "pkg_manager_backend": "uv",
    "pkg_manager_frontend": "npm",
    "test_backend_cmd": "uv run pytest",
    "test_frontend_cmd": "npx vitest run",
    "db_extensions": [],
    "has_mlflow": false,
    "has_langgraph": false,
    "tailwind": true,
    "zod_validation": true,
    "cicd_platform": "github-actions",
    "e2e_tool": "playwright",
    "ui_library": "shadcn/ui",
    "confidence": "high"
  }

  MCP service (Python-only):
  {
    "mode": "backend-only",
    "profile": "mcp",
    "project_name": "mcp-weather",
    "python_version": "3.12",
    "fastapi_version": null,
    "react_version": null,
    "typescript_version": null,
    "vite_version": null,
    "db_provider": null,
    "state_manager": null,
    "pkg_manager_backend": "uv",
    "pkg_manager_frontend": null,
    "test_backend_cmd": "uv run pytest",
    "test_frontend_cmd": null,
    "has_mlflow": false,
    "has_langgraph": false,
    "cicd_platform": "github-actions",
    "confidence": "high"
  }
"""

from __future__ import annotations

import ast
import glob
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# ── Heuristic constants ──────────────────────────────────────────────────────
BACKEND_PACKAGES = {
    "fastapi": ("fastapi", r'"fastapi(?:\[[^\]]*\])?"\s*:?\s*["\']?\~?\>?\=?\s*[0-9.+\*a-z]+'),
    "flask": ("flask", r'"flask"\s*:?\s*["\']?\~?\>?\=?\s*[0-9.+\*a-z]+'),
    "mcp": ("mcp", r'"mcp"'),
    "uvicorn": ("uvicorn", r'"uvicorn"'),
    "httpx": ("httpx", r'"httpx"'),
    "asyncpg": ("asyncpg", r'"asyncpg"'),
    "psycopg2": ("psycopg2", r'"psycopg2"'),
    "supabase": ("supabase", r'"supabase"'),
    "sqlalchemy": ("sqlalchemy", r'"sqlalchemy"'),
    "playwright": ("playwright", r'"playwright"'),
}

FRONTEND_PACKAGES = {
    "react": ("react", r'"react"\s*:?\s*["\']?\~?\>?\=?\s*[0-9.+\*a-z]+'),
    "next": ("next", r'"next"\s*:?\s*["\']?\~?\>?\=?\s*[0-9.+\*a-z]+'),
    "vite": ("vite", r'"vite"\s*:?\s*["\']?\~?\>?\=?\s*[0-9.+\*a-z]+'),
    "zustand": ("zustand", r'"zustand"'),
    "redux": ("redux", r'"redux"'),
    "tailwindcss": ("tailwindcss", r'"tailwindcss"'),
}

DB_PACKAGES = {
    "psycopg2": "postgres",
    "asyncpg": "postgres",
    "supabase": "supabase",
    "sqlmodel": "postgres",
}

CI_DIRS = {
    ".github/workflows": "github-actions",
    ".gitlab-ci.yml": "gitlab-ci",
    ".circleci": "circleci",
    "azure-pipelines.yml": "azure-pipelines",
}

E2E_PACKAGES = {
    "playwright": "playwright",
    "cypress": "cypress",
    "vitest": None,  # Unit, not E2E
}


# ── File readers ──────────────────────────────────────────────────────────────

def read_text(p: Path, max_bytes: int = 500_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
    except Exception:
        return ""


def parse_semver(text: str, package_name: str) -> str | None:
    """Loose semver extraction from dependency string."""
    # Match: "fastapi" : "0.119+"  OR  "fastapi" : ">=0.119"
    pat = re.compile(
        rf'"{re.escape(package_name)}(?:\[[^\]]*\])?"\s*[:=]\s*["\']?'
        rf'[\~\^\><\=\!]*([0-9][0-9.+\*a-z]*)',
        re.IGNORECASE,
    )
    m = pat.search(text)
    return m.group(1).rstrip(",;") if m else None


def parse_pyproject_deps(text: str) -> dict[str, str]:
    """Extract direct dependencies from a pyproject.toml string."""
    deps: dict[str, str] = {}
    # Poetry-style [tool.poetry.dependencies]
    in_poetry_deps = False
    for line in text.splitlines():
        if "[tool.poetry.dependencies]" in line:
            in_poetry_deps = True
            continue
        if in_poetry_deps:
            if line.startswith("[") and line.endswith("]"):
                break
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                # "fastapi" = "^0.119.0"
                m = re.match(r'^([a-zA-Z0-9_\-]+)\s*=\s*"([^"]+)"', stripped)
                if m:
                    deps[m.group(1).lower()] = m.group(2)

    # PEP 621 / uv hatchling [project.dependencies] — quoted list format
    in_proj_deps = False
    for line in text.splitlines():
        if "[project]" in line:
            in_proj_deps = False  # reset
            continue
        if "dependencies" in line and "=" in line and ("[" in line or not line.strip().endswith("]")):
            in_proj_deps = True
            continue
        if in_proj_deps:
            stripped = line.strip()
            if stripped.startswith("]"):
                in_proj_deps = False
                continue
            if stripped.startswith("#"):
                continue
            # Match "fastapi>=0.104.0,<1.0.0"
            m = re.match(r'^"([a-zA-Z0-9_\-]+)(?:\[[^\]]*\])?\s*([><~=!]+=?)\s*([0-9][0-9.+\*a-z]*)"', stripped)
            if m:
                deps[m.group(1).lower()] = m.group(3)

    return deps


def parse_requirements_txt(text: str) -> dict[str, str]:
    deps: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = re.match(r'^([a-zA-Z0-9_\-]+)\s*\[?[^\]]*\]?\s*[\><\~\=\!]*=[\s]*([0-9][0-9.+\*a-z]*)', line)
        if m:
            deps[m.group(1).lower()] = m.group(2)
        else:
            pkg = line.split("=>", 1)[0].split("[")[0].strip().lower()
            if pkg:
                deps[pkg] = "*"
    return deps


def parse_package_json(text: str) -> dict[str, str]:
    try:
        data: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError:
        return {}
    all_deps: dict[str, str] = {}
    for k in ("dependencies", "devDependencies"):
        for pkg, ver in data.get(k, {}).items():
            all_deps[pkg.lower()] = str(ver).lstrip("^~")
    return all_deps


# ── Core detection ────────────────────────────────────────────────────────────

class ProjectInspector:
    def __init__(self, root: Path):
        self.root = root
        self.py_deps: dict[str, str] = {}
        self.js_deps: dict[str, str] = {}
        self.confidence = "medium"

    # ── Phase 1: Dependency discovery ───

    def scan_deps(self) -> None:
        # Python deps
        pyproject = self.root / "pyproject.toml"
        if pyproject.is_file():
            self.py_deps.update(parse_pyproject_deps(read_text(pyproject)))
            self.confidence = "high"
        req = self.root / "requirements.txt"
        if req.is_file():
            self.py_deps.update(parse_requirements_txt(read_text(req)))

        # JS deps
        pkg = self.root / "package.json"
        if pkg.is_file():
            self.js_deps.update(parse_package_json(read_text(pkg)))
            self.confidence = "high"

        # Monorepo detection: search nested package.json / pyproject.toml
        for f in self.root.rglob("pyproject.toml"):
            if f == pyproject:
                continue
            self.py_deps.update(parse_pyproject_deps(read_text(f)))
        for f in self.root.rglob("package.json"):
            if f == pkg:
                continue
            self.js_deps.update(parse_package_json(read_text(f)))

    # ── Phase 2: Import sniffer ───

    def sniff_imports(self, pattern: str, limit: int = 5) -> set[str]:
        """Read first `limit` matching files and extract top-level imports."""
        found: set[str] = set()
        for p in sorted(self.root.rglob(pattern))[:limit]:
            if p.stat().st_size > 50_000:
                continue  # Skip huge generated files
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found.add(alias.name.split(".")[0].lower())
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        found.add(node.module.split(".")[0].lower())
        return found

    def sniff_mcp(self) -> bool:
        """Detect MCP via imports or file names."""
        if "mcp" in self.py_deps:
            return True
        imports = self.sniff_imports("*.py", limit=8)
        if "mcp" in imports:
            return True
        # File names like weather_mcp.py, mcp_server.py
        # Exclude config files (.mcp.json is VS Code MCP config, not a server)
        for p in self.root.rglob("*.py"):
            if re.search(r"(?:^|_)mcp(?:_|\.|$)", p.name, re.IGNORECASE):
                return True
        return False

    def sniff_fastapi(self) -> bool:
        if "fastapi" in self.py_deps:
            return True
        return "fastapi" in self.sniff_imports("*.py", limit=5)

    def sniff_flask(self) -> bool:
        if "flask" in self.py_deps:
            return True
        return "flask" in self.sniff_imports("*.py", limit=5)

    def sniff_frontend(self) -> bool:
        if any(k in self.js_deps for k in ("react", "next")):
            return True
        # Look for common frontend files
        for name in ("vite.config.ts", "vite.config.js", "next.config.js", "next.config.ts", "src/App.tsx", "src/main.tsx", "index.html"):
            if (self.root / name).is_file():
                return True
        return False

    def sniff_nextjs(self) -> bool:
        """Detect Next.js specifically (vs plain React+Vite)."""
        if "next" in self.js_deps:
            return True
        for name in ("next.config.js", "next.config.ts", "next.config.mjs"):
            if (self.root / name).is_file():
                return True
        # App Router signal
        if (self.root / "app").is_dir() and any(
            (self.root / "app" / f).exists()
            for f in ("layout.tsx", "layout.jsx", "page.tsx", "page.jsx")
        ):
            return True
        return False

    # ── Phase 3: Config & infra ───

    def detect_db(self) -> str | None:
        for pkg, db in DB_PACKAGES.items():
            if pkg in self.py_deps or (self.root / f"{pkg}").exists():
                return db
        if (self.root / "supabase").is_dir() or (self.root / "supabase" / "config.toml").is_file():
            return "supabase"
        if any((self.root / d).is_dir() for d in ("migrations", "alembic", "prisma")):
            # Heuristic: if postgres package present, it's postgres
            if any(p in self.py_deps for p in ("asyncpg", "psycopg2", "psycopg")):
                return "postgres"
        return None

    def detect_ci(self) -> str:
        for subdir, platform in CI_DIRS.items():
            if (self.root / subdir).exists():
                return platform
        return "github-actions"

    def detect_e2e(self) -> str | None:
        for pkg, tool in E2E_PACKAGES.items():
            if pkg in self.js_deps:
                return tool
        if (self.root / "e2e").is_dir():
            return "playwright"
        return None

    def detect_tailwind(self) -> bool:
        return "tailwindcss" in self.js_deps or (self.root / "tailwind.config.js").is_file() or (self.root / "tailwind.config.ts").is_file()

    def detect_zod(self) -> bool:
        return "zod" in self.js_deps or "@zod-validation" in self.js_deps

    def detect_uv(self) -> bool:
        return (self.root / "uv.lock").is_file()

    # ── Phase 4: Decision matrix ───

    def decide(self) -> dict[str, Any]:
        self.scan_deps()

        has_mcp = self.sniff_mcp()
        has_fastapi = self.sniff_fastapi()
        has_flask = self.sniff_flask()
        has_frontend = self.sniff_frontend()
        has_nextjs = self.sniff_nextjs() if has_frontend else False

        has_godot = (self.root / "project.godot").is_file()
        has_mlflow = "mlflow" in self.py_deps or (self.root / "mlruns").is_dir()
        has_langgraph = "langgraph" in self.py_deps

        # Profile selection: one archetype per project. A full-stack app is
        # `web` even if it also exposes MCP endpoints; agent systems take
        # precedence over a bare MCP server.
        if has_godot:
            profile = "godot"
        elif has_fastapi and has_frontend:
            profile = "web"
        elif has_langgraph or has_mlflow:
            profile = "agent"
        elif has_mcp:
            profile = "mcp"
        elif has_frontend:
            profile = "web"
        else:
            profile = "python"

        # Mode selection
        if has_frontend:
            mode = "full"
        else:
            mode = "backend-only"

        # Python version
        python_version = self.py_deps.get("python")
        if not python_version:
            # Check .python-version, Dockerfile, or pyenv
            pv = self.root / ".python-version"
            if pv.is_file():
                python_version = read_text(pv).strip().splitlines()[0]
        if not python_version:
            python_version = "3.12"
        # Clean trailing dots (e.g. "3.12." -> "3.12")
        if isinstance(python_version, str):
            python_version = python_version.rstrip(".")

        # FastAPI version
        fastapi_version = self.py_deps.get("fastapi")
        if not fastapi_version:
            fastapi_version = "0.119+"

        # React / TS / Vite versions
        react_version = self.js_deps.get("react") or "19"
        typescript_version = self.js_deps.get("typescript") or "5.9"
        vite_version = self.js_deps.get("vite") or "7.3"

        # State manager
        state_manager = None
        for sm in ("zustand", "redux", "pinia", "jotai", "recoil"):
            if sm in self.js_deps:
                state_manager = sm
                break
        if state_manager is None:
            state_manager = "zustand"

        # Package manager
        uv = self.detect_uv()
        pkg_backend = "uv" if uv else "pip"
        # Frontend package manager: Bun if bun.lockb, otherwise npm
        if (self.root / "bun.lockb").is_file():
            pkg_frontend = "bun"
        else:
            pkg_frontend = "npm"

        # DB
        db_provider = self.detect_db()
        if not db_provider and has_mcp:
            # MCP usually stateless or simple key-value
            db_provider = None

        # E2E
        e2e = self.detect_e2e()

        # ML / Lang infra
        has_mlflow = "mlflow" in self.py_deps or (self.root / "mlruns").is_dir()
        has_langgraph = "langgraph" in self.py_deps

        # Tailwind & Zod (frontend only)
        tailwind = self.detect_tailwind() if has_frontend else False
        zod_val = self.detect_zod() if has_frontend else False

        def _clean_python_ver(v: str) -> str:
            parts = v.split(".")
            return ".".join(parts[:2]) if len(parts) >= 2 else v

        output: dict[str, Any] = {
            "mode": mode,
            "profile": profile,
            "project_name": self.root.name,
            "project_slug": re.sub(r"[^a-z0-9]", "", self.root.name.lower()),
            "python_version": _clean_python_ver(python_version) if python_version else "3.12",
            "fastapi_version": fastapi_version if has_fastapi else None,
            "react_version": react_version if has_frontend else None,
            "typescript_version": typescript_version if has_frontend else None,
            "vite_version": vite_version if has_frontend else None,
            "db_provider": db_provider,
            "state_manager": state_manager if has_frontend else None,
            "pkg_manager_backend": pkg_backend,
            "pkg_manager_frontend": pkg_frontend if has_frontend else None,
            "test_backend_cmd": f"{pkg_backend} run pytest" if uv else "pytest",
            "test_frontend_cmd": (
                "bun test" if pkg_frontend == "bun" else "npx vitest run"
            ) if has_frontend else None,
            "db_extensions": [],
            "has_mlflow": has_mlflow,
            "has_langgraph": has_langgraph,
            "has_nextjs": has_nextjs,
            "tailwind": tailwind,
            "zod_validation": zod_val,
            "cicd_platform": self.detect_ci(),
            "e2e_tool": e2e,
            "ui_library": "shadcn/ui" if (has_frontend and "radix-ui" in self.js_deps) else "shadcn/ui",
            "confidence": self.confidence,
        }

        # Clean nulls for brevity
        output = {k: v for k, v in output.items() if v is not None}
        return output


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 inspect-project.py <project_root>", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 1

    inspector = ProjectInspector(root)
    result = inspector.decide()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
