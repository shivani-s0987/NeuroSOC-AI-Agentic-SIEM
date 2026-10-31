from __future__ import annotations

import shutil
import sqlite3
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
def backup(output: str = "neurosoc-backup.db") -> None:
    from app.config import settings
    if not settings.database_url.startswith("sqlite"):
        raise typer.BadParameter("CLI backup currently supports SQLite; use pg_dump for PostgreSQL")
    source = settings.database_url.removeprefix("sqlite:///")
    source_path = Path(source)
    if not source_path.exists():
        raise typer.BadParameter(f"Database does not exist: {source_path}")
    shutil.copy2(source_path, output)
    typer.echo(f"Backup created: {output}")


@app.command()
def restore(source: str) -> None:
    from app.config import settings
    if not settings.database_url.startswith("sqlite"):
        raise typer.BadParameter("CLI restore currently supports SQLite; use pg_restore for PostgreSQL")
    source_path = Path(source)
    if not source_path.is_file():
        raise typer.BadParameter(f"Backup does not exist: {source_path}")
    destination = Path(settings.database_url.removeprefix("sqlite:///"))
    with sqlite3.connect(source_path) as backup, sqlite3.connect(destination) as database:
        backup.backup(database)
    typer.echo(f"Restored: {source}")


@app.command()
def version() -> None:
    typer.echo("NeuroSOC 0.1.0")


if __name__ == "__main__":
    app()
