from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Event

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict[str, int]:
    return {
        "events": db.query(Event).count(),
        "alerts": db.query(Alert).count(),
        "high_severity": db.query(Alert).filter(Alert.severity == "high").count(),
    }
