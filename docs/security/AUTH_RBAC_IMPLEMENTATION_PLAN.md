# Authentication and RBAC Implementation Plan

## 1. Data foundation

- Add refresh-session, password-reset-token, and structured security-audit fields.
- Add a reversible Alembic revision preserving users and role values.
- Normalize legacy roles into the three enterprise roles.

## 2. Password and token services

- Keep Argon2id hashing and legacy migration in a shared security service.
- Add issuer/audience/type validation where configured.
- Store only refresh/reset hashes; implement rotation, reuse detection, and family revocation.

## 3. RBAC

- Define permissions and role mappings centrally.
- Add reusable authenticated and permission dependencies.
- Protect core data-mutating and data-reading routers.
- Add administrative user-management endpoints and final-admin safeguards.

## 4. Password reset and audit

- Add generic forgot-password responses.
- Add development reset-token delivery only through an explicit development response/configuration.
- Audit authentication and administrative outcomes without credentials or raw tokens.

## 5. Frontend

- Add a focused login page and API-backed authenticated state.
- Protect operational routes and surface forbidden/unauthorized states.
- Keep access-token state in memory; document that refresh-cookie support may require HTTPS deployment.

## 6. Verification

- Password, JWT, rotation/reuse, logout, reset, RBAC, IDOR, audit, migration, and rate-limit tests.
- Full backend suite, Ruff, frontend build/tests, migration lifecycle, Compose configuration, and Docker smoke tests.

## Scope exclusions

Detection-engine redesign, AI behavior, real-time processing, and dashboard redesign remain outside PR 2.
