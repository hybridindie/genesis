---
read_when: "Adding, upgrading, or auditing a dependency"
---

# Dependencies: Pinned, Audited, Justified

## MUST

- Commit the lockfile. Builds install from the lockfile, never from floating
  ranges.
- Pin runtime floors (`>=x.y,<next-major`) and let the lockfile pin exact
  versions.
- Run an audit (OSV/npm audit/pip-audit) in CI; a known-exploited advisory
  blocks merge.
- New dependencies are justified in the PR: what it does, licence, maintenance
  signal, and why not the standard library.
- Remove unused dependencies; do not ship transitive extras you do not use.
- Never install from an unpinned URL or a git ref in a release path.

## SHOULD

- Prefer the standard library and already-present dependencies.
- Batch routine updates; review majors individually with release notes.
- Check the licence is compatible with the project.

## ANTI-PATTERNS

- Copy-pasting `pip install` output into a manifest.
- `--force`/`--no-deps` to get past a conflict.
- Ignoring a critical advisory "because it works".
- A dependency for a ten-line function.

## Checklist

- [ ] Lockfile updated.
- [ ] Audit clean or documented exception.
- [ ] Licence and maintenance checked.
