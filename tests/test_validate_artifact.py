"""Calibration tests for validate_artifact.py's acceptance-criteria parsing.

The canonical spellings are the ones the shell templates emit: an epic labels
lines `**AC1:** ...`, a story uses `- [ ] **Given** ...` checkboxes.
"""

from __future__ import annotations

import pytest

from conftest import load

va = load(".agents/scripts/validate_artifact.py", "validate_artifact")


@pytest.mark.parametrize("line", [
    "- [ ] **Given** a report, **when** exported, **then** a PDF downloads.",
    "- **AC1:** **Given** a report, **when** exported, **then** a PDF downloads.",
    "- **AC1:** When a report is exported, then a PDF downloads, so that finance can share it.",
])
def test_accepts_the_shipped_spellings(line):
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


@pytest.mark.parametrize("line", [
    "- [ ] **AC1:** **Given** a report, **when** exported, **then** a PDF downloads.",
    "- [x] Given a report, when exported, then a PDF downloads.",
])
def test_rejects_variants_the_templates_never_emit(line):
    # Not the shipped shape: a labelled checkbox, or a non-bold Given. Pinned so
    # a future parser change is a deliberate decision rather than a surprise.
    assert va.extract_acceptance(line + "\n") == []
