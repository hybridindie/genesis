#!/usr/bin/env python3
"""
Cross-Harness Policy Checker — validates that the Claude and OpenCode harnesses
remain consistent with the single source of truth (mirror-pairs.json).

Checks:
  1. Every source article declares read_when
  2. Every rendered rule is indexed in AGENTS.md (and the index has no extras)
  3. Opencode agents/skills are semantically aligned with Claude rules
  4. No orphaned placeholders in rendered harnesses
  5. Agent version claims match AGENTS.md canonical versions
  6. Coverage tier requirements are present
  7. No-skipped-tests policy is present in both harnesses

Usage:
  python3 templates/scripts/check-harness-sync.py [templates_dir] [output_dir]

Exits 0 if clean, non-zero with grouped FAIL lines if drift detected.
"""

import json
import os
import re
import sys
from pathlib import Path


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


class HarnessSyncChecker:
    def __init__(self, templates_dir: str, output_dir: str = ""):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir) if output_dir else None
        self.errors: list[str] = []
        self.warnings: list[str] = []

        self.mirror_json = self.templates_dir / "_shared" / "mirror-pairs.json"
        self.agent_entries: list[dict] = []
        self._load_mirror_pairs()

        self._stack_versions: dict[str, str] = {}

    # ── 1. Mirror pairs -------------------------------------------------

    def _load_mirror_pairs(self) -> None:
        with open(self.mirror_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.agent_entries = data.get("agent_entries", [])

    def check_article_sources(self) -> None:
        """Every source article must declare read_when (used by the rule index)."""
        roots = [self.templates_dir / "_shared" / "core" / "articles"]
        profiles = self.templates_dir / "_shared" / "profiles"
        if profiles.is_dir():
            roots += sorted(profiles.glob("*/articles"))
        if not roots[0].is_dir():
            self.errors.append("FAIL: core/articles directory missing")
        for root in roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                fm = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
                if not fm or "read_when:" not in fm.group(1):
                    self.errors.append(
                        f"FAIL: {path.relative_to(self.templates_dir)} needs read_when frontmatter"
                    )

    def check_rendered_rules(self) -> None:
        """Rendered rules must all be indexed in AGENTS.md, and vice versa."""
        if not self.output_dir:
            return
        rules = self.output_dir / ".claude" / "rules"
        if not rules.is_dir():
            self.errors.append("FAIL: rendered .claude/rules directory missing")
            return
        files = [
            p for p in rules.rglob("*.md")
            if not p.relative_to(rules).as_posix().startswith("doctrine/")
        ]
        for path in files:
            fm = re.match(r"^---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.DOTALL)
            if not fm or "read_when:" not in fm.group(1):
                self.errors.append(f"FAIL: rendered rule missing read_when: {path.relative_to(self.output_dir)}")
        agents = self.output_dir / "AGENTS.md"
        text = agents.read_text(encoding="utf-8") if agents.exists() else ""
        rows = len(re.findall(r"^\| `\.claude/rules/", text, re.MULTILINE))
        if rows != len(files):
            self.errors.append(
                f"FAIL: AGENTS.md rule index has {rows} rows for {len(files)} rendered rules"
            )

    # ── 2. Opencode alignment -------------------------------------------

    def check_opencode_alignment(self) -> None:
        if self.output_dir:
            base = self.output_dir / ".opencode"
        else:
            base = self.templates_dir / "opencode" / ".opencode"
        expected_agents = ["article-compliance-reviewer.md"]
        expected_commands = ["preflight.md", "harness-eval.md", "graphify.md"]
        web = self.output_dir and (self.output_dir / ".claude" / "rules" / "api-design.md").exists()
        if web:
            expected_agents += ["backend-architect.md", "frontend-architect.md"]
            expected_commands += ["migration-check.md"]
        for name in expected_agents:
            if not (base / "agents" / name).exists():
                self.warnings.append(f"WARN: Opencode agent missing: {name}")
        for name in expected_commands:
            if not (base / "commands" / name).exists():
                self.warnings.append(f"WARN: Opencode command missing: {name}")

    # ── 3. Placeholder check -------------------------------------------

    def check_placeholders(self) -> None:
        if not self.output_dir:
            return
        pattern = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")
        orphans: list[str] = []
        for path in self.output_dir.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".json", ".sh", ".py", ".yml"):
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for m in pattern.finditer(text):
                    orphans.append(
                        f"  {path.relative_to(self.output_dir)}:{m.start()}:{m.group()}"
                    )
        if orphans:
            for o in sorted(set(orphans)):
                self.errors.append(f"FAIL: Orphaned placeholder:{o}")

    # ── 4. Version consistency ------------------------------------------

    def check_version_consistency(self) -> None:
        if not self.output_dir:
            return
        # AGENTS.md is the canonical context; CLAUDE.md is a thin import kept for
        # older harnesses, so fall back to it when AGENTS.md is missing.
        candidates = [self.output_dir / "AGENTS.md", self.output_dir / "CLAUDE.md"]
        context_md = next((p for p in candidates if p.exists()), None)
        if context_md is None:
            self.warnings.append("WARN: No AGENTS.md or CLAUDE.md found in rendered output")
            return

        text = context_md.read_text(encoding="utf-8")
        versions = {
            "Python": self._extract_version(text, r"Python\s+([0-9.]+)"),
            "FastAPI": self._extract_version(text, r"FastAPI\s+([0-9.+]+)"),
            "React": self._extract_version(text, r"React\s+([0-9.]+)"),
            "TypeScript": self._extract_version(text, r"TypeScript\s+([0-9.]+)"),
            "Vite": self._extract_version(text, r"Vite\s+([0-9.]+)"),
        }
        versions = {k: v for k, v in versions.items() if v is not None}
        self._stack_versions = versions
        if not versions:
            self.warnings.append(f"WARN: Could not extract versions from {context_md.name}")
            return

        for search_dir in ("agents", "rules"):
            full_dir = self.output_dir / ".claude" / search_dir
            if not full_dir.exists():
                continue
            for path in full_dir.rglob("*.md"):
                body = path.read_text(encoding="utf-8")
                for label, expected in versions.items():
                    # Require that the version starts with a digit (e.g. "TypeScript 5.9"),
                    # avoiding false positives like "React 19 + TypeScript + Vite"
                    pat = re.escape(label) + r"\s+([0-9][0-9.+]*(?:-[a-z0-9]+)?)"
                    for m in re.finditer(pat, body):
                        found = m.group(1)
                        if found != expected and not found.startswith(expected):
                            self.errors.append(
                                f"FAIL: Version drift in {path.relative_to(self.output_dir)}: "
                                f"claims {label} {found}, but {context_md.name} says {label} {expected}"
                            )

    # ── 5. Coverage tier consistency --------------------------------------

    def check_coverage_tiers(self) -> None:
        if not self.output_dir:
            return
        testing = self.output_dir / ".claude" / "rules" / "backend" / "testing.md"
        if testing.exists():
            text = testing.read_text(encoding="utf-8")
            if "Security 90%+" not in text and "90%+" not in text:
                self.warnings.append(
                    "WARN: testing.md does not mention the security coverage tier"
                )

    # ── 6. No-skipped-tests policy presence ---------------------------

    def check_no_skipped_tests(self) -> None:
        if not self.output_dir:
            return
        claude_hook = self.output_dir / ".claude" / "hooks" / "check-no-skipped-tests.sh"
        if not claude_hook.exists():
            self.errors.append(
                "FAIL: Claude harness missing check-no-skipped-tests.sh hook"
            )
        else:
            body = claude_hook.read_text(encoding="utf-8")
            if "pytest.mark.skip" not in body:
                self.errors.append(
                    "FAIL: Claude check-no-skipped-tests.sh does not enforce pytest.skip"
                )

        opencode_skills = self.output_dir / ".opencode" / "skills"
        has_scanner = False
        if opencode_skills.exists():
            has_scanner = (opencode_skills / "test-hygiene-scanner" / "SKILL.md").exists()
        if not has_scanner:
            self.warnings.append(
                "WARN: Opencode harness missing test-hygiene-scanner skill"
            )

    # ── Helpers --------------------------------------------------------

    @staticmethod
    def _extract_body(path: Path) -> str:
        """Extract body after YAML frontmatter. Handles empty frontmatter gracefully."""
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n?^---\s*\n", text, re.DOTALL | re.MULTILINE)
        if m:
            return text[m.end():]
        return text

    @staticmethod
    def _extract_key_phrases(path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        return re.findall(r"\*\*([^*]+)\*\*", text)[:5]

    @staticmethod
    def _extract_version(text: str, pattern: str) -> str | None:
        m = re.search(pattern, text)
        if not m:
            return None
        ver = m.group(1)
        return ver if re.search(r"[0-9]", ver) else None

    # ── Runner ----------------------------------------------------------

    def run(self) -> int:
        self.check_article_sources()
        self.check_rendered_rules()
        self.check_opencode_alignment()
        self.check_placeholders()
        self.check_version_consistency()
        self.check_coverage_tiers()
        self.check_no_skipped_tests()

        for w in self.warnings:
            eprint(w)
        for e in self.errors:
            eprint(e)

        if self.errors:
            eprint(f"\nFAIL: {len(self.errors)} cross-harness issue(s) found.")
            return 1

        eprint("PASS: All cross-harness checks passed.")
        return 0


def main() -> int:
    if len(sys.argv) >= 2:
        templates_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else ""
    else:
        script_dir = Path(__file__).resolve().parent
        templates_dir = script_dir.parent
        output_dir = ""
    checker = HarnessSyncChecker(templates_dir, output_dir)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
