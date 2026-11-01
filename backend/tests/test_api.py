import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def register_login(username: str = "api-analyst") -> str:
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "Password123!"},
    )
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    user.role = "SOC_ANALYST"
    db.commit()
    db.close()
    response = client.post("/auth/login", json={"username": username, "password": "Password123!"})
    return response.json()["access_token"]


def test_create_event() -> None:
    token = register_login("api-event-user")
    response = client.post(
        "/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Failed login",
            "event_type": "auth",
            "severity": "high",
            "host": "server-1",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Failed login"


def test_register_and_login() -> None:
    username = f"analyst-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    response = client.post(
        "/auth/login",
        json={"username": username, "password": "Password123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
