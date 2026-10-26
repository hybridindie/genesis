---
read_when: "Handling user input, HTML, or query construction"
paths:
  - "{{BACKEND_PATH}}/app/api/**/*.py"
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - "{{FRONTEND_PATH}}/**/*.ts"
  - "{{FRONTEND_PATH}}/**/*.tsx"
  - "{{FRONTEND_PATH}}/index.html"
---

# Input Sanitization, XSS Prevention & Injection Protection

## MUST

### Cross-Site Scripting (XSS)
- All dynamic content rendered in the frontend MUST be escaped or rendered through a safe framework (React's JSX escaping is acceptable; `dangerouslySetInnerHTML` is BLOCKED unless explicitly DOMPurify-sanitized)
- Sanitize all user-generated HTML with DOMPurify before rendering
- Apply Content Security Policy (CSP) headers:
  - `default-src 'self'`
  - `script-src 'self'` (NO `'unsafe-inline'`, `'unsafe-eval'` only if unavoidable and documented)
  - `style-src 'self' 'unsafe-inline'` (if needed for CSS-in-JS)
  - `img-src 'self' data: blob:`
  - `connect-src 'self' {{DB_PROVIDER}}.co`
- No inline event handlers (`onclick`, `onerror`) in HTML; use React event handling instead

### SQL Injection
- ALL database queries MUST use parameterized queries, prepared statements, or the Supabase client (which parameterizes internally)
- NEVER concatenate user input into SQL strings, even for "simple" queries
- RPC functions in Supabase MUST validate inputs before executing SQL

### Command Injection
- NEVER pass user input to `os.system()`, `subprocess.call()`, `exec()`, or `eval()`
- If shell execution is unavoidable, use a strict allowlist of commands and escape all arguments
- Prefer library functions over shell commands for system operations

### NoSQL Injection
- Validate all keys in user-supplied JSON before using them in database filters or update operations
- Do not use user input to construct field names in `$set`, `$inc`, or similar operations

### Path Traversal
- Validate and sanitize all file paths constructed from user input
- Use `os.path.abspath()` + `os.path.commonpath()` to ensure the resolved path stays within an allowlisted directory
- Never expose full filesystem paths to the client

### Header Injection / Response Splitting
- Sanitize or reject newline characters (`\r`, `\n`) in any user input used in HTTP headers
- Validate redirect URLs to prevent open redirect vulnerabilities (allowlist or same-origin)

## SHOULD

- Sub-resource Integrity (SRI) hashes for external scripts and stylesheets
- Trusted Types API enforcement for frontend DOM manipulation
- Strict CSP reporting via `report-uri` or `report-to` (log violations, iterate)
- Input validation at the outermost API boundary (FastAPI/Pydantic); business logic should assume inputs are already validated

## ANTI-PATTERNS (BLOCKING)

- `dangerouslySetInnerHTML` with unsanitized user content
- Raw SQL string formatting (`f"SELECT * FROM users WHERE id = {user_id}"`)
- `eval()` or `exec()` with any user input
- Trusting client-side validation as the ONLY validation layer
- Reflecting user input back in error messages without escaping
- URLs built from user input without allowlisting or `urllib.parse`

## Enforcement Checklist

- [ ] CSP headers present and strict on all responses
- [ ] No inline `<script>` tags in HTML; all scripts external
- [ ] All SQL queries parameterized or via ORM/client abstraction
- [ ] No `os.system()` or `subprocess` with user input
- [ ] File uploads restricted by extension, size, and scanned for malware
- [ ] Redirect URLs validated (same-origin or allowlist)
