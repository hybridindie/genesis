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
# answer text (FAKE_REVIEW may be several messages separated by \x1e). FAKE_RETRY,
# when set, is the answer to the second review call (the JSON-only retry).
# FAKE_GARBAGE=1 writes a line of non-UTF-8 bytes before the events.
FAKE = r'''#!/usr/bin/env python3
import json, os, sys, time
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
review = "--file" in args
mode = os.environ.get("FAKE_REVIEW" if review else "FAKE_HEALTH", "OK")
with open(os.environ["FAKE_LOG"]) as log:  # FAKE_RETRY answers the second review call
    if review and "FAKE_RETRY" in os.environ and sum('"--file"' in l for l in log) > 1:
        mode = os.environ["FAKE_RETRY"]
if mode == "hang":
    time.sleep(60)
if mode == "fail":
    print("provider reset the connection", file=sys.stderr)
    sys.exit(1)
if mode == "error-event":
    print(json.dumps({"type": "error", "error": {"name": "APIError", "data": {"message": "boom"}}}))
    sys.exit(0)
if os.environ.get("FAKE_GARBAGE"):
    sys.stdout.flush()
    sys.stdout.buffer.write(b"\xff\xfe not utf-8 \x80\n")
    sys.stdout.buffer.flush()
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
DEFAULT = "opencode/big-pickle"
BLOCKING = ["S1 owns app/** and S2 owns app/api.py: ownership overlaps", "AC3 has no story"]
DEFERRED = ["S2 has no task list", "S1's verify greps too loosely"]


def answer(verdict, blocking=(), deferred=()):
    return json.dumps({"verdict": verdict, "findings":
                       [{"severity": "blocking", "text": t} for t in blocking]
                       + [{"severity": "deferred", "text": t} for t in deferred]})


NEEDS_WORK = answer("needs-work", BLOCKING)
READY = answer("ready")


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
    assert out["findings"] == BLOCKING and out["deferred"] == []
    assert out["model"] == DEFAULT and out["round"] == 1


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
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=READY)
    assert (code, out["verdict"], out["findings"], out["deferred"]) == (0, "ready", [], [])


def test_accepts_ready_with_deferred_findings_attached(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer("ready", deferred=DEFERRED))
    assert (code, out["verdict"], out["findings"], out["deferred"]) == (0, "ready", [], DEFERRED)


def test_accepts_ready_when_needs_work_has_only_deferred_findings(env, tmp_path):
    # Task-level findings never hold a plan back: the verdict follows the blocking ones.
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer("needs-work", deferred=DEFERRED))
    assert (code, out["verdict"], out["deferred"]) == (0, "ready", DEFERRED)


def test_rejects_ready_with_a_blocking_finding(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer("ready", BLOCKING, DEFERRED))
    assert (code, out["verdict"]) == (1, "needs-work")
    assert (out["findings"], out["deferred"]) == (BLOCKING, DEFERRED)


def test_accepts_blocked(env, tmp_path):
    question = ["Which tracker? A human must pick."]
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=answer("blocked", deferred=question))
    assert (code, out["verdict"], out["findings"]) == (2, "blocked", question)


def test_accepts_verdict_in_prose_and_fence(env, tmp_path):
    text = "Here is my review.\n\n```json\n" + NEEDS_WORK + "\n```\nHope that helps {really}."
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=text)
    assert code == 1 and len(out["findings"]) == 2


def test_accepts_only_the_final_assistant_message(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=READY + "\x1e" + NEEDS_WORK)
    assert code == 1 and out["verdict"] == "needs-work"


# --- couldn't review -----------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Looks good to me!",
    '{"verdict": "great", "findings": []}',
    '{"verdict": "needs-work", "findings": "fix it"}',
    '{"verdict": "needs-work", "findings": []}',
    '{"verdict": "ready", "findings": [',
    '{"verdict": ["ready"], "findings": []}',
    '{"verdict": {"ready": 1}, "findings": []}',
    '{"verdict": "needs-work", "findings": [{}]}',
    '{"verdict": "needs-work", "findings": [42]}',
    '{"verdict": "ready", "findings": [null]}',
    '{"verdict": "needs-work", "findings": ["AC3 has no story"]}',
    '{"verdict": "needs-work", "findings": [{"severity": "major", "text": "x"}]}',
    '{"verdict": "needs-work", "findings": [{"severity": "blocking", "text": " "}]}',
])
def test_rejects_unparseable_answer_after_one_retry(env, tmp_path, text):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=text)
    assert code == 3 and out["verdict"] == "unreviewed"
    assert "retry" in out["error"]
    first, retry = calls(env)[1:]
    assert retry[1].startswith(first[1]) and "JSON object only" in retry[1][len(first[1]):]


def test_accepts_a_retry_after_a_truncated_answer(env, tmp_path):
    cut = NEEDS_WORK[: len(NEEDS_WORK) // 2]
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=cut, FAKE_RETRY=READY)
    assert (code, out["verdict"]) == (0, "ready")
    assert len(calls(env)) == 3  # health, review, one retry


@pytest.mark.parametrize("mode", ["fail", "error-event"])
def test_rejects_failed_review_run(env, tmp_path, mode):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=mode, FAKE_RETRY=READY)
    assert code == 3 and out["verdict"] == "unreviewed"
    assert len(calls(env)) == 2  # a failed run is not an answer: no retry


# --- rounds --------------------------------------------------------------------

PRIOR = [{"finding": BLOCKING[0], "answer": "S2 now owns app/api.py only"},
         {"finding": BLOCKING[1]}]


def test_accepts_round_two_with_prior_findings(env, tmp_path):
    code, out = run(env, plan(tmp_path), "--round", "2", "--prior", json.dumps(PRIOR),
                    FAKE_REVIEW=READY)
    assert (code, out["round"]) == (0, 2)
    prompt = calls(env)[-1][1]
    assert "round 2" in prompt and "only if it is blocking" in prompt
    assert f"1. {BLOCKING[0]}\n   Answer: S2 now owns app/api.py only" in prompt
    assert f"2. {BLOCKING[1]}\n   Answer: (none given)" in prompt


def test_accepts_prior_from_a_file(env, tmp_path):
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps(PRIOR))
    code, _ = run(env, plan(tmp_path), "--round", "3", "--prior", prior, FAKE_REVIEW=NEEDS_WORK)
    assert code == 1 and "round 3" in calls(env)[-1][1]


def test_accepts_round_one_without_a_follow_up(env, tmp_path):
    run(env, plan(tmp_path), FAKE_REVIEW=NEEDS_WORK)
    prompt = calls(env)[-1][1]
    assert "Prior findings" not in prompt
    assert '"blocking"' in prompt and '"deferred"' in prompt and "task-decomposer" in prompt


@pytest.mark.parametrize("args", [
    ["--round", "2"],
    ["--prior", json.dumps(PRIOR)],
    ["--round", "0", "--prior", json.dumps(PRIOR)],
    ["--round", "2", "--prior", "[]"],
    ["--round", "2", "--prior", '[{"answer": "done"}]'],
    ["--round", "2", "--prior", "[not json"],
    ["--round", "2", "--prior", "missing.json"],
])
def test_rejects_inconsistent_round_and_prior(env, tmp_path, args):
    code, out = run(env, plan(tmp_path), *args, FAKE_REVIEW=READY)
    assert code == 3 and out["verdict"] == "unreviewed"
    assert calls(env) == []


def test_rejects_non_utf8_plan_file(env, tmp_path):
    p = tmp_path / "plan.md"
    p.write_bytes(b"kind: story\n\xff\xfe caf\xe9\n")
    code, out = run(env, p, FAKE_REVIEW=NEEDS_WORK)
    assert code == 3 and out["verdict"] == "unreviewed"
    assert "cannot read" in out["error"]
    assert calls(env) == []


def test_accepts_non_utf8_opencode_output(env, tmp_path):
    code, out = run(env, plan(tmp_path), FAKE_REVIEW=NEEDS_WORK, FAKE_GARBAGE="1")
    assert code == 1 and out["verdict"] == "needs-work"


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
        assert args[args.index("--model") + 1] == DEFAULT
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
