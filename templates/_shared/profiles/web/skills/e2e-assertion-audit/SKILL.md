---
name: e2e-assertion-audit
description: Scan E2E tests for no-op assertions and overly permissive checks that provide false confidence
user-invocable: true
disable-model-invocation: true
---

# E2E Assertion Audit

Review E2E tests for assertions that pass without actually validating behavior.

## Anti-Patterns to Find

### 1. No-Op Assertions
- `expect(true).toBe(true)`
- `assert 1 == 1`
- `expect(page).toBeDefined()` (always true)
- Assertions that don't exercise the feature under test

### 2. Overly Permissive Checks
- `expect(text).toContain("a")` (matches almost anything)
- `expect(response.status).toBeLessThan(500)` (accepts 404 as success)
- `expect(data).toBeTruthy()` (accepts `{}`, `[]`, `true`)
- `expect(error).toBeDefined()` (catches both success and error envelopes)

### 3. Missing Negative Cases
- No assertion that the wrong action is rejected
- No assertion that data is NOT present when unauthorized
- No assertion that the UI shows an error state

### 4. Fragile Selectors
- `page.click("button")` (clicks first button, not the intended one)
- `page.fill("input", ...)` (fills first input)
- `expect(page.locator("text=Submit")).toBeVisible()` (may match multiple)

## Output

```
## E2E Assertion Audit

### No-Op Assertions
- `tests/e2e/checkout.test.ts:45` — `expect(true).toBe(true)` after clicking pay. Assert on receipt page URL or confirmation text instead.

### Overly Permissive
- `tests/e2e/login.test.ts:32` — `expect(response.status).toBeLessThan(500)` accepts 401 as "success". Assert exact status: `expect(response.status).toBe(200)`.

### Missing Negative Cases
- `tests/e2e/admin.test.ts` — No test that non-admin user is redirected. Add: `await page.goto('/admin'); expect(page.url()).not.toContain('/admin')`.

### Fragile Selectors
- `tests/e2e/signup.test.ts:12` — `page.click('button')` clicks wrong button. Use: `page.click('button[type="submit"]')` or `data-testid`.
```

## Rules

- Only audit E2E test files (`tests/e2e/**`).
- Provide concrete replacement assertions.
- If a test is clean, note it: "Clean: `tests/e2e/search.test.ts` has specific selectors and negative cases."
