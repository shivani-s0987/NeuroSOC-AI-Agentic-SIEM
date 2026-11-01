# Environment Configuration

## Environment modes

| Mode | Database | Development token exposure | Intended use |
|---|---|---|---|
| development | SQLite allowed | Allowed | Local developer workstation |
| testing | SQLite or isolated PostgreSQL | Forbidden by API policy where configurable | Automated tests |
| production | PostgreSQL required | Forbidden | Staging and production |

Never commit `.env`. Use `.env.example` as the safe template.

## Required production variables

- `APP_ENV=production`
- `DATABASE_URL=postgresql+psycopg://...`
- `JWT_SECRET` and `JWT_REFRESH_SECRET`: independently generated random values of at least 32 characters.
- `CORS_ORIGINS`: explicit HTTPS origins, comma-separated.
- `TRUSTED_HOSTS`: explicit application hostnames.
- `POSTGRES_PASSWORD`: supplied to Compose through an external secret mechanism.

AI, threat-intelligence, email, Redis/Celery, storage, and provider settings must be configured only when the corresponding feature is enabled. Provider keys remain server-side.

## Validation

Settings load at process startup. Production rejects SQLite, development secret strings, short JWT secrets, localhost/wildcard CORS, and non-PostgreSQL schemes.

## Generate secrets

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Store each generated value in the deployment secret manager. Do not place secrets in Compose files, shell history, logs, API responses, or CI YAML.
