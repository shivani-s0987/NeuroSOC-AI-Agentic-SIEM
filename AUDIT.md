# NeuroSOC Repository Audit

## Severity summary

Confirmed during direct source inspection against commit `c25331b`.

| Severity | Issue | Root cause | Resolution status |
|---|---|---|---|
| Critical | Plain SHA-256 password storage and legacy verification | Passwords were hashed without a password KDF or salt | Argon2id implemented with legacy migration on successful login |
| Critical | Authentication ignored by API authorization | RBAC decorator was a no-op; `/me` accepted a username query | Bearer-token dependency and role dependency added |
| Critical | Hardcoded JWT/session secrets and wildcard CORS | Secrets and development origin policy were embedded in application startup | Environment-backed secrets and configurable origins implemented |
| High | `metadata` schema/API name conflicts with SQLAlchemy `payload_metadata` | API and ORM column names differed without explicit mapping | API alias and routing conversion added |
| High | Arbitrary server-side import path | Import endpoint accepted a caller-controlled path | Upload endpoint and allowlisted extensions implemented in progress |
| High | SQLite configuration branch unusable | Absolute-path logic bypassed configured PostgreSQL URLs | Database URL now selected directly with SQLite-only connection arguments |
| High | Detection loop is a single one-event keyword match | Detection service has no threshold, grouping, windows, or deduplication | Threshold detector implemented in progress |
| High | Rule loading always inserts duplicate rows | No lookup before insertion | Upsert implemented in progress |
| High | API write routes have no ownership or role checks | Authentication dependency absent throughout routers | Protected case/admin routes added in progress |
| Medium | Ingestion trusts JSON/CSV shape and timestamps | JSON parsing failures and non-normalized timestamps are not handled | ISO timestamp normalization and row validation added in progress |
| Medium | CLI `doctor`, `backup`, and `restore` are placeholders | Commands only print success text | SQLite-safe implementation planned |
| Medium | Frontend pages are placeholders and dashboard KPIs are constants | UI has no API client or page data integration | Backend analytics first, then page integration |
| Medium | No API migrations | `create_all` is the only schema lifecycle | Alembic/explicit startup reconciliation incomplete |
| Medium | AI service returns deterministic mock text | Provider abstraction is incomplete | Provider abstraction planned |

## Architecture observed

- FastAPI monolith under `backend/app`, with router modules and thin service modules.
- SQLAlchemy declarative models with SQLite default and no migration framework.
- JWT utilities, but no functioning bearer dependency or refresh-token persistence.
- React/Vite/TypeScript shell with one real route component and placeholder routes.
- Docker Compose starts only the backend and does not run PostgreSQL or frontend.

## Prioritized implementation plan

1. Secure authentication and database configuration; validate metadata and ingestion boundaries.
2. Protect write APIs and implement threshold-based, deduplicated detection.
3. Add safe uploads, pagination/filtering, audit records, consistent errors, and API versioning.
4. Connect the frontend to implemented endpoints and provide loading/error states.
5. Add provider abstraction and real provider fallback behavior for investigation assistance.
6. Add Alembic, Docker/PostgreSQL support, SSE/WebSocket, CI, tests, and accurate documentation.
