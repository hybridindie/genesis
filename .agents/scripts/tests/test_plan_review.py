"""Tests for plan_review.py with a fake `opencode` on PATH (no model, no network).

Same naming as the other calibration tests: test_accepts_* must succeed,
test_rejects_* must refuse (a failure there means the reviewer is too lax).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "plan_review.py"

# The fake speaks the `opencode run --format json` event stream: one JSON event
# per line, text parts carrying the assistant's answer. FAKE_HEALTH and
# FAKE_REVIEW choose its behaviour: "hang", "fail", "error-event", or the
# answer text (FAKE_REVIEW may be several messages separated by \x1e).
FAKE = r'''#!/usr/bin/env python3
import json, os, sys, time
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
review = "--file" in args
mode = os.environ.get("FAKE_REVIEW" if review else "FAKE_HEALTH", "OK")
if mode == "hang":
    time.sleep(60)
if mode == "fail":
    print("provider reset the connection", file=sys.stderr)
    sys.exit(1)
if mode == "error-event":
    print(json.dumps({"type": "error", "error": {"name": "APIError", "data": {"message": "boom"}}}))
    sys.exit(0)
for n, msg in enumerate(mode.split("\x1e")):
    mid = f"msg_{n}"
    print(json.dumps({"type": "step_start", "part": {"messageID": mid, "type": "step-start"}}))
    half = len(msg) // 2
    for chunk in (msg[:half], msg[half:]):
        print(json.dumps({"type": "text", "part": {"messageID": mid, "type": "text", "text": chunk}}))
    print(json.dumps({"type": "step_finish", "part": {"messageID": mid, "type": "step-finish", "reason": "stop"}}))
'''

STORY = "Part of #1\n\n```yaml agent-plan\nversion: 1\nkind: story\nstory: S1\n```\n"
EPIC = "# Epic\n\n```yaml agent-plan\nversion: 1\nkind: epic\nepic: '#1'\n```\n"
NEEDS_WORK = json.dumps({"verdict": "needs-work", "findings": [
    "S1 owns app/** and S2 owns app/api.py: ownership overlaps",
    "AC3 has no story"]})


@pytest.fixture
def env(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "opencode"
    fake.write_text(FAKE.replace("/usr/bin/env python3", sys.executable, 1))
    fake.chmod(0o755)
    e = dict(os.environ)
    e["PATH"] = f"{bin_dir}{os.pathsep}{e['PATH']}"
    e["FAKE_LOG"] = str(tmp_path / "calls.jsonl")
    e.pop("PLAN_REVIEW_MODEL", None)
    return e


def plan(tmp_path, text=STORY, name="plan.md"):
    p = tmp_path / name
    p.write_text(text)
    return p


def run(env, *args, **fake):
    e = dict(env)
    e.update(fake)
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], env=e,
                          capture_output=True, text=True, timeout=60, check=False)
    return proc.returncode, json.loads(proc.stdout)


def calls(env):
    path = Path(env["FAKE_LOG"])
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


# --- AC7 -------------------------------------------------------------------

def test_accepts_needs_work_with_two_findings(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=NEEDS_WORK)
    assert code == 1
    assert out["verdict"] == "needs-work"
    assert out["findings"] == json.loads(NEEDS_WORK)["findings"]
    assert out["model"] == "nvidia/nvidia/nemotron-3-ultra-550b-a55b"


def test_rejects_ready_when_health_check_fails(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_HEALTH="fail",
                    FAKE_REVIEW=json.dumps({"verdict": "ready", "findings": []}))
    assert code == 3
    assert out["verdict"] != "ready"
    assert "health check failed" in out["error"]
    assert len(calls(env)) == 1  # the review is never sent


def test_rejects_ready_when_health_check_hangs(env, tmp_path):
    start = time.monotonic()
    code, out = run(env, plan(tmp_path), "--health-timeout", "1", FAKE_HEALTH="hang")
    assert code == 3 and out["verdict"] != "ready"
    assert "timed out" in out["error"]
    assert time.monotonic() - start < 30


def test_rejects_ready_when_review_exceeds_timeout(env, tmp_path):
    start = time.monotonic()
    code, out = run(env, plan(tmp_path), "--timeout", "1", FAKE_REVIEW="hang")
    assert code == 3 and out["verdict"] != "ready"
    assert "timed out" in out["error"]
    assert time.monotonic() - start < 30


# --- verdicts ----------------------------------------------------------------

def test_accepts_ready(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW='{"verdict": "ready", "findings": []}')
    assert (code, out["verdict"], out["findings"]) == (0, "ready", [])


def test_accepts_blocked(env, tmp_path):
    code, out = run(env, plan(tmp_path),
                    FAKE_REVIEW='{"verdict": "blocked", "findings": ["Which tracker? A human must pick."]}')
    assert (code, out["verdict"]) == (2, "blocked")


def test_accepts_verdict_in_prose_and_fence(env, tmp_path):
    answer = "Here is my review.\n\n```json\n" + NEEDS_WORK + "\n```\nHope that helps {really}."
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer)
    assert code == 1 and len(out["findings"]) == 2


def test_accepts_only_the_final_assistant_message(env, tmp_path):
    early = '{"verdict": "ready", "findings": []}'
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=early + "\x1e" + NEEDS_WORK)
    assert code == 1 and out["verdict"] == "needs-work"


# --- couldn't review -----------------------------------------------------------

@pytest.mark.parametrize("answer", [
    "Looks good to me!",
    '{"verdict": "great", "findings": []}',
    '{"verdict": "needs-work", "findings": "fix it"}',
    '{"verdict": "needs-work", "findings": []}',
    '{"verdict": "ready", "findings": [',
])
def test_rejects_unparseable_answer(env, tmp_path, answer):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer)
    assert code == 3 and out["verdict"] == "unreviewed"


@pytest.mark.parametrize("mode", ["fail", "error-event"])
def test_rejects_failed_review_run(env, tmp_path, mode):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=mode)
    assert code == 3 and out["verdict"] == "unreviewed"


def test_rejects_missing_plan_file(env, tmp_path):
    code, out = run(env, tmp_path / "nope.md")
    assert code == 3 and "not found" in out["error"]
    assert calls(env) == []


def test_rejects_usage_error_without_exit_2(env, tmp_path):
    code, out = run(env, plan(tmp_path), "--timeout", "soon")
    assert code == 3 and out["verdict"] == "unreviewed"


def test_rejects_missing_opencode(env, tmp_path):
    e = dict(env, PATH=str(tmp_path / "empty"))
    code, out = run(e, plan(tmp_path))
    assert code == 3 and out["verdict"] == "unreviewed"


# --- what is sent --------------------------------------------------------------

def test_accepts_read_only_invocation(env, tmp_path):
    p = plan(tmp_path)
    run(env, p, FAKE_REVIEW=NEEDS_WORK)
    health, review = calls(env)
    for args in (health, review):
        assert args[0] == "run"
        assert "--auto" not in args
        assert {"--archived", "--format", "json"} <= set(args)
        assert args[args.index("--model") + 1] == "nvidia/nvidia/nemotron-3-ultra-550b-a55b"
    assert "--file" not in health
    assert review[review.index("--file") + 1] == str(p.resolve())
    prompt = review[1]
    assert '"verdict"' in prompt and "needs-work" in prompt
    assert "Story Quality Pass" in prompt or "story rubric" in prompt.lower()


def test_accepts_every_plan_file_and_both_rubrics(env, tmp_path):
    a, b = plan(tmp_path, EPIC, "epic.md"), plan(tmp_path, STORY, "s1.md")
    run(env, a, b, FAKE_REVIEW=NEEDS_WORK)
    review = calls(env)[-1]
    files = [review[i + 1] for i, x in enumerate(review) if x == "--file"]
    assert files == [str(a.resolve()), str(b.resolve())]
    assert "## Epic rubric" in review[1] and "## Story rubric" in review[1]


def test_accepts_epic_rubric_only_for_an_epic(env, tmp_path):
    run(env, plan(tmp_path, EPIC), FAKE_REVIEW=NEEDS_WORK)
    prompt = calls(env)[-1][1]
    assert "## Epic rubric" in prompt and "## Story rubric" not in prompt


def test_accepts_model_from_env_and_flag(env, tmp_path):
    p = plan(tmp_path)
    _, out = run(env, p, PLAN_REVIEW_MODEL="nvidia/other", FAKE_REVIEW=NEEDS_WORK)
    assert out["model"] == "nvidia/other"
    assert all(c[c.index("--model") + 1] == "nvidia/other" for c in calls(env))
    _, out = run(env, p, "--model", "x/y", PLAN_REVIEW_MODEL="nvidia/other", FAKE_REVIEW=NEEDS_WORK)
    assert out["model"] == "x/y"
