<!--
  dependency-security-rules.md — Shared dependency security doctrine
  Referenced by: security.md ("Dependency & Configuration Hygiene"),
                 cicd.md (dependency audit gate)
  Rendered into target projects at .claude/rules/doctrine/dependency-security-rules.md
  version: 1.0.0, owner: John D
  Single source of truth for dependency/lockfile/CVE rules. The canonical
  detailed article remains dependency-security.md; this doctrine holds only
  the rules restated across multiple articles.
-->

# Dependency Security Rules

The dependency-hygiene rules referenced by multiple articles live here. The
full article (`dependency-security.md`) holds the detailed MUST/SHOULD/
ANTI-PATTERNS; this file is the short reference other articles cite.

## Core rules (restated from dependency-security.md)

- Prefer actively maintained libraries; audit dependencies for CVEs before
  adoption.
- Validate security-critical config at application startup — reject
  missing/weak secrets in production.
- Lockfiles (`uv.lock`, `package-lock.json`, `pnpm-lock.yaml`) MUST be
  committed; CI MUST verify consistency (`uv sync --locked` or `npm ci`).
- CI MUST run dependency vulnerability scans on every PR; fail on any HIGH
  or CRITICAL CVE with a patched version available.
- Suppressed CVEs require: documented risk acceptance, expiration date,
  and security team sign-off.

## Token lifetime rule

- Access tokens: ≤ 15 min in production.
- Refresh tokens: ≤ 7 d in production.

## How callers use this file

- `security.md` references this instead of restating the
  "Dependency & Configuration Hygiene" subsection.
- `cicd.md` references this for the dependency-audit gate.
- The full detailed article `dependency-security.md` remains the canonical
  long-form reference; this doctrine file is the short cross-referenced
  summary.