---
read_when: "Setting SLOs or availability targets"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - ".github/workflows/**"
  - "infra/monitoring/**"
---

# Error Budgets & Service Level Objectives (SLOs)

## MUST

### Availability SLO
| Tier | Target | Measurement Window |
|------|--------|-------------------|
| Critical (auth, payments) | 99.99% (52.6 min downtime/year) | 30 days |
| Standard (business logic) | 99.9% (8.8 hours downtime/year) | 30 days |
| Best-effort (reports, exports) | 99.0% (7.3 hours downtime/month) | 30 days |

- Measured from external probe (synthetic monitoring), not internal metrics
- Downtime: any 5-minute window where >5% of requests return 5xx or time out

### Error Budget
- Error budget = 100% - SLO target (e.g., 99.9% SLO = 0.1% error budget)
- Burned when: 5xx responses, timeouts (no response in 30s), incorrect responses (valid 200 but wrong data)
- Alerting: burn rate > 2x (14.4 hours to exhaust) = page
- Alerting: burn rate > 1x (30 days to exhaust) = ticket/Slack notification

### Latency SLO
| Tier | p50 | p95 | p99 |
|------|-----|-----|-----|
| Critical | ≤50ms | ≤200ms | ≤500ms |
| Standard | ≤100ms | ≤500ms | ≤1000ms |
| Best-effort | ≤500ms | ≤2000ms | ≤5000ms |

### Incident Severity Classification

| Level | Criteria | Response |
|-------|----------|----------|
| SEV-1 | Complete outage, data loss, security breach, revenue-critical failure | Immediate page, all-hands |
| SEV-2 | Major feature degraded, partial outage, significant customer impact | Respond within 30 min |
| SEV-3 | Minor feature degraded, workarounds exist, low customer impact | Respond within 4 hours |
| SEV-4 | Cosmetic issue, monitoring gap, documentation error | Next business day |

- Every SEV-1 and SEV-2 MUST have a post-mortem within 48 hours
- Post-mortem format: Timeline, Root Cause, Impact, Mitigation, Prevention, Action Items with owners
- Blameless culture: focus on system failure, not individual fault

## SHOULD

- Service level indicators (SLIs) derived from user journeys, not just infrastructure metrics
- Multi-window burn rate alerts (short window + long window to reduce false positives)
- Automated rollback on SEV-1 triggers
- Error budget pause during planned maintenance windows
- Quarterly SLO review: are targets too tight (unactionable noise) or too loose (no incentive)?

## ANTI-PATTERNS (BLOCKING)

- No SLOs defined (impossible to know what "good" looks like)
- SLOs defined but never measured or alerted on (decorative SLOs)
- Alerting on symptoms instead of user-impacting metrics (CPU >90% is not a SLO; slow login is)
- Ignoring error budget exhaustion and continuing to ship new features
- Retaliatory post-mortems that assign blame instead of identifying system improvements

## Enforcement Checklist

- [ ] Availability and latency SLOs defined per service tier
- [ ] Error budget tracking dashboard accessible
- [ ] Burn rate alerts configured (2x = page, 1x = ticket)
- [ ] Incident severity classification documented and used
- [ ] Post-mortem required for SEV-1 and SEV-2 within 48 hours
- [ ] No new feature launches when error budget is exhausted
