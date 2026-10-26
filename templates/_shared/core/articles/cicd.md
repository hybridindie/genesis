---
read_when: "Changing CI workflows, build steps, caching, or release automation"
---

# CI/CD: One Command, Same Result Everywhere

CI is the contract. If it is not reproducible locally, it is not a gate.

## MUST

- Every gate runnable locally with one documented command (and mirrored in CI).
- Pin tool and action versions; update them deliberately, not implicitly.
- Deterministic builds: lockfiles committed, no floating `latest` in production
  paths, no network-dependent tests in the blocking job.
- Fail on: lint, type errors, failing tests, unchecked skips, secret leaks,
  broken links, and invalid config/manifests.
- Cache only reproducible artifacts (package caches, build caches) and key them
  on the lockfile.
- Releases are tagged and reproducible from a clean checkout.

## SHOULD

- Fast blocking job (< 5 min) + slower nightly/extended job.
- Matrix only where the matrix proves something (OS/runtime floor).
- Upload failure artifacts (logs, screenshots, coverage) on red.
- Concurrency groups to cancel superseded runs.

## ANTI-PATTERNS

- `--no-verify`, skipped hooks, or `|| true` around a gate.
- Secrets echoed to logs or available to fork PRs.
- A gate that only runs on `main`.
- Tests that need a live external service in the blocking job.
- Rebuilding the same artifact per job instead of once and reusing it.

## Checklist

- [ ] Local preflight matches CI.
- [ ] Versions and actions pinned.
- [ ] Red build means a real defect, not flakiness.
