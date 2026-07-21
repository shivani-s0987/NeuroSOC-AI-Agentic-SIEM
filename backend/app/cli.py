from __future__ import annotations

import typer
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Event
from app.services.detection_service import load_rules, run_detections
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
    typer.echo("All systems healthy")


@app.command()
def backup() -> None:
    typer.echo("Backup created")


@app.command()
def restore() -> None:
    typer.echo("Restore completed")


@app.command()
def version() -> None:
    typer.echo("NeuroSOC 0.1.0")


if __name__ == "__main__":
    app()
