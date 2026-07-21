from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportCreate, ReportOut
from app.services.report_service import create_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db)) -> list[Report]:
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.post("", response_model=ReportOut)
def create(payload: ReportCreate, db: Session = Depends(get_db)) -> Report:
    return create_report(db, payload.title, payload.report_type, payload.format)
