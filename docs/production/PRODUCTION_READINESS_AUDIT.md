# Production Readiness Audit

## Scope

The audit covers the FastAPI backend, React frontend, PostgreSQL/Alembic database layer, Celery polling worker, realtime delivery, Docker assets, CI, tests, configuration, backup code, threat intelligence, AI investigation, and release files.

| Severity | Area | Actual finding | Impact | Reproduction | Recommended correction | Status |
|---|---|---|---|---|---|---|
| Critical | Production database | Production previously permitted SQLite. | Data loss risk and unsupported concurrency. | Set `APP_ENV=production DATABASE_URL=sqlite:///...`. | Reject SQLite and require PostgreSQL in production. | Implemented |
| High | Backup | PostgreSQL CLI reported unsupported even though production requires PostgreSQL. | No restorable production backup. | Run backup CLI against PostgreSQL. | Implement `pg_dump` and integrity metadata; require `pg_restore --confirm`. | Implemented |
| High | Containers | Compose contained malformed connection configuration and insecure fallback secrets. | Compose could not parse or container startup could be insecure. | Run `docker compose config` without overrides. | Require secrets and use Compose interpolation. | Implemented |
| High | Health | Only a superficial health endpoint existed. | Orchestrator could route requests when database was unavailable. | Stop PostgreSQL and call `/health`. | Add liveness/readiness and database checks. | Implemented |
| High | Container security | API image ran as root and had no explicit health/readiness configuration. | Container compromise and poor orchestration behavior. | Inspect Dockerfile and container user. | Non-root runtime, healthcheck, entrypoint migration. | Implemented |
| Medium | HTTP | No trusted-host or browser security headers middleware. | Host-header and browser hardening gaps. | Inspect FastAPI middleware. | Add trusted-host and baseline security headers. | Implemented |
| Medium | Logging | HTTP logs are JSON, but common correlation logging is not universal. | Difficult multi-service tracing. | Trace worker and provider operations. | Standardize service/component/operation structured fields. | Partial |
| Medium | CI | CI only installed and tested backend/frontend, without linting, migration, container, or security jobs. | Non-reproducible and insecure changes could merge. | Inspect `.github/workflows/ci.yml`. | Add separated backend/frontend/container/security jobs. | Implemented |
| Critical | Dependencies | Current lockfile audit reports two critical findings in development tooling through `tinypool` and one high production dependency finding in the Axios chain. | Supply-chain compromise or runtime request handling risk. | Run `npm audit`; current baseline reports 8 findings. | Upgrade Vitest/Vite tooling and review React Router/Axios upgrades; do not use breaking upgrades without compatibility validation. | Open |
| Medium | Worker | Database fallback worker and Celery share different retry semantics. | Duplicate or stuck jobs under partial configurations. | Configure Celery and observe fallback startup. | Document broker and consolidate job state transitions. | Partially verified |
| Low | Repository | Test and local database artifacts are present in the worktree. | Repository noise and accidental data commitment. | Inspect tracked/generated files. | Tighten `.gitignore` and `.dockerignore`. | Implemented |
| Informational | Architecture | The application combines API, worker, realtime, ingestion, detection, and threat intelligence in a modular FastAPI process. | Operational coupling but clear module boundaries. | Inspect `backend/app`. | Preserve modules; scale workers independently when warranted. | Documented |
