from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Event, IOCMatch, ThreatIntel
from app.services.ioc_service import extract_event_candidates, normalize_ioc


def match_event(db: Session, event: Event) -> list[IOCMatch]:
    now = datetime.now(timezone.utc)
    created: list[IOCMatch] = []
    seen: set[tuple[int, str]] = set()
    for field, ioc_type, value in extract_event_candidates(event):
        if not ioc_type:
            continue
        try:
            normalized = normalize_ioc(value, ioc_type)
        except ValueError:
            continue
        indicator = (
            db.query(ThreatIntel)
            .filter(
                ThreatIntel.normalized_value == normalized,
                ThreatIntel.active == 1,
                ThreatIntel.revoked_at.is_(None),
            )
            .filter((ThreatIntel.expires_at.is_(None)) | (ThreatIntel.expires_at > now))
            .first()
        )
        if indicator is None:
            continue
        already_matched = (
            db.query(IOCMatch)
            .filter(
                IOCMatch.event_id == event.id,
                IOCMatch.indicator_id == indicator.id,
            )
            .first()
        )
        if already_matched or indicator.id in {item.indicator_id for item in created}:
            continue
        key = (indicator.id, field)
        if key in seen:
            continue
        seen.add(key)
        existing = (
            db.query(IOCMatch)
            .filter(
                IOCMatch.event_id == event.id,
                IOCMatch.indicator_id == indicator.id,
                IOCMatch.matched_field == field,
            )
            .first()
        )
        if existing:
            continue
        match = IOCMatch(
            event_id=event.id,
            indicator_id=indicator.id,
            match_type=ioc_type,
            matched_field=field,
            matched_value=normalized,
            confidence=indicator.confidence,
            severity=indicator.severity,
            provenance={
                "source": indicator.source,
                "indicator_provenance": indicator.provenance or {},
            },
        )
        db.add(match)
        created.append(match)
    db.flush()
    return created
