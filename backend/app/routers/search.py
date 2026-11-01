from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.search_service import save_search, search_events
from app.core.permissions import Permission
from app.security import require_permission

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=None)
def search(
    query: str | None = None,
    host: str | None = None,
    user: str | None = None,
    severity: str | None = None,
    src_ip: str | None = None,
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.EVENTS_READ)),
) -> list[dict[str, object]]:
    results = search_events(db, query=query, host=host, user=user, severity=severity, src_ip=src_ip)
    return [
        {
            "id": str(event.id),
            "message": str(event.message),
            "severity": str(event.severity),
        }
        for event in results
    ]


@router.post("/saved")
def save(
    payload: dict[str, str],
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.EVENTS_WRITE)),
) -> dict[str, str]:
    saved = save_search(db, payload["name"], payload["query"], payload["owner"])
    return {"id": str(saved.id), "name": str(saved.name)}
