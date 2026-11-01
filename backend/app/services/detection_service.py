from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.detection_engine import correlate, load_yaml, parse_duration
from app.models import Alert, Detection, Event, Rule
from app.services.realtime_service import publish_notification

RULE_DIRECTORY = Path(__file__).resolve().parent.parent / "detection_rules"


def load_rules(db: Session) -> list[Rule]:
    loaded: list[Rule] = []
    for path in sorted(RULE_DIRECTORY.glob("*.yml")):
        try:
            parsed = load_yaml(path)
            rule = db.query(Rule).filter(Rule.rule_id == parsed.id).first()
            if rule is None:
                rule = Rule(rule_id=parsed.id, name=parsed.name, description=parsed.description,
                            content=path.read_text(encoding="utf-8"), severity=parsed.severity,
                            version=parsed.version, enabled=int(parsed.enabled))
                db.add(rule)
            loaded.append(rule)
        except Exception as exc:
            logging.getLogger("neurosoc.detection").error("invalid rule path=%s error=%s", path.name, exc)
    db.commit()
    return loaded


def run_detections(db: Session, as_of: datetime | None = None) -> list[Detection]:
    load_rules(db)
    detections: list[Detection] = []
    for path in sorted(RULE_DIRECTORY.glob("*.yml")):
        try:
            rule = load_yaml(path)
            if not rule.enabled:
                continue
            timeframe = parse_duration(rule.detection["timeframe"])
            cutoff = (as_of or datetime.now(timezone.utc)) - timeframe
            events = db.query(Event).filter(Event.timestamp >= cutoff).order_by(Event.timestamp.asc()).all()
            for match in correlate(rule, events, as_of=as_of):
                existing = db.query(Detection).filter(Detection.fingerprint == match.fingerprint).first()
                timestamps = [event.timestamp for event in events if event.id in match.event_ids]
                if existing:
                    existing.event_ids = sorted(set(existing.event_ids or []) | list(match.event_ids))
                    existing.last_observed_at = max(timestamps) if timestamps else existing.last_observed_at
                    continue
                detection = Detection(name=rule.name, severity=rule.severity, rule_id=rule.id,
                                      description=rule.description, mitre=[{"technique_id": value, "name": "ATT&CK mapping"} for value in rule.mitre.techniques],
                                      enabled=True, fingerprint=match.fingerprint, event_ids=list(match.event_ids),
                                      first_observed_at=match.first_observed, last_observed_at=match.last_observed)
                alert = db.query(Alert).filter(Alert.fingerprint == match.fingerprint).first()
                if alert is None:
                    alert = Alert(title=rule.name, severity=rule.severity, source="detection",
                                 summary=f"{rule.description} Recommended action: {rule.response.recommended_action}",
                                 event_ids=list(match.event_ids), first_observed_at=match.first_observed,
                                 last_observed_at=match.last_observed, fingerprint=match.fingerprint,
                                 status="open", alert_metadata={"grouping": match.context, "mitre": rule.mitre.model_dump()})
                    db.add(alert)
                    db.flush()
                    publish_notification(db, "alert.created", "alert", alert.id, {
                        "severity": alert.severity,
                        "status": alert.status,
                    })
                db.add(detection)
                detections.append(detection)
        except Exception as exc:
            logging.getLogger("neurosoc.detection").error("rule=%s execution_failed=%s", path.stem, exc)
    db.commit()
    return detections
