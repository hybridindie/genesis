#!/usr/bin/env python3
"""
Cross-Harness Policy Checker — validates that Claude, Copilot, and Opencode
harnesses remain consistent with the single source of truth (mirror-pairs.json).

Checks:
  1. All mirrors from mirror-pairs.json have a shared source file
  2. Mirror bodies are byte-for-byte identical (excl. frontmatter)
  3. Opencode agents/skills are semantically aligned with Claude rules
  4. No orphaned placeholders in rendered harnesses
  5. Agent version claims match AGENTS.md canonical versions
  6. Coverage tier requirements are consistent across harnesses
  7. No-skipped-tests policy is present in all three harnesses

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
        self.entries: list[dict] = []
        self.pairs: dict[str, dict] = {}
        self._load_mirror_pairs()

        self._stack_versions: dict[str, str] = {}

    # ── 1. Mirror pairs -------------------------------------------------

    def _load_mirror_pairs(self) -> None:
        with open(self.mirror_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.entries = data.get("entries", [])
        for entry in self.entries:
            self.pairs[entry["claude_file"]] = entry

    def _find_shared_source(self, rel_path: str) -> Path | None:
        """Map output path under .claude/rules/ to shared source under templates/_shared/."""
        shared_dir = self.templates_dir / "_shared"
        direct = shared_dir / rel_path
        if direct.is_file():
            return direct
        # Most articles live under articles/<flat> e.g. articles/enforcement.md
        basename = Path(rel_path).name
        for sub in ("articles", "database", "frontend"):
            candidate = shared_dir / sub / rel_path
            if candidate.is_file():
                return candidate
            candidate = shared_dir / sub / basename
            if candidate.is_file():
                return candidate
        for candidate in shared_dir.rglob(basename):
            if candidate.is_file():
                return candidate
        return None

    def check_mirrors_exist(self) -> None:
        """Check that every entry in mirror-pairs.json has a shared source file."""
        for entry in self.entries:
            src = self._find_shared_source(entry["claude_file"])
            if src is None:
                self.errors.append(
                    f"FAIL: Missing shared source for {entry['title']}: {entry['claude_file']}"
                )

    def check_rendered_mirrors(self) -> None:
        """If output_dir is given, verify mirrored files exist and bodies match."""
        if not self.output_dir:
            return
        for entry in self.entries:
            claude_path = self.output_dir / ".claude" / "rules" / entry["claude_file"]
            copilot_path = (
                self.output_dir
                / ".github"
                / "instructions"
                / entry["copilot_file"]
            )

            for path, side in [(claude_path, "claude"), (copilot_path, "copilot")]:
                if not path.exists():
                    self.errors.append(
                        f"FAIL: Missing rendered {side} mirror: {path}"
                    )

            if claude_path.exists() and copilot_path.exists():
                claude_body = self._extract_body(claude_path)
                copilot_body = self._extract_body(copilot_path)
                if claude_body != copilot_body:
                    self.errors.append(
                        f"FAIL: Body drift detected between .claude/rules/{entry['claude_file']} "
                        f"and .github/instructions/{entry['copilot_file']}"
                    )

    # ── 2. Opencode alignment -------------------------------------------

    def check_opencode_alignment(self) -> None:
        opencode_dir = self.output_dir or self.templates_dir / "opencode"
        for name in ("backend-architect.md", "frontend-architect.md"):
            path = opencode_dir / "agents" / name
            if not path.exists():
                self.warnings.append(f"WARN: Opencode agent missing: {name}")

        # Semantic sniff: key phrases from first two core articles must appear
        # in at least one Opencode agent file
        if not (self.output_dir and (self.output_dir / ".opencode").exists()):
            return

        agents_dir = self.output_dir / ".opencode" / "agents"
        if not agents_dir.exists():
            return

        for entry in self.entries[:2]:
            src = self._find_shared_source(entry["claude_file"])
            if src is None:
                continue
            phrases = self._extract_key_phrases(src)
            for phrase in phrases:
                found_in_any = False
                for md in agents_dir.glob("*.md"):
                    body = md.read_text(encoding="utf-8")
                    if phrase in body:
                        found_in_any = True
                        break
                if not found_in_any:
                    self.warnings.append(
                        f"WARN: Opencode agents do not reference '{phrase}' "
                        f"from {entry['claude_file']}"
                    )

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
        copilot = self.output_dir / ".github" / "copilot-instructions.md"
        if copilot.exists():
            text = copilot.read_text(encoding="utf-8")
            if "Security 90%+" not in text:
                self.errors.append(
                    "FAIL: Copilot instructions missing Security 90%+ tier"
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

        copilot = self.output_dir / ".github" / "copilot-instructions.md"
        if copilot.exists():
            text = copilot.read_text(encoding="utf-8")
            if "Zero failing tests" not in text:
                self.warnings.append(
                    "WARN: Copilot instructions do not reference no-skipped-tests policy"
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
        self.check_mirrors_exist()
        self.check_rendered_mirrors()
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
