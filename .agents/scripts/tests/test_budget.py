"""End-to-end tests for budget.py against a throwaway git repository.

Same naming as the other calibration tests: test_accepts_* must succeed,
test_rejects_* must refuse (a failure there means the ledger is too lax).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BUDGET = Path(__file__).resolve().parent.parent / "budget.py"


def run(*args, cwd):
    proc = subprocess.run([sys.executable, str(BUDGET), *args], cwd=cwd, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def record(repo, epic, unit, tokens):
    code, out = run("record", "--epic", str(epic), "--unit", unit, "--tokens", str(tokens), cwd=repo)
    assert code == 0, out
    return out


def test_accepts_empty_epic_as_ok_zero(repo):
    code, out = run("status", "--epic", "7", cwd=repo)
    assert code == 0
    assert out == {"used": 0, "limit": 5_000_000, "percent": 0, "state": "ok"}


def test_accepts_warn_at_80_percent(repo):
    record(repo, 7, "S1/A", 3_000_000)
    record(repo, 7, "S1/B", 1_000_000)
    code, out = run("status", "--epic", "7", cwd=repo)
    assert code == 0
    assert out == {"used": 4_000_000, "limit": 5_000_000, "percent": 80, "state": "warn"}


def test_accepts_ok_just_below_80_percent(repo):
    record(repo, 7, "S1/A", 3_999_999)
    _, out = run("status", "--epic", "7", cwd=repo)
    assert out["state"] == "ok" and out["percent"] == 79


def test_accepts_pause_at_limit(repo):
    record(repo, 7, "S1/A", 4_000_000)
    out = record(repo, 7, "S1/B", 1_000_000)
    assert out["state"] == "pause" and out["used"] == 5_000_000
    _, out = run("status", "--epic", "#7", cwd=repo)
    assert out == {"used": 5_000_000, "limit": 5_000_000, "percent": 100, "state": "pause"}


def test_accepts_custom_limit(repo):
    record(repo, 7, "S1/A", 900)
    _, out = run("status", "--epic", "7", "--limit", "1000", cwd=repo)
    assert out == {"used": 900, "limit": 1000, "percent": 90, "state": "warn"}


def test_accepts_epics_kept_apart(repo):
    record(repo, 7, "S1/A", 4_000_000)
    record(repo, 8, "S1/A", 10)
    _, out = run("status", "--epic", "8", cwd=repo)
    assert out["used"] == 10 and out["state"] == "ok"


def test_accepts_reset_clears_only_that_epic(repo):
    record(repo, 7, "S1/A", 100)
    record(repo, 7, "S1/B", 200)
    record(repo, 8, "S1/A", 300)
    code, out = run("reset", "--epic", "7", cwd=repo)
    assert code == 0 and out == {"epic": 7, "removed": 2}
    assert run("status", "--epic", "7", cwd=repo)[1]["used"] == 0
    assert run("status", "--epic", "8", cwd=repo)[1]["used"] == 300


def test_accepts_ledger_in_git_common_dir_shared_by_worktrees(repo):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    wt = repo.parent / (repo.name + "-wt")
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", str(wt)], check=True)
    record(wt, 7, "S1/A", 42)
    ledger = json.loads((repo / ".git" / "agent-plan" / "budget.json").read_text())
    assert [(e["epic"], e["unit"], e["tokens"]) for e in ledger["entries"]] == [(7, "S1/A", 42)]
    assert run("status", "--epic", "7", cwd=repo)[1]["used"] == 42


@pytest.mark.parametrize("args", [
    ["record", "--epic", "7", "--unit", "S1/A", "--tokens", "-5"],
    ["record", "--epic", "7", "--unit", "S1/A", "--tokens", "lots"],
    ["record", "--epic", "abc", "--unit", "S1/A", "--tokens", "5"],
    ["record", "--epic", "7", "--unit", " ", "--tokens", "5"],
    ["record", "--epic", "7", "--tokens", "5"],
    ["status", "--epic", "0"],
    ["status", "--epic", "7", "--limit", "0"],
    ["status"],
    ["reset"],
    ["spend", "--epic", "7"],
])
def test_rejects_bad_input_with_exit_2_and_json(repo, args):
    code, out = run(*args, cwd=repo)
    assert code == 2
    assert out["ok"] is False and out["error"]
    assert not (repo / ".git" / "agent-plan" / "budget.json").exists()


def test_rejects_outside_a_git_repository(tmp_path):
    code, out = run("status", "--epic", "7", cwd=tmp_path)
    assert code == 2 and out["ok"] is False


def test_rejects_corrupt_ledger(repo):
    d = repo / ".git" / "agent-plan"
    d.mkdir()
    (d / "budget.json").write_text("{not json")
    code, out = run("status", "--epic", "7", cwd=repo)
    assert code == 2 and "not valid JSON" in out["error"]


@pytest.mark.parametrize("entry", [
    "x",
    None,
    [7, 5],
    {"tokens": 5},
    {"epic": "7", "tokens": 5},
    {"epic": True, "tokens": 5},
    {"epic": 7},
    {"epic": 7, "tokens": None},
    {"epic": 7, "tokens": "5k"},
    {"epic": 7, "tokens": 5.5},
    {"epic": 7, "tokens": -1},
    {"epic": 7, "tokens": False},
])
@pytest.mark.parametrize("cmd", [
    ["status", "--epic", "7"],
    ["record", "--epic", "7", "--unit", "S1/A", "--tokens", "5"],
    ["reset", "--epic", "7"],
])
def test_rejects_corrupt_ledger_entry_with_exit_2_and_json(repo, entry, cmd):
    d = repo / ".git" / "agent-plan"
    d.mkdir()
    ledger = d / "budget.json"
    good = {"epic": 7, "unit": "S1/A", "tokens": 1}
    text = json.dumps({"version": 1, "entries": [good, entry]})
    ledger.write_text(text)
    code, out = run(*cmd, cwd=repo)
    assert code == 2
    assert out["ok"] is False and "entry 1" in out["error"]
    assert ledger.read_text() == text
