from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportCreate, ReportOut, Paginated
from app.core.pagination import apply_sort, paginated, pagination_params
from app.core.permissions import Permission
from app.security import require_permission
from app.services.report_service import create_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=Paginated[ReportOut])
def list_reports(db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.REPORTS_READ)), paging: dict = Depends(pagination_params), report_type: str | None = Query(None), start_time: datetime | None = None, end_time: datetime | None = None):
    allowed = {"id", "created_at", "title", "report_type"}
    if paging["sort_by"] not in allowed:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of: {sorted(allowed)}")
    query = db.query(Report)
    if report_type:
        query = query.filter(Report.report_type == report_type)
    if start_time:
        query = query.filter(Report.created_at >= start_time)
    if end_time:
        query = query.filter(Report.created_at <= end_time)
    total = query.count()
    query = apply_sort(query, Report, paging["sort_by"], allowed, paging["sort_order"], "created_at")
    offset = (paging["page"] - 1) * paging["page_size"]
    return paginated(query.offset(offset).limit(paging["page_size"]).all(), paging["page"], paging["page_size"], total)


@router.post("", response_model=ReportOut)
def create(payload: ReportCreate, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.REPORTS_MANAGE))) -> Report:
    return create_report(db, payload.title, payload.report_type, payload.format)
