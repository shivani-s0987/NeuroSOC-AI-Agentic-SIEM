import csv
import json
from pathlib import Path
from uuid import uuid4

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event
from app.schemas import EventCreate, EventOut, Paginated
from app.core.pagination import apply_sort, paginated, pagination_params
from app.services.ingest_service import ingest_file_report

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=Paginated[EventOut])
def list_events(
    db: Session = Depends(get_db),
    paging: dict = Depends(pagination_params),
    host: str | None = Query(default=None, max_length=120),
    user: str | None = Query(default=None, max_length=120),
    src_ip: str | None = Query(default=None, max_length=120),
    dst_ip: str | None = Query(default=None, max_length=120),
    event_type: str | None = Query(default=None, max_length=120),
    severity: str | None = Query(default=None, max_length=50),
    source: str | None = Query(default=None, max_length=120),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    message: str | None = Query(default=None, max_length=500),
):
    allowed = {"id", "timestamp", "host", "user", "src_ip", "severity", "source", "event_type"}
    if paging["sort_by"] not in allowed:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of: {sorted(allowed)}")
    query = db.query(Event)
    filters = {"host": host, "user": user, "src_ip": src_ip, "dst_ip": dst_ip,
               "event_type": event_type, "severity": severity, "source": source}
    for field, value in filters.items():
        if value is not None:
            query = query.filter(getattr(Event, field) == value)
    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)
    if message:
        query = query.filter(Event.message.ilike(f"%{message}%"))
    total = query.count()
    query = apply_sort(query, Event, paging["sort_by"], allowed, paging["sort_order"], "timestamp")
    offset = (paging["page"] - 1) * paging["page_size"]
    items = query.offset(offset).limit(paging["page_size"]).all()
    return paginated(items, paging["page"], paging["page_size"], total)


@router.post("", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    data = payload.model_dump(exclude={"metadata"})
    data["payload_metadata"] = payload.metadata or {}
    event = Event(**data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/import")
def import_events(path: str, db: Session = Depends(get_db)) -> dict[str, int]:
    raise HTTPException(status_code=410, detail="Use the secure upload endpoint")


@router.post("/upload")
async def upload_events(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    allowed = {".jsonl", ".log", ".csv"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail="Only .jsonl, .log, and .csv files are accepted")
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB")
    upload_dir = Path("./uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / f"{uuid4().hex}{suffix}"
    try:
        content = await file.read(10 * 1024 * 1024 + 1)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds 10 MB")
        destination.write_bytes(content)
        report = ingest_file_report(db, str(destination))
        return {"imported": report.imported, "rejected": report.rejected, "filename": file.filename or "upload", "errors": report.errors}
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Unable to ingest file: {exc}") from exc
    finally:
        destination.unlink(missing_ok=True)
