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

VALIDATOR = ROOT / ".agents/scripts/validate_artifact.py"
CASES = ROOT / "tests/evals"


def run(kind: str, name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--kind", kind, str(CASES / f"{name}.md")],
        capture_output=True, text=True,
    )


@pytest.mark.parametrize(("kind", "name"), [("epic", "epic"), ("story", "story")])
def test_golden_artifact_keeps_its_shape(kind, name):
    result = run(kind, name)
    assert result.returncode == 0, result.stderr


def test_every_story_row_cites_a_declared_ac():
    text = (CASES / "epic.md").read_text()
    declared = set(re.findall(r"\*\*(AC\d+):\*\*", text))
    rows = [line for line in text.splitlines() if re.match(r"^\|\s*#\d+\s*\|", line)]
    assert rows, "the epic fixture needs story rows"
    for row in rows:
        cited = set(re.findall(r"AC\d+", row.split("|")[3]))
        assert cited, f"story row cites no AC: {row}"
        assert cited <= declared, f"story row cites an undeclared AC: {row}"


def test_every_ac_is_realized_by_a_story():
    text = (CASES / "epic.md").read_text()
    declared = set(re.findall(r"\*\*(AC\d+):\*\*", text))
    rows = [line for line in text.splitlines() if re.match(r"^\|\s*#\d+\s*\|", line)]
    covered = {ac for row in rows for ac in re.findall(r"AC\d+", row.split("|")[3])}
    assert declared - covered == set(), f"ACs with no story: {sorted(declared - covered)}"


def test_waves_do_not_share_owned_files():
    text = (CASES / "epic.md").read_text()
    waves = re.findall(r"^- Wave \d+: .*?owns (.+)\.$", text, re.MULTILINE)
    assert len(waves) >= 2, "the fixture needs at least two waves"
    owners: dict[str, int] = {}
    for index, owned in enumerate(waves):
        for path in re.findall(r"`([^`]+)`", owned):
            assert path not in owners, f"{path} is owned by two waves ({owners.get(path)} and {index})"
            owners[path] = index


def test_story_declares_what_it_owns_and_does_not():
    text = (CASES / "story.md").read_text()
    files = re.search(r"\*\*Files\*\*\n\n(.+?)\n\n", text, re.DOTALL)
    assert files, "the story fixture needs a Files section"
    assert "Owns" in files.group(1)
    assert "Does not touch" in files.group(1)


@pytest.mark.parametrize(
    "case", sorted((CASES / "behaviour").glob("*/*.md")), ids=lambda p: f"{p.parent.name}/{p.stem}"
)
def test_behavioural_case_is_well_formed(case):
    text = case.read_text()
    assert "## Input" in text, f"{case} has no Input section"
    assert "## Expected properties" in text, f"{case} has no Expected properties section"
    properties = text.split("## Expected properties", 1)[1]
    assert len(re.findall(r"^- ", properties, re.MULTILINE)) >= 2, f"{case} needs checkable properties"
