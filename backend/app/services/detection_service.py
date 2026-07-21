from __future__ import annotations

import yaml
from sqlalchemy.orm import Session

from app.models import Detection, Event, Rule


def load_rules(db: Session) -> list[Rule]:
    rules: list[Rule] = []
    sample = yaml.safe_load("""
name: Failed Login Spike
id: failed-login-spike
description: Detects repeated failed authentication attempts.
severity: high
mitre:
  - technique_id: T1110
    name: Brute Force
""")
    rule = Rule(name=sample["name"], rule_id=sample["id"], content="failed-login-spike", enabled=1)
    db.add(rule)
    db.commit()
    rules.append(rule)
    return rules


def run_detections(db: Session) -> list[Detection]:
    detections: list[Detection] = []
    events = db.query(Event).all()
    for event in events:
        if event.event_type == "auth" and "failed" in event.message.lower():
            detection = Detection(
                name="Failed login attempt",
                severity="high",
                rule_id="failed-login-spike",
                description="Repeated authentication failure observed.",
                mitre=[{"technique_id": "T1110", "name": "Brute Force"}],
                enabled=True,
            )
            db.add(detection)
            detections.append(detection)
            break
    db.commit()
    return detections
