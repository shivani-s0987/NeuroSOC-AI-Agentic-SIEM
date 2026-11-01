# PR 2 Completion Report

## Completed validation

- Backend pytest suite: 18 passed.
- Ruff backend lint: passed.
- Frontend production build: passed.
- Frontend Vitest: 2 passed.
- SQLite Alembic upgrade, current, downgrade, and upgrade lifecycle: passed for `f0c2a4d1b9e7`.
- Docker Compose backend/frontend/PostgreSQL runtime: passed.
- Persisted PostgreSQL migration and live registration/login/me/analytics smoke: passed.

## Security implementation

- Argon2id password storage with successful legacy SHA-256 migration on login.
- Access and refresh JWTs with type, identifier, issuer/audience support, and refresh family identifiers.
- Server-side refresh-token hash sessions, rotation, reuse-family revocation, and logout.
- Password reset tokens hashed, expiring, and single-use; reset revokes refresh sessions.
- Centralized enterprise roles and permission dependencies.
- Admin user listing, role/status management, self-role protection, and final-admin protection.
- Viewer-only public registration.
- Process-local authentication rate limiting documented as development-only for horizontal deployments.
- Safe structured audit service preventing credential-key persistence.

## Remaining limitations

- Distributed Redis-backed rate limiting is not implemented.
- Refresh cookies are not implemented; browser access tokens remain in memory.
- SMTP reset delivery is not implemented. Development token exposure is gated to development mode only.
- Case ownership remains username/assigned metadata rather than a dedicated owner foreign key.
- Every future domain router should continue to use permission dependencies in later PRs.
