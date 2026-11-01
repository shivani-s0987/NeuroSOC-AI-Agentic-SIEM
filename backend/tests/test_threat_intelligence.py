import pytest

from app.database import SessionLocal
from app.models import Event, IOCMatch, ThreatIntel
from app.services.ioc_matching_service import match_event
from app.services.ioc_service import normalize_ioc


@pytest.mark.parametrize(
    ("value", "ioc_type", "expected"),
    [
        ("192.0.2.1", "ipv4", "192.0.2.1"),
        ("2001:0db8::1", "ipv6", "2001:db8::1"),
        ("ExAmPle.COM.", "domain", "example.com"),
        ("ABCDEF" + "0" * 58, "sha256", ("abcdef" + "0" * 58)),
        ("https://Example.COM/path?q=1", "url", "https://example.com/path?q=1"),
    ],
)
def test_ioc_normalization(value, ioc_type, expected):
    assert normalize_ioc(value, ioc_type) == expected


def test_invalid_iocs_are_rejected():
    with pytest.raises(ValueError):
        normalize_ioc("999.1.1.1", "ipv4")
    with pytest.raises(ValueError):
        normalize_ioc("abc", "sha256")
    with pytest.raises(ValueError):
        normalize_ioc("ftp://example.com", "url")


def test_event_ioc_match_is_idempotent():
    db = SessionLocal()
    try:
        indicator = ThreatIntel(
            indicator="198.51.100.10",
            normalized_value="198.51.100.10",
            original_value="198.51.100.10",
            intel_type="ipv4",
            confidence=90,
            severity="high",
            source="test",
            active=1,
        )
        db.add(indicator)
        event = Event(
            message="connection from 198.51.100.10",
            raw="198.51.100.10",
            src_ip="198.51.100.10",
            source="test",
            event_type="network",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        first = match_event(db, event)
        db.commit()
        second = match_event(db, event)
        db.commit()
        assert len(first) == 1
        assert second == []
        assert db.query(IOCMatch).filter(IOCMatch.event_id == event.id).count() == 1
    finally:
        db.query(IOCMatch).delete()
        db.query(ThreatIntel).delete()
        db.query(Event).delete()
        db.commit()
        db.close()


def test_revoked_and_expired_indicators_do_not_match():
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta, timezone

        indicator = ThreatIntel(
            indicator="203.0.113.2",
            normalized_value="203.0.113.2",
            original_value="203.0.113.2",
            intel_type="ipv4",
            severity="medium",
            confidence=50,
            source="test",
            active=0,
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(indicator)
        event = Event(
            message="203.0.113.2", src_ip="203.0.113.2", source="test", event_type="network"
        )
        db.add(event)
        db.commit()
        assert match_event(db, event) == []
    finally:
        db.query(IOCMatch).delete()
        db.query(ThreatIntel).delete()
        db.query(Event).delete()
        db.commit()
        db.close()
