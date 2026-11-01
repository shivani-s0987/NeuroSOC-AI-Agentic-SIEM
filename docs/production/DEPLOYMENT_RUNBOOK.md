# Deployment Runbook

## Requirements

- PostgreSQL 16 or compatible managed PostgreSQL.
- Redis only where Celery mode is enabled.
- Secrets supplied outside Git and mounted through the deployment platform.
- Persistent volumes for PostgreSQL, uploads, and backups.

## Compose deployment

```bash
export POSTGRES_PASSWORD="$(openssl rand -hex 32)"
export JWT_SECRET="$(openssl rand -hex 32)"
export JWT_REFRESH_SECRET="$(openssl rand -hex 32)"
export CORS_ORIGINS="https://soc.example.com"
docker compose up -d --build
docker compose ps
docker compose exec backend python -m alembic upgrade head
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
```

## Verification

- Frontend is served on `http://127.0.0.1:${FRONTEND_PORT:-8080}`.
- API health probes return HTTP 200.
- Database and worker logs contain no connection errors.
- Create a disposable test event and verify processing status.
- Verify backup creation, metadata, and isolated restore.

## Approval

Production deployment requires explicit platform approval. Do not start production services with placeholder credentials.
