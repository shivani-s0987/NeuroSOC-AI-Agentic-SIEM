from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.database import get_db
from app.models import IOCMatch, MITRETechnique, ThreatIntel
from app.security import require_permission
from app.services.ioc_service import normalize_ioc
from app.services.provider_service import URLhausProvider

router = APIRouter(prefix="/threat-intelligence", tags=["threat-intelligence"])


def _ioc_dict(row: ThreatIntel) -> dict[str, Any]:
    expired = bool(row.expires_at and row.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc))
    return {
        "id": row.id, "type": row.intel_type, "value": row.normalized_value,
        "original_value": row.original_value or row.indicator, "confidence": row.confidence,
        "severity": row.severity, "description": row.description or row.details,
        "tags": row.tags or [], "source": row.source, "first_seen": row.first_seen,
        "last_seen": row.last_seen, "expires_at": row.expires_at,
        "active": bool(row.active), "revoked": bool(row.revoked_at), "expired": expired,
        "external_reference": row.external_reference, "provenance": row.provenance or {},
        "created_at": row.created_at, "updated_at": row.updated_at,
    }


@router.get("/indicators")
def list_indicators(
    q: str | None = None,
    ioc_type: str | None = Query(None, alias="type"),
    severity: str | None = None,
    source: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.DETECTIONS_READ)),
) -> dict[str, Any]:
    query = db.query(ThreatIntel)
    if ioc_type:
        query = query.filter(ThreatIntel.intel_type == ioc_type.lower())
    if severity:
        query = query.filter(ThreatIntel.severity == severity.lower())
    if source:
        query = query.filter(ThreatIntel.source == source)
    if q:
        query = query.filter(or_(ThreatIntel.normalized_value.ilike(f"%{q}%"), ThreatIntel.original_value.ilike(f"%{q}%")))
    if status == "active":
        query = query.filter(ThreatIntel.active == 1, ThreatIntel.revoked_at.is_(None),
                             or_(ThreatIntel.expires_at.is_(None), ThreatIntel.expires_at > datetime.now(timezone.utc)))
    elif status == "revoked":
        query = query.filter(ThreatIntel.revoked_at.is_not(None))
    elif status == "expired":
        query = query.filter(ThreatIntel.expires_at <= datetime.now(timezone.utc))
    total = query.count()
    rows = query.order_by(ThreatIntel.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_ioc_dict(row) for row in rows], "pagination": {"page": page, "page_size": page_size, "total": total}}


