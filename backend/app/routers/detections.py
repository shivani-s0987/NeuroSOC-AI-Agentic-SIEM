from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Rule
from app.schemas import DetectionOut, Paginated
from app.services.detection_service import load_rules, run_detections
from app.core.pagination import apply_sort, paginated, pagination_params

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("", response_model=Paginated[DetectionOut])
def list_detections(db: Session = Depends(get_db), paging: dict = Depends(pagination_params), severity: str | None = Query(None), rule_id: str | None = Query(None)):
    allowed = {"id", "created_at", "name", "severity", "rule_id"}
    if paging["sort_by"] not in allowed:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of: {sorted(allowed)}")
    query = db.query(Detection)
    if severity:
        query = query.filter(Detection.severity == severity)
    if rule_id:
        query = query.filter(Detection.rule_id == rule_id)
    total = query.count()
    query = apply_sort(query, Detection, paging["sort_by"], allowed, paging["sort_order"], "created_at")
    offset = (paging["page"] - 1) * paging["page_size"]
    return paginated(query.offset(offset).limit(paging["page_size"]).all(), paging["page"], paging["page_size"], total)


@router.post("/run")
def run_detection(db: Session = Depends(get_db)) -> dict[str, int]:
    load_rules(db)
    detections = run_detections(db)
    return {"detections": len(detections)}


@router.get("/rules", response_model=list[dict])
def list_rules(db: Session = Depends(get_db)) -> list[Rule]:
    return db.query(Rule).all()
