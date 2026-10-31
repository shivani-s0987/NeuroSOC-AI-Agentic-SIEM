#!/bin/sh
set -eu

set +e
PYTHONPATH=/app/backend python - <<'PY'
from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)
tables = set(inspector.get_table_names())
has_version_table = "alembic_version" in tables
if not has_version_table and "users" in tables and "events" in tables:
    print("Existing schema detected without Alembic history; stamping baseline revision", flush=True)
    raise SystemExit(10)
PY
status=$?
set -e
if [ "$status" -eq 10 ]; then
    python -m alembic stamp head
else
    python -m alembic upgrade head
fi
exec python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
