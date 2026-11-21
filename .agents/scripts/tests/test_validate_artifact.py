"""Calibration tests for validate_artifact.py's acceptance-criteria parsing.

The templates emit `**AC1:** ...` lines in an epic and `- [ ] **Given** ...`
checkboxes in a story. The parser also accepts a labelled checkbox and a plain
Given: agents in the pipeline evals wrote both, and rejecting them failed
correct criteria. This was a deliberate choice; it replaced the stricter pin.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("validate_artifact", HERE.parent / "validate_artifact.py")
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)


@pytest.mark.parametrize("line", [
    "- [ ] **Given** a report, **when** exported, **then** a PDF downloads.",
    "- [ ] **AC1:** **Given** a report, **when** exported, **then** a PDF downloads.",
    "- [ ] **AC1:** Given a report, when exported, then a PDF downloads.",
    "- [x] Given a report, when exported, then a PDF downloads.",
    "- **AC1:** When a report is exported, then a PDF downloads, so that finance can share it.",
])
def test_accepts_common_criterion_spellings(line):
    assert len(va.extract_acceptance(line + "\n")) == 1


def test_accepts_wrapped_given_when_then():
    text = "- [ ] **Given** a report,\n      **when** exported,\n      **then** a PDF downloads.\n"
    (label, body), = va.extract_acceptance(text)
    assert "then" in body and "PDF downloads" in body


@pytest.mark.parametrize("line", [
    "- [ ] Write the export endpoint",
    "- [ ] All acceptance criteria pass",
    "- **Shared contract:** none",
])
def test_rejects_checklist_lines_that_are_not_criteria(line):
    assert va.extract_acceptance(line + "\n") == []


def test_ignores_ac_labels_inside_the_plan_block():
    text = ("- **AC1:** When x, then y.\n- **AC2:** When x, then y.\n- **AC3:** When x, then y.\n\n"
            "```yaml agent-plan\nacs:\n- AC1\n- AC2\n- AC3\nstories:\n- acs:\n  - AC1\n```\n")
    assert va.count_ac(text) == 3
    assert [label for label, _ in va.extract_acceptance(text)] == ["AC1", "AC2", "AC3"]


def test_accepts_a_plan_block_in_a_crlf_file():
    text = "intro\r\n```yaml agent-plan\r\nversion: 1\r\n```\r\n"
    assert va.plan_blocks(text) == []


def test_rejects_an_unclosed_plan_block():
    text = "- **AC1:** When x, then y.\n\n```yaml agent-plan\nacs:\n- AC1\n- AC2\n"
    assert any("not closed" in e for e in va.plan_blocks(text))
