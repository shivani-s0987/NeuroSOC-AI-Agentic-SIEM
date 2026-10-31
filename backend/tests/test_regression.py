import hashlib
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Detection, Event, Rule, User
from app.security import hash_password, verify_password
from app.services.detection_service import run_detections
from app.services.ingest_service import ingest_file, ingest_file_report, normalize_timestamp

client = TestClient(app)


def analyst_headers(username: str = "regression-analyst") -> dict[str, str]:
    registered = client.post("/auth/register", json={"username": username, "email": f"{username}@example.com", "password": "Password123!"})
    assert registered.status_code == 200, registered.text
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    user.role = "SOC_ANALYST"
    db.commit()
    db.close()
    login = client.post("/auth/login", json={"username": username, "password": "Password123!"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_argon2_hash_and_sha256_legacy_verification():
    password = "TestPassword123!"
    encoded = hash_password(password)
    assert encoded.startswith("$argon2")
    assert verify_password(password, encoded)
    legacy = hashlib.sha256(password.encode()).hexdigest()
    assert verify_password(password, legacy)


def test_event_metadata_round_trip():
    response = client.post("/events", headers=analyst_headers(), json={"message": "metadata event", "metadata": {"source_ip": "192.0.2.1"}})
    assert response.status_code == 200
    assert response.json()["metadata"] == {"source_ip": "192.0.2.1"}


def test_timestamp_normalization_to_utc():
    timestamp = normalize_timestamp("2026-10-31T12:00:00+02:00")
    assert timestamp.isoformat() == "2026-10-31T10:00:00+00:00"


def test_json_ingestion_maps_payload_metadata():
    db = SessionLocal()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "events.jsonl"
        path.write_text('{"message":"failed login","event_type":"auth","timestamp":"2026-10-31T12:00:00Z","metadata":{"attempt":1}}\n')
        events = ingest_file(db, str(path))
        assert len(events) == 1
        assert events[0].payload_metadata == {"attempt": 1}
    db.close()


def test_versioned_events_and_pagination_contract():
    response = client.get("/api/v1/events?page=1&page_size=10&sort_by=timestamp&sort_order=desc", headers=analyst_headers("pagination-analyst"))
    assert response.status_code == 200
    assert "items" in response.json()
    assert "pagination" in response.json()


def test_invalid_event_sort_is_rejected():
    response = client.get("/api/v1/events?sort_by=message", headers=analyst_headers("sort-analyst"))
    assert response.status_code == 422


def test_explicit_csv_mapping_and_rejected_rows():
    db = SessionLocal()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "events.csv"
        path.write_text("timestamp,message,severity,src_ip,metadata\n2026-10-31T12:00:00Z,failed login,high,198.51.100.20,{\"attempt\":1}\n2026-10-31T12:00:00Z,,low,198.51.100.21,{}\n")
        report = ingest_file_report(db, str(path))
        assert report.imported == 1
        assert report.rejected == 1
        assert report.errors[0]["row"] == 3
    db.close()


def test_detection_threshold_and_rule_deduplication():
    db = SessionLocal()
    db.query(Detection).delete()
    db.query(Rule).delete()
    for index in range(5):
        db.add(Event(message="failed login", event_type="auth", severity="high", src_ip="198.51.100.20"))
    db.commit()

    first = run_detections(db)
    second = run_detections(db)
    assert first
    assert second == []
    db.close()
