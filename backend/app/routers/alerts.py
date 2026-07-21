from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db)) -> list[Alert]:
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


@router.post("", response_model=AlertOut)
def create_alert(title: str, severity: str = "medium", db: Session = Depends(get_db)) -> Alert:
    alert = Alert(title=title, severity=severity, summary="AI-assisted alert explanation generated")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
