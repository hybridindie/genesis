---
read_when: "Rendering user content, building redirects or file paths from input, handling uploads, or setting security headers"
paths:
  - "{{BACKEND_PATH}}/**/api/**/*.py"
  - "{{FRONTEND_PATH}}/**/*.ts"
  - "{{FRONTEND_PATH}}/**/*.tsx"
---

# Web Input Security

Adds web specifics to `security.md` (secrets, validation, parameterised SQL
and subprocess calls are defined there).

## MUST

- Render user content through the framework's escaping. Raw HTML from users
  is sanitised (DOMPurify) before it is rendered.
- File paths built from input resolve inside an allowlisted directory
  (`Path.resolve()` + `is_relative_to`); full server paths never reach the
  client.
- Redirect targets are same-origin or allowlisted.
- Uploads are limited by type and size and never served from an executable
  path.
- Reject `\r` / `\n` in values placed in HTTP headers.
- Server-side validation exists for every client-side validation.

## SHOULD

- A Content Security Policy without `'unsafe-inline'` scripts; report
  violations before enforcing a stricter policy.
- SRI hashes for third-party scripts.
