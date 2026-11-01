from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case
from app.schemas import CaseCreate, CaseOut, Paginated
from app.services.case_service import add_note, create_case
from app.security import require_permission
from app.core.permissions import Permission
from app.core.pagination import apply_sort, paginated, pagination_params

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=Paginated[CaseOut])
def list_cases(
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.CASES_READ)),
    paging: dict = Depends(pagination_params),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    assigned_to: str | None = Query(None),
):
    allowed = {"id", "created_at", "status", "priority", "assigned_to"}
    if paging["sort_by"] not in allowed:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of: {sorted(allowed)}")
    query = db.query(Case)
    for field, value in {
        "status": status,
        "priority": priority,
        "assigned_to": assigned_to,
    }.items():
        if value:
            query = query.filter(getattr(Case, field) == value)
    total = query.count()
    query = apply_sort(query, Case, paging["sort_by"], allowed, paging["sort_order"], "created_at")
    offset = (paging["page"] - 1) * paging["page_size"]
    return paginated(
        query.offset(offset).limit(paging["page_size"]).all(),
        paging["page"],
        paging["page_size"],
        total,
    )


@router.post("", response_model=CaseOut)
def create(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_permission(Permission.CASES_MANAGE)),
) -> Case:
    return create_case(db, payload.title, payload.priority, payload.assigned_to, payload.summary)


@router.post("/{case_id}/notes")
def add_case_note(
    case_id: int,
    author: str,
    content: str,
    db: Session = Depends(get_db),
    _user=Depends(require_permission(Permission.CASES_MANAGE)),
) -> dict[str, str]:
    try:
        note = add_note(db, case_id, author, content)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": str(note.id), "content": str(note.content)}
