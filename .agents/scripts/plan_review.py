#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Ask a second model, through `opencode run`, whether a plan is ready.

  plan_review.py <plan-file>... [--model M] [--health-timeout 30] [--timeout 300]

First a one-line health prompt checks that the model answers at all, within
--health-timeout seconds. Then the review prompt goes out with the plan files
attached (`--file`) and the matching rubric (`.agents/evals/epic-rubric.md`
and/or `story-rubric.md`) inlined, asking for JSON
`{"verdict": "ready"|"needs-work"|"blocked", "findings": [...]}`.

The reviewer only reads: `--auto` is never passed, so it cannot be granted
write or shell permissions.

The model is --model, else $PLAN_REVIEW_MODEL, else
nvidia/nvidia/nemotron-3-ultra-550b-a55b.

Prints JSON `{"verdict", "findings", "model"}` on stdout. Exit codes:
  0 ready   1 needs-work   2 blocked
  3 couldn't review (health check failed, timeout, unparseable answer, bad
    arguments). The verdict is then "unreviewed" and "error" says why; a
    couldn't-review result is never ready.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS = HERE.parent / "evals"
DEFAULT_MODEL = "nvidia/nvidia/nemotron-3-ultra-550b-a55b"
VERDICTS = {"ready": 0, "needs-work": 1, "blocked": 2}
UNREVIEWED = 3

HEALTH_PROMPT = "Reply with exactly: OK"
KIND = re.compile(r"^kind:[ \t]*['\"]?(epic|story)\b", re.MULTILINE)

INSTRUCTION = """\
You are reviewing an implementation plan before any work is dispatched. \
The plan files are attached. Read them only; do not edit anything or run commands.

Judge the plan against the rubric below. A finding is one concrete problem \
the author must fix, naming where it is and what to change.

Answer with one JSON object and nothing else:
{"verdict": "ready" | "needs-work" | "blocked", "findings": ["...", "..."]}

- "ready": the plan can be dispatched as written; findings may be empty.
- "needs-work": the author can fix it; list every finding.
- "blocked": it cannot proceed without a human decision; say which.
"""


class ReviewError(Exception):
    """The plan could not be reviewed (exit 3)."""


class Parser(argparse.ArgumentParser):
    def error(self, message):  # exit 2 means "blocked" here, so usage errors are 3
        raise ReviewError(f"usage: {message}")


def rubrics(plans: list[Path]) -> str:
    kinds: set[str] = set()
    for p in plans:
        kinds.update(KIND.findall(p.read_text(encoding="utf-8")))
    if not kinds:
        kinds = {"epic", "story"}
    parts = []
    for kind in sorted(kinds):
        path = EVALS / f"{kind}-rubric.md"
        if not path.is_file():
            raise ReviewError(f"rubric not found: {path}")
        parts.append(f"## {kind.capitalize()} rubric\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def run_opencode(prompt: str, model: str, files: list[Path], timeout: float) -> str:
    """Run one `opencode run` and return the text of the final assistant message."""
    cmd = ["opencode", "run", prompt, "--archived", "--format", "json", "--model", model]
    for f in files:
        cmd += ["--file", str(f)]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
    except OSError as e:
        raise ReviewError(f"cannot run opencode: {e}") from e
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        proc.communicate()
        raise ReviewError(f"opencode timed out after {timeout:g}s") from None
    events = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    errors = [e for e in events if e.get("type") == "error"]
    if proc.returncode != 0 or errors:
        detail = json.dumps(errors[-1].get("error", errors[-1])) if errors else err.strip()[-500:]
        raise ReviewError(f"opencode failed (exit {proc.returncode}): {detail}")
    texts = [(e.get("part") or {}) for e in events if e.get("type") == "text"]
    texts = [p for p in texts if isinstance(p.get("text"), str)]
    if not texts:
        raise ReviewError("opencode returned no text")
    last = texts[-1].get("messageID")
    return "".join(p["text"] for p in texts if p.get("messageID") == last)


def parse_verdict(text: str) -> tuple[str, list]:
    """Find the reviewer's JSON object in its answer; the last valid one wins."""
    decoder = json.JSONDecoder()
    found = None
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text, m.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "verdict" in obj:
            found = obj
    if found is None:
        raise ReviewError(f"no verdict JSON in the answer: {text.strip()[:300]!r}")
    verdict = found.get("verdict")
    findings = found.get("findings", [])
    if verdict not in VERDICTS:
        raise ReviewError(f"unknown verdict {verdict!r}")
    if not isinstance(findings, list):
        raise ReviewError("findings is not a list")
    if verdict != "ready" and not findings:
        raise ReviewError(f"verdict {verdict} with no findings")
    return verdict, findings


def review(argv: list[str]) -> tuple[dict, int]:
    ap = Parser(prog="plan_review.py", description="Review plan files with a second model.")
    ap.add_argument("plans", nargs="+", metavar="plan-file")
    ap.add_argument("--model", default=os.environ.get("PLAN_REVIEW_MODEL") or DEFAULT_MODEL)
    ap.add_argument("--health-timeout", type=float, default=30)
    ap.add_argument("--timeout", type=float, default=300)
    model = os.environ.get("PLAN_REVIEW_MODEL") or DEFAULT_MODEL
    try:
        args = ap.parse_args(argv)
        model = args.model
        plans = [Path(p).resolve() for p in args.plans]
        missing = [str(p) for p in plans if not p.is_file()]
        if missing:
            raise ReviewError(f"plan file not found: {', '.join(missing)}")
        prompt = f"{INSTRUCTION}\n{rubrics(plans)}\n"
        try:
            if not run_opencode(HEALTH_PROMPT, model, [], args.health_timeout).strip():
                raise ReviewError("empty answer")
        except ReviewError as e:
            raise ReviewError(f"health check failed: {e}") from None
        verdict, findings = parse_verdict(run_opencode(prompt, model, plans, args.timeout))
    except ReviewError as e:
        return {"verdict": "unreviewed", "findings": [], "model": model, "error": str(e)}, UNREVIEWED
    return {"verdict": verdict, "findings": findings, "model": model}, VERDICTS[verdict]


def main(argv: list[str] | None = None) -> int:
    result, code = review(sys.argv[1:] if argv is None else argv)
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
