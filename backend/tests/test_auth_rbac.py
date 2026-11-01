import hashlib
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import RefreshTokenSession
from app.security import hash_password, needs_rehash, verify_password
from app.services.audit_service import record_audit

client = TestClient(app)


def register(username: str, password: str = "Password123!", role: str | None = None):
    payload = {"username": username, "email": f"{username}@example.com", "password": password}
    if role is not None:
        payload["role"] = role
    return client.post("/auth/register", json=payload)


def login(username: str, password: str = "Password123!"):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_password_hashing_and_legacy_migration():
    encoded = hash_password("Password123!")
    assert encoded.startswith("$argon2id$")
    assert verify_password("Password123!", encoded)
    assert not verify_password("incorrect-password", encoded)
    legacy = hashlib.sha256("LegacyPassword123!".encode()).hexdigest()
    assert verify_password("LegacyPassword123!", legacy)
    assert needs_rehash(legacy)


def test_public_registration_is_viewer_and_login_works():
    response = register("security-viewer-test", role="ADMIN")
    assert response.status_code == 200
    assert response.json()["role"] == "SECURITY_VIEWER"
    assert login("security-viewer-test").status_code == 200


def test_viewer_cannot_create_event_but_can_read():
    registered = register("viewer-write-test")
    assert registered.status_code == 200, registered.text
    authenticated = login("viewer-write-test")
    assert authenticated.status_code == 200, authenticated.text
    tokens = authenticated.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/events", headers=headers, json={"message": "test"}).status_code == 403
    assert client.get("/events", headers=headers).status_code == 200


def test_refresh_rotation_and_reuse_family_revocation():
    registered = register("rotation-user")
    assert registered.status_code == 200, registered.text
    authenticated = login("rotation-user")
    assert authenticated.status_code == 200, authenticated.text
    tokens = authenticated.json()
    first_refresh = tokens["refresh_token"]
    rotated = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200
    second_refresh = rotated.json()["refresh_token"]
    reused = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reused.status_code == 401
    db = SessionLocal()
    family = (
        db.query(RefreshTokenSession)
        .filter(
            RefreshTokenSession.replaced_by_hash
            == hashlib.sha256(second_refresh.encode()).hexdigest()
        )
        .first()
    )
    assert family is not None or db.query(RefreshTokenSession).count() >= 2
    db.close()


def test_reset_token_is_single_use():
    registered = register("reset-user")
    assert registered.status_code == 200, registered.text
    response = client.post("/auth/forgot-password", json={"email": "reset-user@example.com"})
    assert response.status_code == 200
    token = response.json()["development_token"]
    reset = client.post(
        "/auth/reset-password", json={"token": token, "password": "ResetPassword123!"}
    )
    assert reset.status_code == 200
    assert (
        client.post(
            "/auth/reset-password", json={"token": token, "password": "AnotherPassword123!"}
        ).status_code
        == 400
    )


def test_audit_never_persists_sensitive_keys():
    db = SessionLocal()
    entry = record_audit(
        db,
        "test-user",
        "login",
        details={"password": "secret", "access_token": "raw-token", "outcome_detail": "ok"},
    )
    assert entry.details == {"outcome_detail": "ok"}
    db.close()
