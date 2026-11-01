# Authentication and RBAC Audit

## Scope

Inspected the PR 2 branch baseline, including `security.py`, `routers/auth.py`, user and audit models, schemas, all routers, configuration, frontend API shell, existing Alembic revision, and backend tests.

## Confirmed findings

| Severity | Evidence | Required change |
|---|---|---|
| Critical | Refresh tokens are issued without server-side state. Reuse cannot be detected, rotation cannot revoke a family, and logout cannot revoke a session. | Add hashed refresh-session records, family IDs, rotation, reuse detection, and revocation. |
| Critical | Sensitive routes do not consistently depend on authenticated users. The only route inventory was `auth/me` and case creation. | Apply centralized permission dependencies to sensitive read/write operations. |
| High | Role values are legacy `Administrator`, `Analyst`, and `Viewer`; they do not match the requested `ADMIN`, `SOC_ANALYST`, and `SECURITY_VIEWER`. | Normalize roles, migrate existing values, and reject privilege escalation. |
| High | Access tokens do not include issuer/audience/family claims and refresh credentials are not validated against a database session. | Add strict issuer/audience/type/family claims and session validation. |
| High | Forgot-password and reset-password endpoints do not exist. | Add hashed, single-use, expiring reset tokens and revoke sessions on reset. |
| High | No security audit model for structured actor/action/request metadata exists; existing `AuditLog.details` is unconstrained. | Add structured audit fields or a safe JSON details policy and security-event helper. |
| High | Registration schema accepts a role and public registration depends on ad hoc coercion. | Always assign `SECURITY_VIEWER`; expose role changes only to administrators. |
| High | No persistent user-management endpoints exist. | Add paginated admin list, detail, role, activation/deactivation, and final-admin guards. |
| Medium | Frontend has no authentication state or protected-route integration. | Add focused login state and route guards without redesigning dashboard pages. |
| Medium | No application rate limiter is present in the reviewed security modules. | Add configurable in-memory development limiters and state a Redis requirement for production multi-worker deployment. |

## PR 1 foundation status

Available:
- Pydantic Settings and environment parsing.
- SQLAlchemy session factory and declarative Base.
- Alembic environment and initial revision.
- Centralized exception handlers and request logging.
- `/api/v1` compatibility routing.
- Argon2 verification with legacy hash migration support.

Not available:
- Complete endpoint authorization.
- Refresh-session persistence.
- Password-reset persistence.
- Structured security audit fields.
- Production-safe cookie refresh handling.

## Compatibility constraints

- Legacy unversioned auth routes remain available.
- Existing usernames and password hashes remain valid.
- Legacy role values are migrated without granting more access than their prior role.
- Existing frontend API calls remain compatibility aliases until frontend auth is completed.
