from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ThreatIntel
from app.services.ioc_service import infer_ioc_type, normalize_ioc


def enrich_indicator(db: Session, indicator: str, intel_type: str = "ip") -> ThreatIntel:
    intel = db.query(ThreatIntel).filter(ThreatIntel.indicator == indicator).first()
    if intel:
        return intel
    kind = (
        "ipv4"
        if intel_type.lower() in {"ip", "ipv4"}
        else infer_ioc_type(indicator) or intel_type.lower()
    )
    try:
        normalized = normalize_ioc(indicator, kind)
    except ValueError:
        normalized = indicator.strip().lower()
    intel = ThreatIntel(
        indicator=indicator,
        normalized_value=normalized,
        original_value=indicator,
        intel_type=kind,
        severity="medium",
        details="Locally cached enrichment",
    )
    db.add(intel)
    db.commit()
    db.refresh(intel)
    return intel
