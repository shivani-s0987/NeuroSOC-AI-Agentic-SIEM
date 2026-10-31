from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Detection, Event, Rule

RULES = {
    "failed-login-spike": ("Failed Login Spike", 5, 10, "high", "T1110.001", "Password Guessing"),
    "ssh-brute-force": ("SSH Brute Force", 10, 10, "critical", "T1110.001", "Password Guessing"),
    "repeated-access-denied": ("Repeated Access Denied", 5, 15, "medium", "T1078", "Valid Accounts"),
}


def load_rules(db: Session) -> list[Rule]:
    loaded: list[Rule] = []
    for rule_id, (name, threshold, window, severity, technique, technique_name) in RULES.items():
        rule = db.query(Rule).filter(Rule.rule_id == rule_id).first()
        if rule is None:
            rule = Rule(rule_id=rule_id, name=name, content=f"threshold={threshold};window_minutes={window}", enabled=1)
            db.add(rule)
        loaded.append(rule)
    db.commit()
    return loaded


def _timestamp(value: datetime | None) -> datetime:
    timestamp = value or datetime.now(timezone.utc)
    return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp.astimezone(timezone.utc)


def _group(events: list[Event], field: str) -> dict[str, list[Event]]:
    grouped: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        value = getattr(event, field, None) or "unknown"
        grouped[str(value)].append(event)
    return grouped


def run_detections(db: Session) -> list[Detection]:
    load_rules(db)
    now = datetime.now(timezone.utc)
    events = db.query(Event).all()
    detections: list[Detection] = []

    for rule_id, (name, threshold, window_minutes, severity, technique, technique_name) in RULES.items():
        window = now - timedelta(minutes=window_minutes)
        eligible = [event for event in events if _timestamp(event.timestamp) >= window]
        if rule_id == "failed-login-spike":
            eligible = [e for e in eligible if "failed" in e.message.lower() and str(e.event_type).lower() in {"auth", "authentication", "login"}]
        elif rule_id == "ssh-brute-force":
            eligible = [e for e in eligible if "ssh" in str(e.event_type).lower() and "failed" in e.message.lower()]
        else:
            eligible = [e for e in eligible if "access denied" in e.message.lower() or "permission denied" in e.message.lower()]

        for group_field in ("src_ip", "host", "user"):
            for identity, group in _group(eligible, group_field).items():
                if len(group) < threshold:
                    continue
                fingerprint = f"{rule_id}:{group_field}:{identity}:{window_minutes}"
                existing = db.query(Detection).filter(Detection.rule_id == rule_id, Detection.description.contains(fingerprint)).first()
                if existing:
                    continue
                detection = Detection(
                    name=name,
                    severity=severity,
                    rule_id=rule_id,
                    description=f"{fingerprint} count={len(group)}",
                    mitre=[{"technique_id": technique, "name": technique_name}],
                    enabled=True,
                )
                db.add(detection)
                detections.append(detection)
    db.commit()
    return detections
