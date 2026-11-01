# Backup and Restore

## SQLite development

```bash
python -m app.cli backup --output backups/neurosoc.sqlite3
```

The backup uses SQLite's backup API and writes `<backup>.json` with size and SHA-256 metadata.

## PostgreSQL

`pg_dump` and `pg_restore` must be present in the API or operations image.

```bash
python -m app.cli backup
```

Backups are custom-format dumps and are retained according to `BACKUP_RETENTION_DAYS`.

## Restore safety

Restores are destructive and require `--confirm`.

```bash
python -m app.cli restore backups/neurosoc-20261101T120000Z.dump --confirm
```

Before a production restore, stop writes, preserve a pre-restore backup, restore into an isolated database, run migrations and application smoke tests, then update the production connection only after validation.

## Isolated restore validation

1. Create test records in the source database.
2. Run `python -m app.cli backup`.
3. Create a separately named restore database.
4. Run `DATABASE_URL=postgresql+psycopg://...restore_db ... pg_restore ...`.
5. Verify counts and relationships using SQL or application integration tests.
6. Point an application instance configured for the restore database at it and run `/health/ready`.

A file or checksum alone is not proof of recoverability.
