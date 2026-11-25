#!/usr/bin/env python3
"""Run the fixture evals for the skills a branch changes, and fail on a regression.

`claude plugin eval` scores each case (0..1, mean over runs). This script adds
what it does not: picking the cases a diff touches, comparing each score with a
committed baseline, and recording every run in MLflow so scores can be compared
across skill revisions and models.

  python3 scripts/eval-gate.py --base origin/main            # cases for changed skills
  python3 scripts/eval-gate.py --all --runs 5 --update-baseline
  python3 scripts/eval-gate.py --result aggregate-result.json # gate an existing run

Case selection: each case under `.agents/evals/cases/` carries a
`skill:<name>` tag; a changed skill selects its tagged cases.

Gate: a case fails when its score drops more than --tolerance below its
baseline. A case with no baseline is reported, not failed (--strict fails it).
Errored runs (timeouts, API errors) score 0 inside `claude plugin eval`, so an
outage reads as a regression rather than a pass.

MLflow: when `mlflow` is importable, one run per invocation is logged to the
"genesis-skill-evals" experiment ($MLFLOW_TRACKING_URI, else sqlite:///mlflow.db at the repo root) with the
git sha, models, per-case scores and deltas, and the raw result as an artifact.
Without it the gate still runs.

Exit codes: 0 pass (or nothing to run), 1 regression, 2 the eval could not run
or its result is partial (cost ceiling, auth).
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / ".agents/evals/cases"
BASELINE = ROOT / ".agents/evals/baseline.json"
EXPERIMENT = "genesis-skill-evals"
TAG = re.compile(r"^tags:\s*\[(.*)\]\s*$", re.MULTILINE)


def _changed_skills_module():
    spec = importlib.util.spec_from_file_location("changed_skills", ROOT / "scripts/changed-skills.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def case_skills(cases_dir: Path = CASES) -> dict[str, list[str]]:
    """Case name -> the skills its `skill:` tags name."""
    out: dict[str, list[str]] = {}
    for prompt in sorted(cases_dir.glob("*/prompt.md")):
        m = TAG.search(prompt.read_text(encoding="utf-8"))
        tags = [t.strip().strip("'\"") for t in m.group(1).split(",")] if m else []
        out[prompt.parent.name] = [t.split(":", 1)[1] for t in tags if t.startswith("skill:")]
    return out


def select_cases(skills: list[str], mapping: dict[str, list[str]]) -> list[str]:
    wanted = set(skills)
    return sorted(case for case, owners in mapping.items() if wanted & set(owners))


class Verdict:
    def __init__(self, case: str, score: float, baseline: float | None, status: str):
        self.case, self.score, self.baseline = case, score, baseline
        self.status = status  # pass | regressed | no-baseline | missing

    @property
    def delta(self) -> float | None:
        return None if self.baseline is None else round(self.score - self.baseline, 4)


def case_scores(result: dict) -> dict[str, float]:
    """Per-case mean score from aggregate-result.json (documented fields only)."""
    return {c["name"]: float(c["aggregates"]["score"]) for c in result.get("cases", [])}


def gate(scores: dict[str, float], baseline: dict, expected: list[str],
         tolerance: float, strict: bool) -> list[Verdict]:
    base = baseline.get("cases", {})
    verdicts = []
    for case in expected:
        if case not in scores:
            verdicts.append(Verdict(case, 0.0, base.get(case, {}).get("score"), "missing"))
            continue
        score = scores[case]
        ref = base.get(case, {}).get("score")
        if ref is None:
            status = "regressed" if strict else "no-baseline"
        else:
            status = "regressed" if score < ref - tolerance else "pass"
        verdicts.append(Verdict(case, score, ref, status))
    return verdicts


def failed(verdicts: list[Verdict]) -> bool:
    return any(v.status in ("regressed", "missing") for v in verdicts)


def update_baseline(baseline: dict, scores: dict[str, float], meta: dict) -> dict:
    cases = dict(baseline.get("cases", {}))
    for case, score in scores.items():
        cases[case] = {"score": round(score, 4), **meta}
    return {"tolerance_note": baseline.get("tolerance_note", ""), "cases": dict(sorted(cases.items()))}


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "unknown"


def run_eval(skills: list[str], args, out: Path) -> int:
    cmd = ["claude", "plugin", "eval", str(ROOT / ".agents"),
           "--scaffold", "--trust-plugin", "--no-publish",
           "--allow-tools", "Bash", "Write", "Edit",
           "--threshold", "0",  # this script owns the gate
           "--runs", str(args.runs), "--json", str(out)]
    if args.model:
        cmd += ["--model", args.model]
    if args.judge_model:
        cmd += ["--judge-model", args.judge_model]
    if args.max_cost_usd:
        cmd += ["--max-cost-usd", str(args.max_cost_usd)]
    if skills:  # None means every case
        cmd += ["--tag", *(f"skill:{s}" for s in skills)]
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def log_mlflow(result: dict, verdicts: list[Verdict], params: dict, result_path: Path) -> None:
    try:
        import mlflow  # type: ignore
    except ImportError:
        print("mlflow not installed: skipping tracking (pip install mlflow)")
        return
    if not os.environ.get("MLFLOW_TRACKING_URI"):
        # One stable local store per checkout; `mlflow ui --backend-store-uri sqlite:///mlflow.db` reads it.
        mlflow.set_tracking_uri(f"sqlite:///{ROOT / 'mlflow.db'}")
    try:
        _log(mlflow, result, verdicts, params, result_path)
    except Exception as e:  # tracking is a record, never the gate
        print(f"mlflow: logging failed, gate unaffected: {e}")


def _log(mlflow, result: dict, verdicts: list[Verdict], params: dict, result_path: Path) -> None:
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=f"{params['git_sha'][:8]}-{params['selection']}"):
        mlflow.log_params(params)
        agg = result.get("aggregates", {})
        for key in ("overallScore", "casesPassed", "casesTotal"):
            if key in agg:
                mlflow.log_metric(key, float(agg[key]))
        for key in ("costUsd", "durationSeconds"):
            if key in result:
                mlflow.log_metric(key, float(result[key]))
        for v in verdicts:
            mlflow.log_metric(f"score.{v.case}", v.score)
            if v.delta is not None:
                mlflow.log_metric(f"delta.{v.case}", v.delta)
        mlflow.set_tag("gate", "fail" if failed(verdicts) else "pass")
        mlflow.log_artifact(str(result_path))
        print(f"mlflow: logged to experiment {EXPERIMENT} ({mlflow.get_tracking_uri()})")


def report(verdicts: list[Verdict], tolerance: float) -> None:
    print(f"\n{'case':40} {'score':>6} {'base':>6} {'delta':>7}  status  (tolerance {tolerance})")
    for v in verdicts:
        base = "-" if v.baseline is None else f"{v.baseline:.2f}"
        delta = "-" if v.delta is None else f"{v.delta:+.2f}"
        print(f"{v.case:40} {v.score:6.2f} {base:>6} {delta:>7}  {v.status}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sel = p.add_mutually_exclusive_group()
    sel.add_argument("--base", help="git base; run cases for skills changed since it")
    sel.add_argument("--all", action="store_true", help="run every fixture case")
    sel.add_argument("--skill", action="append", help="run cases tagged skill:<name> (repeatable)")
    p.add_argument("--result", type=Path, help="gate an existing aggregate-result.json instead of running")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--model")
    p.add_argument("--judge-model")
    p.add_argument("--max-cost-usd", type=float)
    p.add_argument("--tolerance", type=float, default=0.15,
                   help="allowed drop below baseline (default 0.15: about 2-3 failed checks of ~18 across 3 runs)")
    p.add_argument("--strict", action="store_true", help="fail cases that have no baseline")
    p.add_argument("--baseline", type=Path, default=BASELINE)
    p.add_argument("--update-baseline", action="store_true", help="write these scores as the new baseline")
    args = p.parse_args(argv)

    mapping = case_skills()
    skills: list[str] | None = None
    if args.all or (args.result and not (args.base or args.skill)):
        cases, selection = sorted(mapping), "all"
    else:
        skills = args.skill or _changed_skills_module().changed_skills(args.base or "origin/main")
        cases, selection = select_cases(skills, mapping), ",".join(sorted(skills)) or "none"
        uncovered = sorted(set(skills) - {s for c in cases for s in mapping[c]})
        if uncovered:
            print(f"no fixture case for: {', '.join(uncovered)} (behavioural cases in tests/evals/ stay manual)")
    if not cases:
        print("no fixture cases selected: nothing to gate")
        return 0

    if args.result:
        result_path = args.result
    else:
        result_path = Path(tempfile.mkdtemp(prefix="eval-gate-")) / "aggregate-result.json"
        code = run_eval(skills, args, result_path)
        if not result_path.exists():
            print(f"claude plugin eval exited {code} without a result")
            return 2
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("partial"):
        print(f"partial result ({result.get('partialReason')}): not gating on it")
        return 2

    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {"cases": {}}
    scores = case_scores(result)
    verdicts = gate(scores, baseline, cases, args.tolerance, args.strict)
    report(verdicts, args.tolerance)

    params = {"git_sha": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
              "selection": selection, "runs": args.runs, "model": args.model or "default",
              "judge_model": args.judge_model or "default", "tolerance": args.tolerance,
              "claude_version": result.get("claudeVersion", "unknown")}
    if os.environ.get("EVAL_GATE_NO_MLFLOW") != "1":
        log_mlflow(result, verdicts, params, result_path)

    if args.update_baseline:
        if failed(verdicts):
            print("\nWARNING: writing a baseline over regressed or missing cases; the lower scores become the floor")
        meta = {"runs": args.runs, "model": params["model"], "sha": params["git_sha"][:12],
                "date": dt.date.today().isoformat()}
        args.baseline.write_text(json.dumps(update_baseline(baseline, scores, meta), indent=2) + "\n")
        print(f"baseline updated: {args.baseline.relative_to(ROOT) if args.baseline.is_relative_to(ROOT) else args.baseline}")
        return 0
    if failed(verdicts):
        print("\nFAIL: a skill regressed against its baseline")
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
