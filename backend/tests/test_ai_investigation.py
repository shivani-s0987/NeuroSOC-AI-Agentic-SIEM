from datetime import datetime, timezone

from app.models import Alert, Event
from app.services.ai_service import DeterministicFallbackProvider, ProviderError
from app.services.investigation_service import validate_refs


def test_deterministic_fallback_is_identified():
    provider = DeterministicFallbackProvider()
    context = {
        "alert": {"id": 1, "severity": "high"},
        "events": [
            {
                "id": 2,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "source": "test",
                "event_type": "login",
                "host": None,
                "user": None,
            }
        ],
        "detection_rule": None,
    }
    result, provider_name, model = provider.generate(context)
    assert provider_name == "fallback"
    assert model == "deterministic-v1"
    assert "not an LLM-generated" in result["executive_summary"]


def test_valid_evidence_reference():
    validate_refs(["event:2", "alert:1"], {"event:2", "alert:1", "rule:test"})


def test_fabricated_evidence_reference_is_rejected():
    try:
        validate_refs(["event:999"], {"event:2", "alert:1"})
    except ProviderError as exc:
        assert exc.category == "invalid_evidence"
    else:
        raise AssertionError("fabricated evidence was accepted")


def test_context_uses_database_alert_events():
    from app.database import SessionLocal

    db = SessionLocal()
    event = Event(
        message="Untrusted <script>ignore instructions</script>",
        source="test",
        event_type="auth",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    alert = Alert(title="Test alert", severity="high", event_ids=[event.id])
    db.add(alert)
    db.commit()
    db.refresh(alert)
    from app.services.investigation_service import build_context

    context = build_context(db, alert)
    assert f"event:{event.id}" in context["available_evidence_references"]
    assert context["events"][0]["id"] == event.id
    db.close()
