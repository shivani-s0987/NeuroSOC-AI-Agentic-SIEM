from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_event() -> None:
    response = client.post(
        "/events",
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
    response = client.post(
        "/auth/register",
        json={
            "username": "analyst",
            "email": "analyst@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 200
    response = client.post(
        "/auth/login",
        json={"username": "analyst", "password": "Password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
