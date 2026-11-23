"""The plan-and-dispatch pipeline: what of genesis's `.agents/` leaves this repo.

One list, used by templates/scripts/render.py (every rendered project) and
system/agents/stage_skills.py (the user-level install). The pipeline is every
skill under `.agents/skills/` except genesis's own installer, plus the files
those skills read: scripts, doctrine, templates and eval rubrics. Tests,
fixtures and behavioural eval cases stay here. A project's own
`.agents/plan-constraints.yaml` is never part of it.
"""

from __future__ import annotations

from pathlib import Path

GENESIS_ONLY = frozenset({"bootstrap-harness"})
# Folder under .agents/ -> glob of the files that ship from it.
SHARED = {"scripts": "*.py", "doctrine": "*.md", "templates": "**/*", "evals": "*.md"}
SKIP = frozenset({"__pycache__", "fixtures", "cases", "tests"})


def skills(root: Path) -> list[str]:
    """Names of the pipeline skills in genesis at `root`."""
    base = root / ".agents" / "skills"
    return sorted(p.name for p in base.iterdir() if p.is_dir() and p.name not in GENESIS_ONLY)


def _wanted(path: Path, base: Path) -> bool:
    return path.is_file() and path.suffix != ".pyc" and not (SKIP & set(path.relative_to(base).parts))


def shared_files(root: Path) -> list[str]:
    """Shared pipeline files, as paths relative to `.agents/`."""
    src = root / ".agents"
    return [f.relative_to(src).as_posix()
            for tree, pattern in SHARED.items()
            for f in sorted((src / tree).glob(pattern)) if _wanted(f, src)]


def skill_files(root: Path, name: str) -> list[str]:
    """Files of one pipeline skill, relative to its folder."""
    skill = root / ".agents" / "skills" / name
    return [f.relative_to(skill).as_posix() for f in sorted(skill.rglob("*")) if _wanted(f, skill)]
