from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Alert, Event, User

client = TestClient(app)


def register_analyst(username: str) -> str:
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    user.role = "SOC_ANALYST"
    db.commit()
    db.close()
    return client.post(
        "/auth/login", json={"username": username, "password": "Password123!"}
    ).json()["access_token"]


def test_start_and_retrieve_fallback_investigation():
    token = register_analyst("ai-investigator")
    db = SessionLocal()
    event = Event(
        message="Authentication failure",
        event_type="auth",
        severity="high",
        host="host-a",
        user="alice",
    )
    db.add(event)
    db.flush()
    alert = Alert(title="Repeated login failures", severity="high", event_ids=[event.id])
    db.add(alert)
    db.commit()
    alert_id = alert.id
    db.close()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        f"/api/v1/assistant/alerts/{alert_id}/investigate", headers=headers, json={}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["fallback"] is True
    assert body["result"]["event_count"] == 1
    retrieved = client.get(f"/api/v1/assistant/investigations/{body['id']}", headers=headers)
    assert retrieved.status_code == 200


def test_feedback_and_unauthorized_access():
    token = register_analyst("ai-feedback")
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    alert = Alert(title="Feedback alert", severity="medium")
    db.add(alert)
    db.commit()
    alert_id = alert.id
    db.close()
    started = client.post(
        f"/api/v1/assistant/alerts/{alert_id}/investigate", headers=headers, json={}
    )
    investigation_id = started.json()["id"]
    feedback = client.post(
        f"/api/v1/assistant/investigations/{investigation_id}/feedback",
        headers=headers,
        json={"category": "helpful", "comments": "Useful evidence summary"},
    )
    assert feedback.status_code == 200
    assert client.get(f"/api/v1/assistant/investigations/{investigation_id}").status_code == 401
