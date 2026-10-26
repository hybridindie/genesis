---
read_when: "Adding rate limits, throttles, or quotas"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
  - "{{BACKEND_PATH}}/app/core/*.py"
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
---

# Rate Limiting & Throttling

## MUST

### Algorithm
- Use token bucket or sliding window algorithm for rate limiting
- Token bucket preferred for burst tolerance with sustainable average rate
- Sliding window preferred for strict enforcement with no burst allowance
- Sliding window counter acceptable for approximate enforcement at high scale

### Per-Endpoint Tiers

| Tier | Requests | Window | Scope | Example |
|------|----------|--------|-------|---------|
| Anonymous | 30 | 60s | IP address | Public search |
| Authenticated | 100 | 60s | User ID | API consumption |
| Authenticated (write) | 20 | 60s | User ID | POST/PUT/DELETE |
| Internal service | 1000 | 60s | API key | Microservice-to-microservice |
| Admin | 500 | 60s | User ID | Admin dashboard |

- Rate limits MUST be enforceable per user, per IP, and per API key independently
- Critical endpoints (auth, password reset) MUST have stricter limits than defaults

### Response Headers
Every rate-limited response MUST include:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1715247600
```

When limit exceeded, return HTTP 429 with:
```json
{"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "details": {"limit": 100, "window": "60s", "retry_after": 23}}}
```

### Middleware Pattern
- Implement rate limiting as FastAPI middleware or dependency, not inline in route handlers
- Support both in-memory (development / single-instance) and distributed (Redis/pg-based) backends
- In distributed mode, use atomic counter operations; never read-then-write (race condition)

## SHOULD

- Gradual backoff advice in 429 responses (`Retry-After` header)
- Separate rate limits per HTTP method (GET more permissive than POST)
- Whitelist for internal health checks and monitoring probes
- Circuit breaker integration: if downstream service is rate-limiting us, propagate or shed load

## ANTI-PATTERNS (BLOCKING)

- `time.sleep()` in middleware to enforce rate limits (blocks the event loop)
- Unlimited endpoints that accept user-controlled parameters that expand to expensive operations
- Per-IP limits as the ONLY protection (easily bypassed via proxies, NAT)
- Silent dropping of requests returning 200 OK but not processing them
- No rate limits on authentication endpoints (invitation to credential stuffing)

## Enforcement Checklist

- [ ] Token bucket or sliding window chosen and documented
- [ ] Per-endpoint tier table defined
- [ ] Rate limit headers present on every constrained endpoint
- [ ] 429 response shape matches Article IV error envelope
- [ ] Auth endpoints (login, password reset, signup) have strict limits
- [ ] Distributed backend configured for multi-instance deployments
