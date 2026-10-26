---
read_when: "Adding feature flags, canaries, or rollback paths"
paths:
  - "{{BACKEND_PATH}}/app/**/*.py"
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - ".github/workflows/**"
  - "infra/**"
  - "docs/deploy/**"
---

# Production Safety: Feature Flags, Canary Deployments & Rollbacks

## MUST

### Feature Flags
- All new user-facing features MUST be deployable behind a feature flag
- Feature flag implementation: LaunchDarkly, Unleash, or environment-variable-based toggles (never hardcoded booleans in source)
- Flags MUST have a defined owner, expiration date, and cleanup schedule
- No "permanent" flags without architectural justification (flags older than 90 days trigger a review)
- Default state for new flags: OFF in production, ON in development/testing

### Deployment Gates
- Production deployments require: green CI, green preflight, approval from the code owner (not self-approval for solo changes)
- No direct pushes to `main` — all changes via PR
- Database migrations and application code changes MUST be separable (backward-compatible migrations first, code change second)

### Canary Deployment
- Deploy to a small subset of traffic first (5–10%)
- Monitor error rates, latency p95/p99, and business-critical metrics for a minimum of 15 minutes
- Automatic rollback triggers: error rate > 0.5%, latency p95 > 2x baseline, any SEV-1 alert
- Canary must be promotable or abortable via a single command or button (no manual file edits during an incident)

### Rollback Procedure
- Rollback must complete within 5 minutes of decision
- Database migrations are NOT rolled back; use forward-only migration strategy with compensating migrations if needed
- Application rollback: redeploy previous known-good container/image
- After rollback, create a SEV incident and begin root-cause analysis before attempting another deploy

## SHOULD

- Dark launches: ship code to production but do not expose to users (validate performance, log behavior)
- Traffic shadowing: mirror production traffic to new version and compare outputs without affecting users
- A/B testing framework for controlled feature experiments
- Automated rollback via CI/CD pipeline (GitHub Actions, ArgoCD, or similar)
- Feature flag audit log: who toggled what, when, and with what context

## ANTI-PATTERNS (BLOCKING)

- Deploying without any feature flags (all-or-nothing launches)
- Database migrations that are not backward-compatible with the currently running application version
- Manual production edits via SSH or database console bypassing CI/CD
- Skipping canary for "small" changes (the smallest change can have the biggest blast radius)
- Rollback procedures that require running undocumented commands from memory
- Leaving feature flags in the codebase permanently (flag debt)

## Deployment Checklist

- [ ] Feature flag exists and is OFF by default in production
- [ ] Database migration is backward-compatible
- [ ] Monitoring dashboards are accessible and baseline metrics known
- [ ] Rollback command is documented and tested
- [ ] On-call engineer is aware of the deployment window
- [ ] Post-deployment: watch error rate and latency for 15+ minutes
