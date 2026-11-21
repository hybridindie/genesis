"""The PR size budget counts what a reviewer has to read, nothing else."""

from __future__ import annotations

import pytest

from conftest import load

size = load("templates/_shared/skills/ship-pr/scripts/pr_size.py", "pr_size")


@pytest.mark.parametrize("path", [
    "uv.lock", "web/package-lock.json", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock",
    "tests/fixtures/report.json", ".agents/evals/cases/x/files/app/main.py",
    "src/__snapshots__/view.test.tsx.snap", "tests/golden/out.txt",
    "vendor/lib/a.go", "web/dist/app.min.js",
])
def test_excludes_what_nobody_reviews_line_by_line(path):
    assert size.excluded(path)


@pytest.mark.parametrize("path", ["src/app.py", "web/src/App.tsx", "tests/test_app.py", "README.md"])
def test_counts_code_tests_and_docs(path):
    assert not size.excluded(path)


def test_measures_reviewable_lines_and_files():
    numstat = "10\t5\tsrc/app.py\n300\t0\tuv.lock\n-\t-\tlogo.png\n2\t1\ttests/test_app.py\n"
    m = size.measure(numstat, max_lines=400, max_files=25)
    assert (m["lines"], m["files"], m["excluded_files"]) == (18, 2, 2)
    assert m["within_budget"]


def test_over_budget_names_the_largest_files():
    numstat = "".join(f"{40}\t0\tsrc/m{i}.py\n" for i in range(12))
    m = size.measure(numstat, max_lines=400, max_files=25)
    assert not m["within_budget"] and m["lines"] == 480
    assert m["largest"][0] == {"path": "src/m0.py", "lines": 40}


def test_too_many_files_is_over_budget_even_when_small():
    numstat = "".join(f"1\t0\tsrc/m{i}.py\n" for i in range(26))
    assert not size.measure(numstat, max_lines=400, max_files=25)["within_budget"]


def test_extra_excludes_apply():
    numstat = "500\t0\tdocs/api/generated.md\n"
    assert size.measure(numstat, max_lines=400, max_files=25, extra=["docs/api/**"])["within_budget"]
