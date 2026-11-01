from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Event

CSV_FIELDS = {
    "message",
    "timestamp",
    "source",
    "event_type",
    "severity",
    "host",
    "user",
    "src_ip",
    "dst_ip",
    "process_name",
    "raw",
    "metadata",
}
CSV_ALIASES = {
    "username": "user",
    "ip": "src_ip",
    "type": "event_type",
    "payload_metadata": "metadata",
}


def normalize_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp: {value}") from exc
    else:
        raise ValueError("Timestamp must be an ISO-8601 string")
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def parse_line(line: str) -> dict[str, Any]:
    text = line.strip()
    if not text:
        return {}
    if text.startswith("{"):
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("JSON record must be an object")
        if not payload.get("message"):
            raise ValueError("message is required")
        timestamp = (
            normalize_timestamp(payload.get("timestamp"))
            if payload.get("timestamp")
            else datetime.now(timezone.utc)
        )
        return {
            "source": payload.get("source", "json"),
            "event_type": payload.get("event_type", "json"),
            "severity": payload.get("severity", "info"),
            "host": payload.get("host"),
            "user": payload.get("user"),
            "src_ip": payload.get("src_ip"),
            "dst_ip": payload.get("dst_ip"),
            "process_name": payload.get("process_name"),
            "message": payload["message"],
            "raw": text,
            "timestamp": timestamp,
            "payload_metadata": payload.get("metadata", payload.get("payload_metadata", {})),
        }

    if "," in text:
        parts = [part.strip() for part in text.split(",")]
        if len(parts) >= 3:
            return {
                "source": "csv",
                "event_type": "csv",
                "severity": "info",
                "message": parts[-1],
                "raw": text,
                "payload_metadata": {"csv": parts},
                "timestamp": datetime.now(timezone.utc),
            }
    match = re.match(r"^(?P<ts>\S+) (?P<host>\S+) (?P<proc>\S+): (?P<msg>.+)$", text)
    if match:
        try:
            timestamp = normalize_timestamp(match.group("ts"))
        except ValueError:
            timestamp = datetime.now(timezone.utc)
        return {
            "source": "syslog",
            "event_type": "syslog",
            "severity": "info",
            "host": match.group("host"),
            "process_name": match.group("proc"),
            "message": match.group("msg"),
            "raw": text,
            "timestamp": timestamp,
        }
    return {
        "source": "custom",
        "event_type": "custom",
        "severity": "info",
        "message": text,
        "raw": text,
        "timestamp": datetime.now(timezone.utc),
    }


def parse_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for raw_name, raw_value in row.items():
        if raw_name is None:
            continue
        name = raw_name.strip().lower()
        name = CSV_ALIASES.get(name, name)
        if name not in CSV_FIELDS:
            raise ValueError(f"Unsupported CSV field: {raw_name}")
        normalized[name] = raw_value.strip() if isinstance(raw_value, str) else raw_value
    if not normalized.get("message"):
        raise ValueError("CSV message is required")
    normalized["timestamp"] = normalize_timestamp(
        normalized["timestamp"] if normalized.get("timestamp") else datetime.now(timezone.utc)
    )
    normalized["severity"] = normalized.get("severity", "info").lower()
    if normalized["severity"] not in {"info", "low", "medium", "high", "critical"}:
        raise ValueError("Invalid CSV severity")
    raw_metadata = normalized.pop("metadata", None)
    normalized["payload_metadata"] = json.loads(raw_metadata) if raw_metadata else {}
    if not isinstance(normalized["payload_metadata"], dict):
        raise ValueError("CSV metadata must be a JSON object")
    normalized["raw"] = normalized.get("raw", json.dumps(row, sort_keys=True))
    return normalized


def ingest_file(db: Session, path: str) -> list[Event]:
    return ingest_file_report(db, path).events


@dataclass
class IngestReport:
    imported: int = 0
    rejected: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    events: list[Event] = field(default_factory=list, repr=False)


def ingest_file_report(db: Session, path: str) -> IngestReport:
    file_path = Path(path)
    report = IngestReport()
    if not file_path.is_file():
        raise FileNotFoundError(path)
    try:
        if file_path.suffix.lower() == ".csv":
            with file_path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None:
                    raise ValueError("CSV header is required")
                for row_number, row in enumerate(reader, start=2):
                    try:
                        payload = parse_csv_row(row)
                        report.events.append(Event(**payload))
                    except (ValueError, json.JSONDecodeError) as exc:
                        report.errors.append({"row": row_number, "message": str(exc)})
                        report.rejected += 1
        else:
            with file_path.open("r", encoding="utf-8") as fh:
                lines = fh if file_path.suffix.lower() != ".json" else fh.read().splitlines()
                for row_number, line in enumerate(lines, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = parse_line(line)
                        if not payload:
                            continue
                        report.events.append(Event(**payload))
                    except (ValueError, json.JSONDecodeError) as exc:
                        report.errors.append({"row": row_number, "message": str(exc)})
                        report.rejected += 1
        for event in report.events:
            db.add(event)
        db.commit()
        report.imported = len(report.events)
        return report
    except Exception:
        db.rollback()
        raise
