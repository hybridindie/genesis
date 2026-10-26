---
read_when: "Handling personal data, retention, or consent"
paths:
  - "{{BACKEND_PATH}}/src/libs/**/*.py"
  - "{{BACKEND_PATH}}/app/**/*.py"
  - "{{FRONTEND_PATH}}/**/*.ts"
  - "{{FRONTEND_PATH}}/**/*.tsx"
  - "supabase/migrations/**"
  - "supabase/seed.sql"
---

# Privacy, Data Protection & GDPR Compliance

## MUST

### Data Minimization
- Collect only data strictly necessary for the stated purpose
- Default to collecting less; require explicit justification for additional fields
- Document the purpose of every PII column in the database schema (comment or checklist)

### Lawful Basis
- Every data processing activity must document its lawful basis (consent, contract, legal obligation, vital interests, public task, or legitimate interests)
- Consent records must be verifiable: who consented, when, what they were told, and how they consented
- Consent must be opt-in (no pre-checked boxes) and as easy to withdraw as to give

### Data Subject Rights
- Implement endpoints for all GDPR rights: access, rectification, erasure (right to be forgotten), restriction, portability, objection
- Right to erasure: permanently delete user data within 30 days of request; cascade deletion to related tables
- Right to portability: export user data in a commonly used, machine-readable format (JSON or CSV)
- Log all data subject requests (timestamp, type, status, fulfillment date) in an auditable table

### PII Handling
- Define a canonical PII inventory: list of fields, tables, and services that store personal data
- PII must never be logged to application logs, error trackers, or analytics
- Use tokenized or pseudonymized identifiers in logs instead of raw user IDs when possible
- PII in transit: enforce HTTPS/TLS 1.3 for all client-server communication
- PII at rest: encrypt sensitive columns at the database level (column-level encryption for highly sensitive fields)

### International Transfers
- If data leaves the jurisdiction, document the transfer mechanism (Adequacy Decision, Standard Contractual Clauses, Binding Corporate Rules)
- Maintain a record of all third-party subprocessors (name, purpose, location, data types)

### Data Retention
- Every PII table must have a documented retention period
- Implement automated cleanup: scheduled jobs to soft-delete then permanently purge expired data
- Retain anonymized aggregate data for analytics; strip identifiers before retention period expires

## SHOULD

- Data Privacy Impact Assessment (DPIA) before launching features that process sensitive data
- Just-in-time privacy notices at the point of data collection
- Granular consent: separate consent for marketing vs functional data use
- Privacy-preserving defaults: features that share data are OFF by default

## ANTI-PATTERNS (BLOCKING)

- Storing PII in unencrypted columns without business justification
- Logging PII in plaintext (email, phone, name, IP address in application logs)
- Sending PII to third-party services without a Data Processing Agreement (DPA)
- Hard-deleting user data without a cascade plan (orphaned records, broken FKs)
- Using "we may use your data for any purpose" broad consent language
- Storing IP addresses or device fingerprints without consent or legal basis

## Compliance Checklist

- [ ] PII inventory documented
- [ ] All PII columns encrypted or access-controlled
- [ ] Consent mechanism implemented and auditable
- [ ] Data subject request endpoints exist and are tested
- [ ] Retention policies defined per table
- [ ] Automated data purge jobs scheduled
- [ ] Transfer mechanism documented for cross-border data
- [ ] Subprocessor list maintained
