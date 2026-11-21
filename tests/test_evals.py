"""Deterministic half of the skill evals.

No model calls: the golden artifacts in `tests/evals/` must keep passing the
shipped validators, and the epic must keep satisfying the invariants the
rubrics describe. A skill that stops producing this shape (or a validator that
stops accepting it) fails here.

The behavioural half runs only when a skill body changes — see
`docs/skill-evals.md`.
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

from conftest import ROOT

SCRIPTS = ROOT / ".agents/scripts"
CASES = ROOT / "tests/evals"
GOLDEN = [CASES / "epic.md", CASES / "story.md"]


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True)


@pytest.mark.parametrize("kind", ["epic", "story"])
def test_golden_prose_keeps_its_shape(kind):
    result = run("validate_artifact.py", "--kind", kind, CASES / f"{kind}.md")
    assert result.returncode == 0, result.stderr


def test_golden_plans_pass_the_planner_check():
    # Schema, AC coverage, disjoint ownership between parallel units, Epic <->
    # story consistency, and generated tables in sync: all owned by plan.py.
    result = run("plan.py", "check", "--no-sync", *GOLDEN)
    assert result.returncode == 0, result.stdout + result.stderr


def test_golden_plans_have_parallel_work_to_schedule():
    out = run("plan.py", "check", "--no-sync", *GOLDEN).stdout
    assert "stories wave 2" in out, "the epic fixture needs at least two waves"
    # S2 depends on S1, whose story isn't in the golden set, so its tracks wait
    # rather than appearing in a wave the dispatcher would never run.
    assert "tracks waiting on unplanned stories: S2/api, S2/web" in out
    story = (CASES / "story.md").read_text()
    assert "depends_on: [api]" in story, "the story fixture needs a dependent track"


@pytest.mark.parametrize(
    "case", sorted((CASES / "behaviour").glob("*/*.md")), ids=lambda p: f"{p.parent.name}/{p.stem}"
)
def test_behavioural_case_is_well_formed(case):
    text = case.read_text()
    assert "## Input" in text, f"{case} has no Input section"
    assert "## Expected properties" in text, f"{case} has no Expected properties section"
    properties = text.split("## Expected properties", 1)[1]
    assert len(re.findall(r"^- ", properties, re.MULTILINE)) >= 2, f"{case} needs checkable properties"


FIXTURE = ROOT / ".agents/evals/cases/_fixture/reports-app"


@pytest.mark.parametrize("case", sorted(p.parent.parent for p in (ROOT / ".agents/evals/cases").glob("*/files/backend")),
                         ids=lambda p: p.name)
def test_eval_case_fixture_copies_match_the_source(case):
    """Each case carries its own copy of the app; edit _fixture and re-copy."""
    for part in ("backend", "frontend"):
        src = {p.relative_to(FIXTURE / part): p.read_bytes() for p in (FIXTURE / part).rglob("*") if p.is_file()}
        dst = {p.relative_to(case / "files" / part): p.read_bytes()
               for p in (case / "files" / part).rglob("*") if p.is_file()}
        assert dst == src, f"{case.name}/files/{part} differs from _fixture/reports-app/{part}"
