---
read_when: "Adding performance-sensitive code or budgets"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - "{{FRONTEND_PATH}}/vite.config.ts"
  - "{{FRONTEND_PATH}}/package.json"
  - ".github/workflows/**"
---

# Performance Budgets & SLOs

## MUST

### Backend Latency Budgets

| Endpoint Category | p50 Target | p95 Target | p99 Target |
|-------------------|-----------|-----------|-----------|
| Auth (login, token refresh) | ≤100ms | ≤300ms | ≤500ms |
| Read (list, get) | ≤50ms | ≤200ms | ≤500ms |
| Write (create, update) | ≤100ms | ≤300ms | ≤800ms |
| Search / filter | ≤200ms | ≤500ms | ≤1000ms |
| Report / analytics | ≤500ms | ≤2000ms | ≤5000ms |
| External API call | — | ≤3000ms | ≤5000ms |

- Every new endpoint MUST include p95 latency test in CI
- Performance regression: merge blocked if p95 exceeds baseline by >20%

### Frontend Bundle Budgets

| Metric | Budget | CI Gate |
|--------|--------|---------|
| Initial JS bundle | ≤200KB (gzipped) | FAIL >250KB |
| Total JS (async chunks) | ≤500KB (gzipped) | WARN >500KB, FAIL >800KB |
| CSS | ≤50KB (gzipped) | FAIL >100KB |
| Largest Contentful Paint (LCP) | ≤2.5s | FAIL >4s |
| First Input Delay (FID / INP) | ≤200ms | FAIL >500ms |
| Cumulative Layout Shift (CLS) | ≤0.1 | FAIL >0.25 |

- Bundle analyzer (`npx vite-bundle-visualizer`) MUST be runnable locally
- CI MUST report bundle size delta per PR

### Database Query Budgets
- Every DB query MUST have a timeout: `statement_timeout = '5s'` in production
- N+1 queries are BLOCKING; use `select_related` / `prefetch_related` patterns or Supabase bulk fetch
- Full table scans are BLOCKING on tables >10,000 rows without index
- Add query plan review (`EXPLAIN ANALYZE`) for slow query tickets

## SHOULD

- Server-side rendering (SSR) or static generation for public pages (improves LCP)
- Image optimization: WebP/AVIF, lazy loading, responsive srcsets
- Code splitting: per-route lazy loading, vendor chunk separation
- CDN for static assets ( caching headers: `Cache-Control: public, max-age=31536000` for versioned assets)
- Database query caching: Redis/pg-based, with explicit TTL per query category

## ANTI-PATTERNS (BLOCKING)

- No performance tests, no latency measurement in CI
- Bundles growing unbounded (no budget, no monitoring)
- Synchronous loops over unbounded collections in API handlers
- Sending full entity payloads when only IDs or summaries are needed
- Blocking the event loop with CPU-intensive operations inside async handlers
- Loading all rows from a table into memory for "convenience"

## Enforcement Checklist

- [ ] CI performance tests run on every PR (backend latency, frontend bundle size)
- [ ] p95 latency baselines established and regression >20% blocks merge
- [ ] Bundle budget enforced in CI (frontend build fails if budget exceeded)
- [ ] Core Web Vitals monitored in production (RUM or synthetic)
- [ ] Slow query review process documented
