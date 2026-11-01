from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertOut, Paginated
from app.core.pagination import apply_sort, paginated, pagination_params
from app.core.permissions import Permission
from app.security import require_permission

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.ALERTS_MANAGE)),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    allowed_statuses = {"open", "investigating", "acknowledged", "resolved", "closed"}
    if "status" in payload:
        status = str(payload["status"]).lower()
        if status not in allowed_statuses:
            raise HTTPException(status_code=422, detail="Invalid alert status")
        alert.status = status
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("", response_model=Paginated[AlertOut])
def list_alerts(
    db: Session = Depends(get_db),
    paging: dict = Depends(pagination_params),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
):
    allowed = {"id", "created_at", "severity", "status", "source"}
    if paging["sort_by"] not in allowed:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of: {sorted(allowed)}")
    query = db.query(Alert)
    for field, value in {"severity": severity, "status": status, "source": source}.items():
        if value:
            query = query.filter(getattr(Alert, field) == value)
    if start_time:
        query = query.filter(Alert.created_at >= start_time)
    if end_time:
        query = query.filter(Alert.created_at <= end_time)
    total = query.count()
    query = apply_sort(query, Alert, paging["sort_by"], allowed, paging["sort_order"], "created_at")
    offset = (paging["page"] - 1) * paging["page_size"]
    return paginated(
        query.offset(offset).limit(paging["page_size"]).all(),
        paging["page"],
        paging["page_size"],
        total,
    )


@router.post("", response_model=AlertOut)
def create_alert(
    title: str,
    severity: str = "medium",
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.ALERTS_MANAGE)),
) -> Alert:
    alert = Alert(title=title, severity=severity, summary="AI-assisted alert explanation generated")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
