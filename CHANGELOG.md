# Changelog

## Unreleased

### PR 8 - Production Readiness

- Added production startup validation that rejects SQLite and development secrets.
- Added database readiness, non-root containers, PostgreSQL worker support, and safe Compose configuration.
- Added integrity-verified database backups and confirmed PostgreSQL restore tooling.
- Added separated CI, container, and security workflows.
- Added production release, deployment, rollback, observability, backup, and configuration documentation.

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
