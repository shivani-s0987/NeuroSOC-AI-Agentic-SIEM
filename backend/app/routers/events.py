import csv
import json
from pathlib import Path
from uuid import uuid4

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event
from app.schemas import EventBatchCreate, EventCreate, EventIngestResult, EventOut, Paginated
from app.core.pagination import apply_sort, paginated, pagination_params
from app.core.permissions import Permission
from app.security import require_permission
from app.services.ingest_service import ingest_file_report
from app.services.realtime_service import enqueue_celery_event, publish_notification, queue_event

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=Paginated[EventOut])
def list_events(
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.EVENTS_READ)),
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
def create_event(payload: EventCreate, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.EVENTS_WRITE))) -> Event:
    data = payload.model_dump(exclude={"metadata", "idempotency_key", "external_id"})
    data["payload_metadata"] = payload.metadata or {}
    data["idempotency_key"] = payload.idempotency_key
    data["external_id"] = payload.external_id
    event = Event(**data)
    db.add(event)
    try:
        db.flush()
        queue_event(db, event)
        publish_notification(db, "event.created", "event", event.id, {
            "severity": event.severity,
            "source": event.source,
        })
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An event with this external or idempotency identifier already exists")
    db.refresh(event)
    enqueue_celery_event(event.id)
    return event


@router.post("/ingest", response_model=EventIngestResult)
def ingest_event(payload: EventCreate, db: Session = Depends(get_db), actor=Depends(require_permission(Permission.EVENTS_WRITE))) -> EventIngestResult:
    if payload.idempotency_key:
        existing = db.query(Event).filter(Event.idempotency_key == payload.idempotency_key).first()
        if existing:
            return EventIngestResult(accepted=True, duplicate=True, id=existing.id)
    event_data = payload.model_dump(exclude={"metadata", "idempotency_key", "external_id"})
    event_data.update(payload_metadata=payload.metadata or {}, idempotency_key=payload.idempotency_key,
                      external_id=payload.external_id)
    event = Event(**event_data)
    db.add(event)
    try:
        db.flush()
        queue_event(db, event)
        publish_notification(db, "event.created", "event", event.id, {"severity": event.severity})
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate event identifier") from None
    enqueue_celery_event(event.id)
    return EventIngestResult(accepted=True, duplicate=False, id=event.id)


@router.post("/ingest/batch")
def ingest_batch(payload: EventBatchCreate, db: Session = Depends(get_db), actor=Depends(require_permission(Permission.EVENTS_WRITE))) -> dict[str, Any]:
    results: list[EventIngestResult] = []
    for index, item in enumerate(payload.events):
        try:
            if item.idempotency_key:
                existing = db.query(Event).filter(Event.idempotency_key == item.idempotency_key).first()
                if existing:
                    results.append(EventIngestResult(accepted=True, duplicate=True, id=existing.id, index=index))
                    continue
            result = ingest_event(item, db=db, actor=actor)
            result.index = index
            results.append(result)
        except HTTPException as exc:
            results.append(EventIngestResult(accepted=False, index=index, errors=[str(exc.detail)]))
    return {"accepted": sum(r.accepted for r in results), "rejected": sum(not r.accepted for r in results), "results": results}


@router.get("/processing-status/{event_id}")
def processing_status(event_id: int, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.EVENTS_READ))) -> dict[str, Any]:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "event_id": event.id,
        "status": event.processing_status,
        "attempts": event.processing_attempts,
        "processed_at": event.processed_at,
        "error": event.last_processing_error if event.processing_status == "failed" else None,
    }


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
