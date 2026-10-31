# PR 1 Implementation Plan

## Task sequence

1. **Configuration foundation**
   - Add environment-name parsing, URL validation, production secret checks, and CORS parsing.
   - Keep SQLite as the local default and make PostgreSQL explicit.
   - Add isolated test settings.

2. **Database and migration foundation**
   - Remove production startup DDL.
   - Complete Alembic environment setup.
   - Generate and review the initial schema revision.
   - Add migration tests against temporary SQLite.

3. **Common API behavior**
   - Add request IDs and structured logging.
   - Add centralized HTTP and validation exception handlers.
   - Preserve useful unversioned routes while exposing `/api/v1`.

4. **Schemas and pagination**
   - Constrain core strings, enums, timestamps, and pagination.
   - Add a common pagination dependency and response shape.
   - Add allowlisted sorting to bounded list endpoints.

5. **Event and ingestion correctness**
   - Preserve public `metadata` and internal `payload_metadata` mapping.
   - Stream JSONL, CSV, syslog, and plain text input.
   - Return success/rejection counts with row-level errors.
   - Restrict uploads to configuration limits.

6. **Transactions and CLI**
   - Roll back failed bulk and service operations.
   - Make CLI database checks truthful and restore destructive only with confirmation.
   - Close sessions in error paths.

7. **Tests and documentation**
   - Add isolated backend fixture coverage.
   - Run backend tests, Ruff, migrations, Docker Compose, and live smoke checks.
   - Update migration, environment, API, README, changelog, and test-report documents.

## Acceptance gates

Each gate requires focused tests before proceeding:

- Configuration and database startup.
- Event serialization and ingestion.
- Error handling and API aliases.
- Pagination/filter/sort behavior.
- Migration upgrade and rollback.
- Docker health and smoke workflow.

## Explicit PR boundaries

Not included in PR 1: advanced detection engineering, Redis queues, WebSockets, provider-backed autonomous AI, Playwright, new business domains, or frontend redesign.
