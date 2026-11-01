# PR 1 Test Report

## Executed

- Focused foundation regressions.
- Full backend pytest suite.
- Clean SQLite Alembic upgrade, current, and downgrade lifecycle.
- Frontend production TypeScript/Vite build.
- Docker Compose runtime and live API smoke workflow where available.

## Current results

- Backend suite: 12 passed.
- Ruff: all backend checks passed.
- Frontend production build: passed.
- Frontend Vitest: 1 test passed.
- Alembic clean SQLite upgrade, current revision, and downgrade: passed with revision `efbc1c8b5938`.
- Docker Compose configuration: passed.
- Docker backend image: built and started.
- PostgreSQL container: healthy.
- Live Docker smoke: registration, login, authenticated event creation, and analytics returned successfully.

## Known validation limits

- PostgreSQL migration downgrade was not exercised against a disposable deployment database.
- The legacy PostgreSQL stamping path was exercised against the existing Compose volume with tables created by the previous startup code.
- The request suite does not cover every router because those domains are outside PR 1 scope.
