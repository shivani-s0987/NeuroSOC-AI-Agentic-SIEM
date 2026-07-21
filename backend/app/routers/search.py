from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event
from app.services.search_service import save_search, search_events

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(query: str | None = None, host: str | None = None, user: str | None = None, severity: str | None = None, src_ip: str | None = None, db: Session = Depends(get_db)) -> list[Event]:
    return search_events(db, query=query, host=host, user=user, severity=severity, src_ip=src_ip)


@router.post("/saved")
def save(payload: dict[str, str], db: Session = Depends(get_db)) -> dict[str, str]:
    saved = save_search(db, payload["name"], payload["query"], payload["owner"])
    return {"id": str(saved.id), "name": saved.name}
