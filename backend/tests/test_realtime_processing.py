import json
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Event, Notification, ProcessingJob
from app.security import create_token, hash_password
from app.models import User


def auth_headers(client, username="realtime-user", role="SOC_ANALYST"):
    db = SessionLocal()
    if not db.query(User).filter(User.username == username).first():
        db.add(
            User(
                username=username,
                email=f"{username}@example.com",
                password_hash=hash_password("password123456"),
                role=role,
            )
        )
        db.commit()
    db.close()
    return {"Authorization": f"Bearer {create_token(username, role)}"}


def test_ingest_is_durable_and_idempotent():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    headers = auth_headers(client)
    payload = {"message": "login failed", "source": "idp", "idempotency_key": "idem-123"}
    first = client.post("/events/ingest", headers=headers, json=payload)
    second = client.post("/events/ingest", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    db = SessionLocal()
    assert db.query(Event).filter(Event.idempotency_key == "idem-123").count() == 1
    event = db.query(Event).filter(Event.idempotency_key == "idem-123").one()
    assert db.query(ProcessingJob).filter(ProcessingJob.event_id == event.id).count() == 1
    assert (
        db.query(Notification)
        .filter(
            Notification.event_type == "event.created",
            Notification.resource_id == str(event.id),
        )
        .count()
        == 1
    )
    db.close()


def test_processing_status():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    headers = auth_headers(client, username="status-user")
    response = client.post("/events/ingest", headers=headers, json={"message": "status test"})
    event_id = response.json()["id"]
    status = client.get(f"/events/processing-status/{event_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["event_id"] == event_id
    assert status.json()["status"] in {"pending", "processing", "retrying", "processed", "failed"}


def test_publish_notification_serializes_canonical_payload_and_publishes(monkeypatch):
    from app.services.realtime_service import publish_realtime_notification

    published = {}

    class RedisClient:
        def publish(self, channel, payload):
            published["channel"] = channel
            published["payload"] = payload
            return 1

    class Redis:
        @staticmethod
        def from_url(_url):
            return RedisClient()

    import redis

    monkeypatch.setattr(redis.Redis, "from_url", Redis.from_url)
    notification = Notification(
        notification_id="notification-1",
        event_type="event.created",
        schema_version=1,
        timestamp=datetime.now(timezone.utc),
        resource_type="event",
        resource_id="42",
        data={"severity": "high"},
    )

    publish_realtime_notification(notification)

    assert published["channel"] == "neurosoc:notifications"
    payload = json.loads(published["payload"])
    assert payload["event_id"] == "notification-1"
    assert payload["resource"] == {"type": "event", "id": "42"}
