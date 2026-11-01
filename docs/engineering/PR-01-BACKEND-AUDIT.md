# PR 1 Backend Foundation Audit

## Scope

Audited the FastAPI application under `backend/app`, backend tests, dependency manifests, Docker configuration, migration configuration, frontend API usage, and the current SQLite database state.

## Architecture

- FastAPI exposes authentication, events, alerts, detections, search, cases, reports, analytics, settings, and assistant routers.
- SQLAlchemy declarative models are defined in `backend/app/models.py` and share a session and declarative base in `backend/app/database.py`.
- Routers currently mix transport, validation, and some service/database behavior.
- Pydantic v2 schemas are defined in `backend/app/schemas.py`.
- A React frontend calls Axios endpoints directly and currently expects the unversioned paths.
- The backend defaults to SQLite and has Docker support for PostgreSQL.

## Confirmed findings

| Severity | Finding and evidence | Proposed solution |
|---|---|---|
| Critical | `Settings` provides development JWT secrets in source. These are used by `security.py`. | Environment variable validation must reject default production secrets and require explicit production configuration. |
| High | `main.py` executes `Base.metadata.create_all()` and handwritten SQLite `ALTER TABLE` startup logic. | Production schema changes belong in Alembic; development startup may use migrations where appropriate. |
| High | `database.py` accepts `DATABASE_URL`, but `Settings.database_url` has only a generic string and startup has no environment validation. | Define normalized environment models and validate URL schemes and production settings. |
| High | `/events/import` accepts server paths and `/events/upload` is not constrained by the centralized configuration consistently. | Require multipart upload, allowlisted extensions, configured size, and generated safe storage names. |
| High | `ingest_service.py` uses text splitting for CSV and converts CSV rows through JSON; headers are not validated or mapped explicitly. | Add explicit supported CSV headers, required-field validation, row errors, and streaming reads. |
| High | JSON ingestion calls `json.loads` directly in the line parser and malformed input can abort a file import. | Catch parse errors per record and return rejected row counts. |
| High | Event GET and the alert, detection, case, and report lists call unbounded queries or fixed limits. | Add common pagination dependencies and allowlisted sorting/filter fields. |
| High | `require_roles` protects only a limited portion of API behavior; write routers remain inconsistently protected. | Inventory authorization ownership and apply dependencies consistently in PR 1 foundation routes. |
| Medium | API responses are FastAPI/Pydantic defaults or arbitrary exception text; no request ID is attached. | Add centralized request ID middleware, structured logging, and application exception handlers. |
| Medium | Several schemas have unconstrained strings and no valid value allowlists. | Add Pydantic constraints and reusable enums. |
| Medium | `main.py` combines startup schema handling, middleware, router registration, and configuration. | Keep startup small and place middleware/logging error handling in dedicated modules. |
| Medium | CLI backup and restore behavior depends on SQLite assumptions and destructive restore needs confirmation. | Make SQLite backups verified; PostgreSQL restoration explicitly supported or unsupported; require confirmation. |
| Medium | Alembic is configured but no migration revision exists. | Generate an initial revision from metadata and test clean upgrade/downgrade behavior. |
| Medium | Frontend calls unversioned routes directly, such as `/analytics/summary`, `/events`, `/alerts`, `/detections`, and `/cases`. | Add `/api/v1` with temporary unversioned compatibility aliases and update the frontend API base path. |

## Regression candidates already reproduced

- Metadata can be accepted as public `metadata` and persisted in `payload_metadata`.
- Current metadata response uses a serialization alias to avoid exposing the ORM column.
- Docker startup was reproducibly blocked by mismatch between `postgresql://` and the installed `psycopg` dialect.
- A live Docker smoke workflow successfully registered, logged in, created an event, and returned analytics; it validates runtime connectivity but not migration behavior.

## Database state

The root repository contains a runtime SQLite database. It is not used as a deterministic test fixture. Test configuration must override `DATABASE_URL` and tests must not depend on committed database contents.

## Compatibility considerations

- Existing frontend paths should continue to work during migration via unversioned aliases.
- Public JSON field names must remain `metadata`, while ORM `payload_metadata` remains internal.
- Existing query parameter names for direct creation must not be removed unexpectedly.
- Response shape changes should be added rather than silently replacing list arrays until the frontend is updated.

## Testing strategy

Tests will isolate database state, use temporary files, and exercise Pydantic/FastAPI behavior directly. Required coverage includes configuration, metadata round trips, ingestion row rejection, pagination/filtering/sorting, centralized errors, API aliases, migrations, CLI behavior, and Docker smoke validation.
