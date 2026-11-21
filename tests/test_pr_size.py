"""The PR size budget counts what a reviewer has to read, nothing else."""

from __future__ import annotations

import pytest

from conftest import load

size = load("templates/_shared/skills/ship-pr/scripts/pr_size.py", "pr_size")


@pytest.mark.parametrize("path", [
    "uv.lock", "web/package-lock.json", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock",
    "tests/fixtures/report.json", ".agents/evals/cases/x/files/app/main.py",
    ".agents/evals/cases/_fixture/app/main.py", "tests/fixture/data.json",
    "src/__snapshots__/view.test.tsx.snap", "tests/golden/out.txt",
    "vendor/lib/a.go", "web/dist/app.min.js",
])
def test_excludes_what_nobody_reviews_line_by_line(path):
    assert size.excluded(path)


@pytest.mark.parametrize("path", ["src/app.py", "web/src/App.tsx", "tests/test_app.py", "README.md"])
def test_counts_code_tests_and_docs(path):
    assert not size.excluded(path)


def z(*records):
    """Build `git diff --numstat -z` output: renames are 'a\td\t\0old\0new\0'."""
    out = ""
    for r in records:
        if len(r) == 4:
            a, d, old, new = r
            out += f"{a}\t{d}\t\0{old}\0{new}\0"
        else:
            a, d, path = r
            out += f"{a}\t{d}\t{path}\0"
    return out


def test_measures_reviewable_lines_and_files():
    numstat = z(("10", "5", "src/app.py"), ("300", "0", "uv.lock"), ("-", "-", "logo.png"),
                ("2", "1", "tests/test_app.py"))
    m = size.measure(numstat, max_lines=400, max_files=25)
    assert (m["lines"], m["files"], m["excluded_files"]) == (18, 2, 2)
    assert m["within_budget"]


def test_over_budget_names_the_largest_files():
    numstat = z(*[("40", "0", f"src/m{i}.py") for i in range(12)])
    m = size.measure(numstat, max_lines=400, max_files=25)
    assert not m["within_budget"] and m["lines"] == 480
    assert m["largest"][0] == {"path": "src/m0.py", "lines": 40}


def test_too_many_files_is_over_budget_even_when_small():
    numstat = z(*[("1", "0", f"src/m{i}.py") for i in range(26)])
    assert not size.measure(numstat, max_lines=400, max_files=25)["within_budget"]


def test_extra_excludes_apply():
    numstat = z(("500", "0", "docs/api/generated.md"), ("500", "0", "test-data.txt"))
    assert size.measure(numstat, max_lines=400, max_files=25,
                        extra=["docs/api/**", "**/test-data.txt"])["within_budget"]


def test_renames_use_the_destination_and_pure_renames_cost_nothing():
    numstat = z(("0", "0", "src/old.py", "src/new.py"),
                ("4", "1", "tests/data.json", "tests/fixtures/data.json"),
                ("3", "2", "src/a.py", "src/pkg/a.py"))
    m = size.measure(numstat, max_lines=400, max_files=25)
    assert (m["lines"], m["files"]) == (5, 1)
    assert m["largest"] == [{"path": "src/pkg/a.py", "lines": 5}]


def test_any_failure_is_exit_2_with_an_error(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise FileNotFoundError("git")
    monkeypatch.setattr(size.subprocess, "run", boom)
    monkeypatch.setattr(size.sys, "argv", ["pr_size.py"])
    assert size.main() == 2
    assert "error" in capsys.readouterr().out
