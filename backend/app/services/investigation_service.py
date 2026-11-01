from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, Case, Detection, Event, Investigation, InvestigationResult, MITRETechnique, Rule, ThreatIntel
from app.schemas import InvestigationResultSchema
from app.services.ai_service import ProviderError, provider_for_settings, validate_result


SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "cookie", "api_key"}


def _safe_text(value: Any, limit: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\x00", "")
    limit = limit or settings.ai_max_field_chars
    return text[:limit]


def build_context(db: Session, alert: Alert, case: Case | None = None) -> dict[str, Any]:
    event_ids = list(alert.event_ids or [])
    events = db.query(Event).filter(Event.id.in_(event_ids)).limit(settings.ai_context_max_events).all() if event_ids else []
    if len(events) < settings.ai_context_max_events and not event_ids:
        cutoff = None
        if alert.first_observed_at:
            cutoff = alert.first_observed_at
        else:
            cutoff = alert.created_at - timedelta(hours=24) if alert.created_at else None
        query = db.query(Event)
        if cutoff:
            query = query.filter(Event.timestamp >= cutoff)
        events = query.order_by(Event.timestamp.asc()).limit(settings.ai_context_max_events).all()

    event_data = []
    available = [f"alert:{alert.id}"]
    for event in sorted(events, key=lambda item: item.timestamp or datetime.min):
        available.append(f"event:{event.id}")
        event_data.append({
            "id": event.id,
            "timestamp": _iso(event.timestamp),
            "source": _safe_text(event.source),
            "event_type": _safe_text(event.event_type),
            "host": _safe_text(event.host),
            "user": _safe_text(event.user),
            "src_ip": _safe_text(event.src_ip),
            "dst_ip": _safe_text(event.dst_ip),
            "process_name": _safe_text(event.process_name),
            "message": _safe_text(event.message),
            "payload_metadata": _safe_metadata(event.payload_metadata),
        })

    detection = db.query(Detection).filter(Detection.id == ((alert.alert_metadata or {}).get("detection_id"))).first()
    rule = None
    if detection and detection.rule_id:
        rule_model = db.query(Rule).filter(Rule.rule_id == detection.rule_id).first()
        rule = {"id": detection.rule_id, "name": rule_model.name if rule_model else detection.name, "description": detection.description, "mitre": detection.mitre}
        available.append(f"rule:{detection.rule_id}")

    cases = []
    if case:
        cases.append({"id": case.id, "title": case.title, "status": case.status, "summary": _safe_text(case.summary), "evidence": case.evidence[:20]})
        available.append(f"case:{case.id}")

    indicators = {event["src_ip"] for event in event_data if event["src_ip"]} | {event["dst_ip"] for event in event_data if event["dst_ip"]}
    intel = []
    if indicators:
        for item in db.query(ThreatIntel).filter(ThreatIntel.indicator.in_(indicators)).limit(20).all():
            intel.append({"id": item.id, "indicator": item.indicator, "type": item.intel_type, "severity": item.severity, "details": _safe_text(item.details)})
            available.append(f"intel:{item.id}")

    mitre_ids = {mapping.get("technique_id") for mapping in (rule or {}).get("mitre", []) if isinstance(mapping, dict)}
    for technique in db.query(MITRETechnique).filter(MITRETechnique.technique_id.in_(mitre_ids)).all() if mitre_ids else []:
        available.append(f"mitre:{technique.technique_id}")

    return {
        "alert": {"id": alert.id, "title": _safe_text(alert.title), "severity": alert.severity, "status": alert.status, "summary": _safe_text(alert.summary), "created_at": _iso(alert.created_at)},
        "events": event_data,
        "detection_rule": rule,
        "cases": cases,
        "threat_intelligence": intel,
        "available_evidence_references": available,
    }


def _safe_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _safe_text(item) for key, item in value.items() if str(key).lower() not in SENSITIVE_KEYS}


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def execute_investigation(db: Session, investigation: Investigation, context: dict[str, Any]) -> InvestigationResultSchema:
    provider = provider_for_settings()
    raw, provider_name, model_name = provider.generate(context)
    result = validate_result(raw)
    allowed = set(context["available_evidence_references"])
    for finding in result.findings:
        validate_refs(finding.evidence_references, allowed)
    for analysis in result.attack_analysis:
        validate_refs(analysis.evidence_references, allowed)
    for item in result.timeline:
        reference = item.get("reference_id")
        if reference and reference not in allowed:
            raise ProviderError("invalid_evidence", "Investigation referenced unavailable evidence")
    investigation.provider = provider_name
    investigation.model = model_name
    investigation.status = "COMPLETED"
    investigation.completed_at = datetime.now(timezone.utc)
    references = sorted({ref for finding in result.findings for ref in finding.evidence_references} | allowed)
    existing = db.query(InvestigationResult).filter(InvestigationResult.investigation_id == investigation.id).first()
    if existing:
        db.delete(existing)
        db.flush()
    db.add(InvestigationResult(investigation_id=investigation.id, result=result.model_dump(), evidence_references=references))
    return result


def validate_refs(references: list[str], allowed: set[str]) -> None:
    invalid = set(references) - allowed
    if invalid:
        raise ProviderError("invalid_evidence", "AI response referenced unavailable evidence")