@router.get("/indicators/{indicator_id}")
def indicator_detail(indicator_id: int, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> dict[str, Any]:
    row = db.get(ThreatIntel, indicator_id)
    if row is None:
        raise HTTPException(404, "Indicator not found")
    matches = db.query(IOCMatch).filter(IOCMatch.indicator_id == indicator_id).order_by(IOCMatch.matched_at.desc()).all()
    return {
        **_ioc_dict(row),
        "matches": [{
            "id": match.id, "event_id": match.event_id, "alert_id": match.alert_id,
            "match_type": match.match_type, "matched_field": match.matched_field,
            "matched_value": match.matched_value, "matched_at": match.matched_at,
            "confidence": match.confidence, "severity": match.severity,
        } for match in matches],
    }


@router.post("/indicators")
def create_indicator(payload: dict[str, Any], db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, Any]:
    try:
        original = str(payload["value"]).strip()
        ioc_type = str(payload["type"]).lower()
        normalized = normalize_ioc(original, ioc_type)
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    if db.query(ThreatIntel).filter(ThreatIntel.normalized_value == normalized).first():
        raise HTTPException(409, detail="Indicator already exists")
    now = datetime.now(timezone.utc)
    row = ThreatIntel(
        indicator=normalized, normalized_value=normalized, original_value=original,
        intel_type=ioc_type, confidence=max(0, min(100, int(payload.get("confidence", 50)))),
        severity=str(payload.get("severity", "medium")).lower(),
        description=payload.get("description"), tags=payload.get("tags", []),
        source=str(payload.get("source", "manual")), first_seen=payload.get("first_seen") or now,
        last_seen=payload.get("last_seen") or now, expires_at=payload.get("expires_at"),
        external_reference=payload.get("external_reference"),
        provenance={"source": "manual", "created_by": str(_actor.username)},
        active=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _ioc_dict(row)


@router.post("/indicators/{indicator_id}/revoke")
def revoke_indicator(indicator_id: int, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, Any]:
    row = db.get(ThreatIntel, indicator_id)
    if row is None:
        raise HTTPException(404, "Indicator not found")
    row.revoked_at = datetime.now(timezone.utc)
    row.active = 0
    db.commit()
    return _ioc_dict(row)


@router.post("/indicators/import")
async def import_indicators(payload: dict[str, Any], db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_MANAGE))) -> dict[str, Any]:
    content = payload.get("content", "")
    format_name = str(payload.get("format", "json")).lower()
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if format_name == "json":
        try:
            parsed = json.loads(content)
            records = parsed if isinstance(parsed, list) else parsed.get("indicators", [])
        except json.JSONDecodeError as exc:
            raise HTTPException(422, detail=f"Invalid JSON: {exc.msg}") from exc
    elif format_name == "csv":
        for index, record in enumerate(csv.DictReader(io.StringIO(content)), start=2):
            if record:
                records.append(record)
    else:
        raise HTTPException(422, "format must be json or csv")
    imported = updated = duplicates = rejected = 0
    for index, record in enumerate(records):
        try:
            result = create_indicator(record, db=db, _actor=_actor)
            imported += 1
        except HTTPException as exc:
            if exc.status_code == 409:
                duplicates += 1
            else:
                rejected += 1
                errors.append({"record": index + 1, "message": exc.detail})
    db.commit()
    return {"total": len(records), "imported": imported, "updated": updated, "duplicates": duplicates,
            "rejected": rejected, "errors": errors}


@router.get("/providers")
def providers() -> dict[str, list[dict[str, Any]]]:
    return {"items": [{"name": "urlhaus", "configured": True, "live_lookup": True, "description": "Abuse.ch URLhaus API"}]}


@router.post("/providers/{provider}/lookup")
def provider_lookup(provider: str, payload: dict[str, Any], _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> dict[str, Any]:
    if provider != "urlhaus":
        raise HTTPException(404, "Provider not found")
    value = str(payload.get("value", "")).strip()
    ioc_type = str(payload.get("type", "domain")).lower()
    try:
        normalized = normalize_ioc(value, ioc_type)
        return URLhausProvider().lookup(normalized, ioc_type)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/matches/event/{event_id}")
def event_matches(event_id: int, db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> list[dict[str, Any]]:
    return [{"indicator_id": row.indicator_id, "matched_field": row.matched_field, "matched_value": row.matched_value,
             "match_type": row.match_type, "confidence": row.confidence, "severity": row.severity,
             "provenance": row.provenance} for row in db.query(IOCMatch).filter(IOCMatch.event_id == event_id).all()]


mitre_router = APIRouter(prefix="/mitre", tags=["mitre"])


@mitre_router.get("/techniques")
def techniques(q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500),
               db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.DETECTIONS_READ))) -> dict[str, Any]:
    query = db.query(MITRETechnique)
    if q:
        query = query.filter(or_(MITRETechnique.technique_id.ilike(f"%{q}%"), MITRETechnique.name.ilike(f"%{q}%")))
    total = query.count()
    rows = query.order_by(MITRETechnique.technique_id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": row.id, "technique_id": row.technique_id, "name": row.name,
                       "description": row.description, "platforms": row.platforms or [], "tactics": row.tactics or [],
                       "revoked": bool(row.revoked), "deprecated": bool(row.deprecated)} for row in rows],
            "pagination": {"page": page, "page_size": page_size, "total": total}}
