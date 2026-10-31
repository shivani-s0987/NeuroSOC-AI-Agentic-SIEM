# Authentication Threat Model

## Assets

- User passwords and password-reset credentials
- Access and refresh tokens
- User roles and account status
- Security events, cases, reports, settings, and audit evidence

## Key threats and controls

- Credential theft: Argon2id, short access-token lifetime, rotated refresh tokens, and TLS deployment guidance.
- Token replay/reuse: refresh-session hashes and family revocation.
- Privilege escalation: server-authoritative role map, ignored public role, and administrator-only management endpoints.
- Account enumeration: generic password-reset response.
- Brute force: configurable sensitive-route rate limiting; production Redis is required for reliable distributed limits.
- Disabled-account access: access and refresh authentication reject disabled users.
- Audit tampering: audit records have no ordinary user write endpoints.
- IDOR: resource reads require backend permissions; case ownership must be strengthened when an owner field exists.

## Residual risks

- The development rate limiter is process-local and not distributed.
- Refresh tokens are returned in JSON because secure refresh cookies are not yet implemented.
- Reset delivery has no SMTP provider integration and production must integrate or intentionally disable development exposure.
- Password-reset initiation is rate-limited by client IP only in the current implementation.
