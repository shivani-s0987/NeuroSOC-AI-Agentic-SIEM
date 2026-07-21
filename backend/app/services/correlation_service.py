from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models import Event


def build_timeline(db: Session, host: str | None = None) -> list[dict[str, Any]]:
    query = db.query(Event)
    if host:
        query = query.filter(Event.host == host)
    events = query.order_by(Event.timestamp.asc()).all()
    timeline = []
    for event in events:
        timeline.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "host": event.host,
                "user": event.user,
                "message": event.message,
                "severity": event.severity,
            }
        )
    return timeline


def correlate_events(db: Session) -> dict[str, list[Event]]:
    groups: dict[str, list[Event]] = defaultdict(list)
    for event in db.query(Event).all():
        key = str(event.host or event.user or event.src_ip or "unknown")
        groups[key].append(event)
    return dict(groups)
