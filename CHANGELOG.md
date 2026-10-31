# Changelog

## Unreleased

### PR 1 - Backend Foundation Stabilization

- Added environment validation for SQLite/PostgreSQL configuration and production secrets.
- Removed schema mutation from application startup.
- Added Alembic migrations with a reviewed initial schema revision.
- Added `/api/v1` routes while retaining unversioned compatibility aliases.
- Added standardized validation and application error responses with request IDs.
- Added bounded pagination, filtering, sorting allowlists, and structured HTTP logging.
- Added header-aware CSV ingestion and row-level rejection reporting.
- Added backend foundation engineering and migration documentation.

## 0.1.0

- Initial release of NeuroSOC with backend API, SQLite persistence, detection engine, case management, AI assistant hooks, React dashboard, and CI workflow.
