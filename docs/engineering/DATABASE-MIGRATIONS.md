# Database Migrations

## Commands

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "description"
```

## Configuration

Alembic reads `DATABASE_URL` through the application settings. SQLite is suitable for local development. PostgreSQL is used for deployment containers.

## Existing database procedure

Before migrating an existing SQLite database:

1. Copy the database file to a timestamped backup.
2. Run `alembic current` and inspect its state.
3. Test `alembic upgrade head` against the copy.
4. Only apply the migration to the original after the copy succeeds.
5. Use a PostgreSQL dump/restore workflow for PostgreSQL backups; do not treat the SQLite backup as valid PostgreSQL data.

## Production startup

Production application startup must not infer schema changes from model metadata. Review and apply migrations explicitly as a deployment step.
