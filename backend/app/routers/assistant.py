from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.database import get_db
from app.models import Alert, Case, Investigation, InvestigationFeedback, InvestigationResult, User
from app.schemas import (
    InvestigationCreate,
    InvestigationFeedbackCreate,
    InvestigationOut,
    InvestigationResultSchema,
    Paginated,
)
from app.services.ai_service import ProviderError, build_assistant_response
from app.services.investigation_service import build_context, execute_investigation
from app.security import require_permission

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/explain")
def explain(
    payload: dict[str, str], _actor=Depends(require_permission(Permission.EVENTS_READ))
) -> dict[str, object]:
    prompt = payload.get("prompt", "Explain this alert")
    return build_assistant_response(prompt, {"context": payload})


def serialize_investigation(db: Session, investigation: Investigation) -> InvestigationOut:
    stored = (
        db.query(InvestigationResult)
        .filter(InvestigationResult.investigation_id == investigation.id)
        .first()
    )
    result = InvestigationResultSchema.model_validate(stored.result) if stored else None
    refs = stored.evidence_references if stored else []
    return InvestigationOut.model_validate(
        {
            **{
                field: getattr(investigation, field)
                for field in (
                    "id",
                    "alert_id",
                    "case_id",
                    "status",
                    "provider",
                    "model",
                    "started_at",
                    "completed_at",
                    "error_category",
                    "version",
                )
            },
            "result": result,
            "evidence_references": refs,
            "fallback": investigation.provider == "fallback",
        }
    )


def run(db: Session, investigation: Investigation) -> None:
    alert = db.query(Alert).filter(Alert.id == investigation.alert_id).first()
    if alert is None:
        investigation.status = "FAILED"
        investigation.error_category = "alert_not_found"
        investigation.completed_at = datetime.now(timezone.utc)
        db.commit()
        return
    case = (
        db.query(Case).filter(Case.id == investigation.case_id).first()
        if investigation.case_id
        else None
    )
    context = build_context(db, alert, case)
    investigation.status = "IN_PROGRESS"
    try:
        execute_investigation(db, investigation, context)
    except ProviderError as exc:
        investigation.status = "FAILED"
        investigation.error_category = exc.category
        investigation.completed_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/investigations", response_model=InvestigationOut)
def start_investigation(
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    if payload.alert_id is None:
        raise HTTPException(status_code=422, detail="alert_id is required")
    alert = db.query(Alert).filter(Alert.id == payload.alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if payload.case_id and db.query(Case).filter(Case.id == payload.case_id).first() is None:
        raise HTTPException(status_code=404, detail="Case not found")
    active = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id == payload.alert_id,
            Investigation.status.in_(["PENDING", "IN_PROGRESS"]),
        )
        .first()
    )
    if active and not payload.force_rerun:
        return serialize_investigation(db, active)
    rerun_of = active.id if payload.force_rerun and active else None
    version = db.query(Investigation).filter(Investigation.alert_id == payload.alert_id).count() + 1
    investigation = Investigation(
        alert_id=payload.alert_id,
        case_id=payload.case_id,
        initiated_by=user.id,
        status="PENDING",
        provider="pending",
        version=version,
        rerun_of=rerun_of,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    run(db, investigation)
    db.refresh(investigation)
    return serialize_investigation(db, investigation)


@router.get("/investigations", response_model=Paginated[InvestigationOut])
def list_investigations(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = db.query(Investigation).filter(Investigation.initiated_by == user.id)
    total = query.count()
    items = (
        query.order_by(Investigation.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_investigation(db, item) for item in items],
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


@router.get("/investigations/{investigation_id}", response_model=InvestigationOut)
def get_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id, Investigation.initiated_by == user.id)
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return serialize_investigation(db, investigation)


@router.post("/investigations/{investigation_id}/retry", response_model=InvestigationOut)
def retry_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    previous = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id, Investigation.initiated_by == user.id)
        .first()
    )
    if not previous:
        raise HTTPException(status_code=404, detail="Investigation not found")
    investigation = Investigation(
        alert_id=previous.alert_id,
        case_id=previous.case_id,
        initiated_by=user.id,
        status="PENDING",
        provider="pending",
        version=previous.version + 1,
        rerun_of=previous.id,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    run(db, investigation)
    db.refresh(investigation)
    return serialize_investigation(db, investigation)


@router.post("/alerts/{alert_id}/investigate", response_model=InvestigationOut)
def investigate_alert(
    alert_id: int,
    payload: InvestigationCreate | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    payload = payload or InvestigationCreate(alert_id=alert_id)
    payload.alert_id = alert_id
    return start_investigation(payload, db, user)


@router.get("/alerts/{alert_id}/investigation", response_model=InvestigationOut)
def latest_alert_investigation(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id == alert_id,
            Investigation.initiated_by == user.id,
        )
        .order_by(Investigation.started_at.desc(), Investigation.id.desc())
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return serialize_investigation(db, investigation)


@router.post("/investigations/{investigation_id}/feedback")
def submit_feedback(
    investigation_id: int,
    payload: InvestigationFeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.ALERTS_READ)),
):
    investigation = (
        db.query(Investigation)
        .filter(Investigation.id == investigation_id, Investigation.initiated_by == user.id)
        .first()
    )
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    feedback = InvestigationFeedback(
        investigation_id=investigation_id,
        user_id=user.id,
        category=payload.category,
        comments=payload.comments,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "id": feedback.id,
        "investigation_id": investigation_id,
        "category": feedback.category,
        "created_at": feedback.created_at,
    }
