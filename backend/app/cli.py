from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess  # nosec B404
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Event
from app.services.detection_service import load_rules
from app.services.ingest_service import ingest_file
from app.services.report_service import create_report

app = typer.Typer(add_completion=False, rich_markup_mode="rich")


@app.command()
def start() -> None:
    Base.metadata.create_all(bind=engine)
    typer.echo("NeuroSOC backend started")


@app.command()
def import_logs(path: str) -> None:
    db: Session = SessionLocal()
    ingest_file(db, path)
    typer.echo("Imported logs")
    db.close()


@app.command()
def search(query: str) -> None:
    db: Session = SessionLocal()
    results = db.query(Event).filter(Event.message.ilike(f"%{query}%")).all()
    typer.echo(f"Found {len(results)} matching events")
    db.close()


@app.command()
def rules() -> None:
    db: Session = SessionLocal()
    load_rules(db)
    typer.echo("Loaded rules")
    db.close()


@app.command()
def report(title: str = "Investigation Report") -> None:
    db: Session = SessionLocal()
    create_report(db, title, "investigation", "markdown")
    typer.echo("Created report")
    db.close()


@app.command()
def doctor() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.connect():
        typer.echo("Database connection: healthy")
    typer.echo("Configuration: loaded")


@app.command()
def backup(output: str | None = None) -> None:
    from app.config import settings

    backup_dir = settings.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = (
        Path(output)
        if output
        else backup_dir
        / (
            f"neurosoc-{timestamp}.sqlite3"
            if settings.database_url.startswith("sqlite")
            else f"neurosoc-{timestamp}.dump"
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        source = Path(settings.database_url.removeprefix("sqlite:///"))
        if not source.is_file():
            raise typer.BadParameter(f"Database does not exist: {source}")
        with sqlite3.connect(source) as source_db, sqlite3.connect(destination) as backup_db:
            source_db.backup(backup_db)
    else:
        pg_dump = shutil.which("pg_dump")
        if pg_dump is None:
            raise typer.BadParameter("pg_dump is required for PostgreSQL backups")
        # The allowlisted executable is resolved to an absolute path and all arguments are fixed.
        result = subprocess.run(  # nosec B603
            [
                pg_dump,
                "--format=custom",
                "--no-password",
                "--file",
                str(destination),
                settings.database_url,
            ],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            destination.unlink(missing_ok=True)
            raise typer.BadParameter(f"pg_dump failed: {result.stderr.strip()}")
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    metadata = {
        "database_url_scheme": settings.database_url.split(":", 1)[0],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
        "bytes": destination.stat().st_size,
    }
    destination.with_suffix(destination.suffix + ".json").write_text(json.dumps(metadata, indent=2))
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.backup_retention_days)
    for candidate in backup_dir.iterdir():
        if (
            candidate.is_file()
            and datetime.fromtimestamp(candidate.stat().st_mtime, timezone.utc) < cutoff
        ):
            candidate.unlink(missing_ok=True)
    typer.echo(f"Backup created: {destination}")


@app.command()
def restore(
    source: str,
    confirm: bool = typer.Option(False),
) -> None:
    if not confirm:
        raise typer.BadParameter(
            "Pass --confirm to restore; use an isolated database for validation"
        )
    from app.config import settings

    source_path = Path(source)
    if not source_path.is_file():
        raise typer.BadParameter(f"Backup does not exist: {source_path}")
    metadata_path = source_path.with_suffix(source_path.suffix + ".json")
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text())
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != metadata.get("sha256"):
            raise typer.BadParameter("Backup integrity check failed: SHA-256 mismatch")
    if not settings.database_url.startswith("sqlite"):
        pg_restore = shutil.which("pg_restore")
        if pg_restore is None:
            raise typer.BadParameter("pg_restore is required for PostgreSQL restores")
        # The allowlisted executable is resolved to an absolute path and all arguments are fixed.
        result = subprocess.run(  # nosec B603
            [
                pg_restore,
                "--no-password",
                "--clean",
                "--if-exists",
                "--exit-on-error",
                "--dbname",
                settings.database_url,
                str(source_path),
            ],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise typer.BadParameter(f"pg_restore failed: {result.stderr.strip()}")
        typer.echo(f"Restored: {source_path}")
        return
    destination = Path(settings.database_url.removeprefix("sqlite:///"))
    with sqlite3.connect(source_path) as backup, sqlite3.connect(destination) as database:
        backup.backup(database)
    typer.echo(f"Restored: {source}")


@app.command()
def version() -> None:
    typer.echo("NeuroSOC 0.1.0")


if __name__ == "__main__":
    app()
