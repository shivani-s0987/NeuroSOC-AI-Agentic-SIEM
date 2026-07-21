from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Rule
from app.schemas import DetectionOut
from app.services.detection_service import load_rules, run_detections

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("", response_model=list[DetectionOut])
def list_detections(db: Session = Depends(get_db)) -> list[Detection]:
    return db.query(Detection).order_by(Detection.created_at.desc()).all()


@router.post("/run")
def run_detection(db: Session = Depends(get_db)) -> dict[str, int]:
    load_rules(db)
    detections = run_detections(db)
    return {"detections": len(detections)}


@router.get("/rules", response_model=list[dict])
def list_rules(db: Session = Depends(get_db)) -> list[Rule]:
    return db.query(Rule).all()
