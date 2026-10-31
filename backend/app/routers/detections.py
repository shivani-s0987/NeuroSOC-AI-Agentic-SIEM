from fastapi import APIRouter, Depends, HTTPException, Query
import yaml
from pathlib import Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Rule, RuleVersion
from app.schemas import DetectionOut, Paginated
from app.services.detection_service import load_rules, run_detections
from app.core.pagination import apply_sort, paginated, pagination_params
from app.core.permissions import Permission
from app.security import require_permission
from app.detection_engine import Rule as DetectionRule, correlate

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("", response_model=Paginated[DetectionOut])
def list_detections(db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ)), paging: dict = Depends(pagination_params), severity: str | None = Query(None), rule_id: str | None = Query(None)):
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
def run_detection(db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, int]:
    load_rules(db)
    detections = run_detections(db)
    return {"detections": len(detections)}


@router.get("/rules")
def list_rules(db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> list[dict]:
    load_rules(db)
    return [{"id": item.rule_id, "name": item.name, "description": item.description,
             "severity": item.severity, "version": item.version, "enabled": bool(item.enabled)}
            for item in db.query(Rule).order_by(Rule.rule_id).all()]


@router.get("/rules/{rule_id}")
def get_rule(rule_id: str, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> dict:
    rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"id": rule.rule_id, "name": rule.name, "description": rule.description,
            "severity": rule.severity, "version": rule.version, "enabled": bool(rule.enabled), "content": rule.content}


@router.post("/rules")
def create_rule(payload: dict, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict:
    try:
        parsed = DetectionRule.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if db.query(Rule).filter(Rule.rule_id == parsed.id).first():
        raise HTTPException(status_code=409, detail="Rule ID already exists")
    content = yaml.safe_dump(payload, sort_keys=False)
    rule = Rule(rule_id=parsed.id, name=parsed.name, description=parsed.description, content=content,
                severity=parsed.severity, version=parsed.version, enabled=int(parsed.enabled))
    db.add(rule)
    db.flush()
    db.add(RuleVersion(rule_id=parsed.id, version=parsed.version, content=content))
    Path(__file__).resolve().parent.parent.joinpath("detection_rules", f"{parsed.id}.yml").write_text(content, encoding="utf-8")
    db.commit()
    return {"id": parsed.id, "version": parsed.version}


@router.get("/rules/{rule_id}/history")
def rule_history(rule_id: str, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> list[dict]:
    return [{"version": row.version, "created_at": row.created_at.isoformat() if row.created_at else None}
            for row in db.query(RuleVersion).filter(RuleVersion.rule_id == rule_id).order_by(RuleVersion.version.desc()).all()]


@router.post("/rules/validate")
def validate_rule(payload: dict, _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict:
    try:
        rule = DetectionRule.model_validate(payload)
        return {"valid": True, "rule_id": rule.id}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/rules/{rule_id}/enable")
def enable_rule(rule_id: str, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, object]:
    rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.enabled = 1
    db.commit()
    return {"rule_id": rule_id, "enabled": True}


@router.post("/rules/{rule_id}/disable")
def disable_rule(rule_id: str, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, object]:
    rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.enabled = 0
    db.commit()
    return {"rule_id": rule_id, "enabled": False}


@router.post("/rules/{rule_id}/test")
def test_rule(rule_id: str, events: list[dict], _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> dict[str, object]:
    rule = None
    try:
        from app.services.detection_service import RULE_DIRECTORY
        path = RULE_DIRECTORY / f"{rule_id}.yml"
        from app.detection_engine import load_yaml
        rule = load_yaml(path)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=f"Rule unavailable or invalid: {exc}") from exc
    matches = correlate(rule, events)
    return {"rule_id": rule_id, "matched_groups": len(matches), "event_count": sum(len(match.event_ids) for match in matches)}
