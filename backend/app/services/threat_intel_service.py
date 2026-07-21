from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ThreatIntel


def enrich_indicator(db: Session, indicator: str, intel_type: str = "ip") -> ThreatIntel:
    intel = db.query(ThreatIntel).filter(ThreatIntel.indicator == indicator).first()
    if intel:
        return intel
    intel = ThreatIntel(
        indicator=indicator,
        intel_type=intel_type,
        severity="medium",
        details="Locally cached enrichment",
    )
    db.add(intel)
    db.commit()
    db.refresh(intel)
    return intel
