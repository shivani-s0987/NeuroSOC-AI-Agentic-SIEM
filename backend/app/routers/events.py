from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event
from app.schemas import EventCreate, EventOut
from app.services.ingest_service import ingest_file

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return db.query(Event).order_by(Event.timestamp.desc()).limit(100).all()


@router.post("", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/import")
def import_events(path: str, db: Session = Depends(get_db)) -> dict[str, int]:
    events = ingest_file(db, path)
    return {"imported": len(events)}
