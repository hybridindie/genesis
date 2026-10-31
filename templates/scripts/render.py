#!/usr/bin/env python3
"""Render the genesis harness into a project from composable stacks and packs.

  core            always rendered (rules, shared agents/commands/skills)
  stacks/<id>/    one per detected or requested stack; several per project
  packs/<id>/     opt-in rule packs (production, acd)

Each source dir may hold articles/, agents/, commands/ and skills/. Article
paths must be unique across everything rendered; stacks add rules, they never
replace core ones.

Usage:
  render.py --output-dir DIR [--auto-detect] [--stacks a,b] [--add-stacks x]
            [--remove-stacks y] [--packs p] [--project-name N] [--project-slug S]
            [--python-path P] [--frontend-path P] [--godot-path P] [--rust-path P]
            [--ci-runs-on LABEL] [--no-ci] [--force-ci] [--force-hooks]
            [--plan]

On an existing harness (.claude/harness.json present) the stacks and packs
recorded there are the starting point; --stacks replaces them and
--add-stacks / --remove-stacks adjust them. --plan prints the resolved plan as
JSON and writes nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES = SCRIPT_DIR.parent
SHARED = TEMPLATES / "_shared"
GENESIS = TEMPLATES.parent

STACKS: dict[str, list[str]] = {  # id -> implied stacks
    "python": [],
    "mcp": ["python"],
    "agent": ["python"],
    "fastapi": ["python"],
    "frontend": [],
    "godot": [],
    "godot-addon": ["godot"],
    "rust": [],
}
PACKS = ("production", "acd")
LEGACY_PROFILES = {
    "web": ["fastapi", "frontend"], "fastapi+react": ["fastapi", "frontend"],
    "generic-python": ["python"],
}
TEXT_SUFFIXES = {".md", ".json", ".sh", ".py", ".yml", ".yaml", ".ts", ".toml", ""}
COND = re.compile(r"\{\{#([A-Z0-9_]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)
PLACEHOLDER = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")
TAG_LINE = re.compile(r"^[ \t]*(\{\{[#/][A-Z0-9_]+\}\})[ \t]*\n", re.MULTILINE)


def flag(name: str) -> str:
    return name.upper().replace("-", "_")


def csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


# ── Resolve inputs ────────────────────────────────────────────────────────


def resolve(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.output_dir).resolve()
    manifest_path = out / ".claude" / "harness.json"
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    legacy = manifest.get("schema") == 1  # single-profile harness: re-detect stacks

    detected: dict[str, Any] = {}
    if args.auto_detect or not manifest or legacy:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "inspect-project.py"), str(out)],
            capture_output=True, text=True,
        )
        if proc.returncode == 0:
            detected = json.loads(proc.stdout)

    if args.profile:
        stacks = LEGACY_PROFILES.get(args.profile, [args.profile])
    elif args.stacks is not None:
        stacks = csv(args.stacks)
    elif manifest.get("stacks"):
        stacks = list(manifest["stacks"])
    elif legacy and not detected.get("stacks"):
        profile = manifest.get("profile") or "python"
        stacks = LEGACY_PROFILES.get(profile, [profile])
    else:
        stacks = list(detected.get("stacks") or ["python"])
    stacks += csv(args.add_stacks)
    stacks = [s for s in stacks if s not in set(csv(args.remove_stacks))]
    for s in stacks:
        if s not in STACKS:
            sys.exit(f"ERROR: unknown stack {s!r} (known: {', '.join(STACKS)})")
    for s in list(stacks):
        for implied in STACKS[s]:
            if implied not in stacks:
                stacks.append(implied)
    stacks = [s for s in STACKS if s in stacks]  # canonical order

    packs = csv(args.packs) if args.packs is not None else list(manifest.get("packs") or [])
    for p in packs:
        if p not in PACKS:
            sys.exit(f"ERROR: unknown pack {p!r} (known: {', '.join(PACKS)})")

    paths = {**(manifest.get("paths") or {})}
    for key, value in (detected.get("paths") or {}).items():
        if value and not paths.get(key):
            paths[key] = value
    for key in ("python", "frontend", "godot", "rust"):
        override = getattr(args, f"{key}_path")
        if override:
            paths[key] = override
        paths.setdefault(key, None)
    defaults = {"python": ".", "frontend": "frontend", "godot": ".", "rust": "."}
    for key, stack in (("python", "python"), ("frontend", "frontend"), ("godot", "godot"), ("rust", "rust")):
        paths[key] = (paths[key] or defaults[key]) if stack in stacks else None

    name = args.project_name or manifest.get("project_name") or detected.get("project_name") or out.name
    derived = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = args.project_slug or (derived if args.project_name else None) \
        or manifest.get("project_slug") or detected.get("project_slug") or derived

    return {
        "output_dir": out,
        "updating": bool(manifest),
        "project_name": name,
        "project_slug": slug,
        "stacks": stacks,
        "packs": packs,
        "paths": paths,
        "python": {**(manifest.get("python") or {}), **(detected.get("python") or {})},
        "frontend": {**(manifest.get("frontend") or {}), **(detected.get("frontend") or {})},
        "godot": {**(manifest.get("godot") or {}), **(detected.get("godot") or {})},
        "ci_platform": args.ci_platform or detected.get("ci_platform") or manifest.get("ci_platform") or "github",
        "ci_runs_on": args.ci_runs_on or manifest.get("ci_runs_on") or "ubuntu-latest",
        "has_ci": bool(detected.get("has_ci")),
        "evidence": detected.get("evidence") or {},
        "recorded": manifest.get("files") or {},
        "packs_suggested": detected.get("packs_suggested") or [],
    }


def values(plan: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, str], dict[str, bool]]:
    stacks, paths = plan["stacks"], plan["paths"]
    py, fe, gd = plan["python"], plan["frontend"], plan["godot"]
    py_mgr = args.py_pkg_manager or py.get("pkg_manager") or "uv"
    run = {"uv": "uv run ", "poetry": "poetry run ", "pip": ""}.get(py_mgr, "")
    fe_mgr = fe.get("pkg_manager") or "npm"

    test_roots = []
    if "python" in stacks:
        test_roots.append(f"{paths['python']}/tests" if paths["python"] != "." else "tests")
    if "frontend" in stacks:
        test_roots.append(f"{paths['frontend']}/tests")
    if "godot" in stacks:
        test_roots.append(f"{paths['godot']}/tests" if paths["godot"] != "." else "tests")

    v = {
        "PROJECT_NAME": plan["project_name"],
        "PROJECT_SLUG": plan["project_slug"],
        "BACKEND_PATH": paths["python"] or ".",
        "FRONTEND_PATH": paths["frontend"] or "frontend",
        "GODOT_PATH": paths["godot"] or ".",
        "RUST_PATH": paths["rust"] or ".",
        "PYTHON_VERSION": args.python_version or py.get("version") or "3.12",
        "PY_PKG_MANAGER": py_mgr,
        "PY_TYPE_CHECKER": py.get("type_checker") or "mypy",
        "PY_SYNC_CMD": py.get("sync_cmd") or ("uv sync --locked" if py_mgr == "uv" else "python -m pip install -e ."),
        "LINT_BACKEND_CMD": py.get("lint_cmd") or f"{run}ruff check .",
        "TYPE_BACKEND_CMD": py.get("type_cmd") or f"{run}mypy .",
        "TEST_BACKEND_CMD": py.get("test_cmd") or f"{run}pytest",
        "DB_PROVIDER": args.db_provider or py.get("db_provider") or "Postgres",
        "FRONTEND_STACK": fe.get("stack_summary") or "see package.json",
        "LINT_FRONTEND_CMD": fe.get("lint_cmd") or "npm run lint",
        "TYPE_FRONTEND_CMD": fe.get("type_cmd") or "npx tsc --noEmit",
        "TEST_FRONTEND_CMD": fe.get("test_cmd") or "npm test",
        "GODOT_VERSION": gd.get("version") or "4",
        "GODOT_TEST_CMD": gd.get("test_cmd") or "godot --headless --script res://tests/run_tests.gd",
        "TEST_ROOTS": " ".join(test_roots) or "tests",
        "CI_RUNS_ON": plan["ci_runs_on"],
        "CUSTOM_INSTRUCTIONS": args.custom_instructions or "",
        "CUSTOM_TECH_STACK": args.custom_tech_stack or "",
    }
    flags = {f"STACK_{flag(s)}": s in stacks for s in STACKS}
    flags |= {f"PACK_{flag(p)}": p in plan["packs"] for p in PACKS}
    flags |= {
        "HAS_MLFLOW": bool(py.get("has_mlflow")),
        "HAS_LANGGRAPH": bool(py.get("has_langgraph")),
        "PY_UV": py_mgr == "uv",
        "PY_PIP": py_mgr != "uv",
        "FE_NPM": fe_mgr == "npm",
        "FE_PNPM": fe_mgr == "pnpm",
        "FE_BUN": fe_mgr == "bun",
        "FE_VITEST": (fe.get("unit_runner") or "vitest") == "vitest",
        "FE_JEST": fe.get("unit_runner") == "jest",
        "PY_IN_SUBDIR": (paths["python"] or ".") != ".",
        "GODOT_IN_SUBDIR": (paths["godot"] or ".") != ".",
        "RUST_IN_SUBDIR": (paths["rust"] or ".") != ".",
    }
    return v, flags


# ── Text rendering ────────────────────────────────────────────────────────


def render_text(text: str, v: dict[str, str], flags: dict[str, bool]) -> str:
    # A conditional tag alone on its line takes the line with it.
    text = TAG_LINE.sub(r"\1", text)
    while True:
        new = COND.sub(lambda m: m.group(2) if flags.get(m.group(1)) else "" if m.group(1) in flags
                       else m.group(0), text)
        if new == text:
            break
        text = new
    # A path of "." renders as no prefix: "{{BACKEND_PATH}}/src" -> "src".
    for key in ("BACKEND_PATH", "FRONTEND_PATH", "GODOT_PATH", "RUST_PATH"):
        if v.get(key) == ".":
            text = text.replace("{{%s}}/" % key, "")
    text = PLACEHOLDER.sub(lambda m: v.get(m.group(1), m.group(0)), text)
    return re.sub(r"\n{3,}", "\n\n", text)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Writer:
    """Writes rendered files without clobbering local edits.

    An existing file is replaced only if it is byte-identical to what was
    rendered last time (its hash is recorded in harness.json), or with
    --force-overwrite. Anything else is a local edit and is kept. A recorded
    file that no longer exists was deleted on purpose and is not recreated.
    """

    def __init__(self, out: Path, v: dict[str, str], flags: dict[str, bool], dry: bool,
                 recorded: dict[str, str], force: bool) -> None:
        self.out, self.v, self.flags, self.dry = out, v, flags, dry
        self.recorded, self.force = recorded, force
        self.written: list[str] = []
        self.kept: list[str] = []
        self.deleted: list[str] = []

    def file(self, src: Path, rel: str, mode: int | None = None) -> None:
        dst = self.out / rel
        data = src.read_bytes()
        if src.suffix in TEXT_SUFFIXES:
            try:
                data = render_text(data.decode("utf-8"), self.v, self.flags).encode("utf-8")
            except UnicodeDecodeError:
                pass
        if not dst.exists() and rel in self.recorded and not self.force:
            self.deleted.append(rel)  # rendered before, deleted since: respect it
            return
        if dst.is_file() and not self.force:
            existing = dst.read_bytes()
            if existing != data and self.recorded.get(rel) != sha(existing):
                self.kept.append(rel)
                return
        self.written.append(rel)
        if self.dry:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        if mode is not None or os.access(src, os.X_OK):
            dst.chmod(mode or 0o755)

    def tree(self, src_dir: Path, rel_dir: str) -> None:
        for src in sorted(p for p in src_dir.rglob("*") if p.is_file()):
            if "__pycache__" in src.parts or src.suffix == ".pyc":
                continue
            self.file(src, f"{rel_dir}/{src.relative_to(src_dir).as_posix()}")


# ── Render ────────────────────────────────────────────────────────────────


def sources(plan: dict[str, Any]) -> list[Path]:
    return [SHARED / "core"] + [SHARED / "stacks" / s for s in plan["stacks"]] + \
        [SHARED / "packs" / p for p in plan["packs"]]


def load_script(name: str) -> Any:
    import importlib.util
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Harness content the renderer owns; anything else (CI, git hooks, docs) is never removed.
OWNED_PREFIXES = (".claude/rules/", ".claude/agents/", ".claude/commands/", ".claude/skills/",
                  ".opencode/agents/", ".opencode/commands/", ".opencode/skills/")


def remove_stale(out: Path, recorded: dict[str, str], current: set[str], w: Writer) -> list[str]:
    """Delete files rendered last time but not this time (a removed stack or
    pack, or a rule genesis dropped) if they are unmodified; keep edited ones."""
    removed = []
    for rel, digest in sorted(recorded.items()):
        if rel in current or not rel.startswith(OWNED_PREFIXES):
            continue
        path = out / rel
        if not path.is_file():
            continue
        if sha(path.read_bytes()) == digest:
            removed.append(rel)
            if not w.dry:
                path.unlink()
        else:
            w.kept.append(rel)
    if not w.dry:
        for d in sorted({(out / r).parent for r in removed}, key=lambda p: -len(p.parts)):
            while d != out and d.is_dir() and not any(d.iterdir()):
                d.rmdir()
                d = d.parent
    return removed


def render(plan: dict[str, Any], args: argparse.Namespace) -> tuple[list[str], list[str]]:
    out = plan["output_dir"]
    v, flags = values(plan, args)
    w = Writer(out, v, flags, args.plan, plan["recorded"], args.force_overwrite)

    # Rules: every article path must be unique across core, stacks and packs.
    seen: dict[str, Path] = {}
    for base in sources(plan):
        articles = base / "articles"
        if not articles.is_dir():
            continue
        for src in sorted(articles.rglob("*.md")):
            rel = src.relative_to(articles).as_posix()
            if rel in seen:
                sys.exit(f"ERROR: rule {rel} provided by both {seen[rel]} and {src}")
            seen[rel] = src
            w.file(src, f".claude/rules/{rel}")

    mirror = json.loads((SHARED / "mirror-pairs.json").read_text(encoding="utf-8"))
    for entry in mirror.get("doctrine_entries", []):
        w.file(SHARED / "doctrine" / entry["source_file"], f"{entry['render_dir']}/{entry['source_file']}")

    # Agents, commands and skills: shared first, then stacks and packs.
    for base in [SHARED] + sources(plan)[1:]:
        for kind in ("agents", "commands"):
            d = base / kind
            if d.is_dir():
                for src in sorted(d.glob("*.md")):
                    w.file(src, f".claude/{kind}/{src.name}")
        skills = base / "skills"
        if skills.is_dir():
            for skill in sorted(p for p in skills.iterdir() if p.is_dir()):
                for dest in (".claude/skills", ".opencode/skills"):
                    w.tree(skill, f"{dest}/{skill.name}")

    w.tree(TEMPLATES / "claude-code" / ".claude", ".claude")
    if (out / "opencode.json").is_file() and not (out / ".opencode" / "opencode.json").exists():
        # The project keeps its OpenCode config at the root; don't add a second one.
        print("  Kept root opencode.json (add my-workflows.md to its instructions)", file=sys.stderr)
    else:
        w.tree(TEMPLATES / "opencode" / ".opencode", ".opencode")
    w.file(TEMPLATES / "claude-code" / "CLAUDE.md", "CLAUDE.md")
    w.file(SHARED / "AGENTS.md", "AGENTS.md")
    w.file(GENESIS / "docs" / "harness-eval.md", "docs/harness-eval.md")

    if (out / "my-workflows.md").exists() and not args.force_workflows:
        print("  Kept existing my-workflows.md (use --force-workflows to replace)", file=sys.stderr)
    else:
        w.file(SHARED / "my-workflows.md", "my-workflows.md")

    for src in sorted((SHARED / "githooks").iterdir()):
        if (out / ".githooks" / src.name).exists() and not args.force_hooks:
            print(f"  Kept existing .githooks/{src.name} (use --force-hooks to replace)", file=sys.stderr)
            continue
        w.file(src, f".githooks/{src.name}", 0o755)

    render_ci(plan, args, w)

    if args.plan:
        return w.written, w.kept + w.deleted

    mirrors_written, mirrors_kept, mirrors_same = load_script("generate-harness-mirrors").mirror(
        out, plan["recorded"])
    w.written += mirrors_written + mirrors_same
    w.kept += mirrors_kept
    removed = remove_stale(out, plan["recorded"], set(w.written) | set(w.kept) | set(w.deleted), w)
    subprocess.run([sys.executable, str(SCRIPT_DIR / "generate-rule-index.py"), str(out)], check=True)
    for rel in removed:
        print(f"  Removed {rel} (no longer rendered, unmodified)", file=sys.stderr)

    manifest = {
        "schema": 2,
        "generated_by": "templates/scripts/render.py",
        "project_name": plan["project_name"],
        "project_slug": plan["project_slug"],
        "stacks": plan["stacks"],
        "packs": plan["packs"],
        "paths": plan["paths"],
        "python_version": v["PYTHON_VERSION"] if "python" in plan["stacks"] else None,
        "python": plan["python"] if "python" in plan["stacks"] else {},
        "frontend": plan["frontend"] if "frontend" in plan["stacks"] else {},
        "godot": plan["godot"] if "godot" in plan["stacks"] else {},
        "ci_platform": plan["ci_platform"],
        "ci_runs_on": plan["ci_runs_on"],
        # Hash of each harness file as rendered; a file that still matches is
        # safe to replace on the next render, anything else is a local edit.
        "files": {
            **{rel: plan["recorded"][rel] for rel in w.kept + w.deleted if rel in plan["recorded"]},
            **{rel: sha((out / rel).read_bytes()) for rel in w.written if (out / rel).is_file()},
        },
    }
    path = out / ".claude" / "harness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


    leftovers = []
    for rel in w.written:
        p = out / rel
        if p.suffix in TEXT_SUFFIXES and p.is_file():
            text = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\{\{[#/][A-Z0-9_]+\}\}", text):
                leftovers.append(rel)
    if leftovers:
        sys.exit("ERROR: unresolved conditional blocks in: " + ", ".join(leftovers))
    return w.written, w.kept + w.deleted


def render_ci(plan: dict[str, Any], args: argparse.Namespace, w: Writer) -> None:
    if args.no_ci or plan["ci_platform"] == "none":
        return
    folder = ".gitea/workflows" if plan["ci_platform"] == "gitea" else ".github/workflows"
    target = plan["output_dir"] / folder
    existing = target.is_dir() and any(target.glob("*.y*ml"))
    if existing and not args.force_ci:
        print(f"  Kept existing {folder}/ (use --force-ci to write ci.yml)", file=sys.stderr)
        return
    parts = [(SHARED / "ci" / "base.yml").read_text(encoding="utf-8")]
    for stack, job in (("python", "python"), ("frontend", "frontend"), ("godot", "godot"), ("rust", "rust")):
        if stack in plan["stacks"]:
            parts.append((SHARED / "ci" / "jobs" / f"{job}.yml").read_text(encoding="utf-8"))
    w.written.append(f"{folder}/ci.yml")
    if not w.dry:
        target.mkdir(parents=True, exist_ok=True)
        (target / "ci.yml").write_text(render_text("".join(parts), w.v, w.flags), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--auto-detect", action="store_true")
    ap.add_argument("--stacks")
    ap.add_argument("--add-stacks")
    ap.add_argument("--remove-stacks")
    ap.add_argument("--packs")
    ap.add_argument("--profile", help="legacy single profile (mcp|python|agent|web|godot)")
    ap.add_argument("--project-name")
    ap.add_argument("--project-slug")
    for key in ("python", "frontend", "godot", "rust"):
        ap.add_argument(f"--{key}-path")
    ap.add_argument("--backend-path", dest="python_path", help=argparse.SUPPRESS)
    ap.add_argument("--python-version")
    ap.add_argument("--py-pkg-manager", choices=["uv", "pip", "poetry"])
    ap.add_argument("--db-provider")
    ap.add_argument("--ci-platform", choices=["github", "gitea", "none"])
    ap.add_argument("--ci-runs-on")
    ap.add_argument("--custom-instructions")
    ap.add_argument("--custom-tech-stack")
    ap.add_argument("--no-ci", action="store_true")
    ap.add_argument("--force-ci", action="store_true")
    ap.add_argument("--force-hooks", action="store_true")
    ap.add_argument("--force-workflows", action="store_true")
    ap.add_argument("--force-overwrite", action="store_true",
                    help="replace locally edited harness files instead of keeping them")
    ap.add_argument("--plan", action="store_true", help="print the resolved plan; write nothing")
    args = ap.parse_args()

    plan = resolve(args)
    written, kept = render(plan, args)
    summary = {k: (str(v) if isinstance(v, Path) else v) for k, v in plan.items()
               if k in ("output_dir", "updating", "stacks", "packs", "paths", "evidence", "packs_suggested")}
    if args.plan:
        summary["files"] = len(written)
        summary["kept_local_edits"] = kept
        print(json.dumps(summary, indent=2))
    else:
        print(f"Rendered {len(written)} files: stacks={','.join(plan['stacks'])} "
              f"packs={','.join(plan['packs']) or 'none'} -> {plan['output_dir']}")
        if kept:
            print(f"Kept {len(kept)} locally edited or deleted files (--force-overwrite replaces them):")
            for rel in kept:
                print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
