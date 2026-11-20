"""Calibration tests for validate_artifact.py's acceptance-criteria parsing."""

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
