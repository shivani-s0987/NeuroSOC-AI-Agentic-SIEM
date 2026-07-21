from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import Event


def parse_line(line: str) -> dict[str, Any]:
    text = line.strip()
    if not text:
        return {}
    if text.startswith("{"):
        payload = json.loads(text)
        timestamp = payload.get("timestamp") or datetime.now(timezone.utc)
        return {
            "source": payload.get("source", "json"),
            "event_type": payload.get("event_type", "json"),
            "severity": payload.get("severity", "info"),
            "host": payload.get("host"),
            "user": payload.get("user"),
            "src_ip": payload.get("src_ip"),
            "dst_ip": payload.get("dst_ip"),
            "process_name": payload.get("process_name"),
            "message": payload.get("message", text),
            "raw": text,
            "timestamp": timestamp,
            "metadata": payload.get("metadata", {}),
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
                "metadata": {"csv": parts},
                "timestamp": datetime.now(timezone.utc),
            }
    match = re.match(r"^(?P<ts>\S+) (?P<host>\S+) (?P<proc>\S+): (?P<msg>.+)$", text)
    if match:
        return {
            "source": "syslog",
            "event_type": "syslog",
            "severity": "info",
            "host": match.group("host"),
            "process_name": match.group("proc"),
            "message": match.group("msg"),
            "raw": text,
            "timestamp": datetime.now(timezone.utc),
        }
    return {
        "source": "custom",
        "event_type": "custom",
        "severity": "info",
        "message": text,
        "raw": text,
        "timestamp": datetime.now(timezone.utc),
    }


def ingest_file(db: Session, path: str) -> list[Event]:
    file_path = Path(path)
    events: list[Event] = []
    if file_path.suffix.lower() == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                payload = parse_line(json.dumps(row))
                event = Event(**payload)
                db.add(event)
                events.append(event)
    else:
        with file_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                payload = parse_line(line)
                if not payload:
                    continue
                event = Event(**payload)
                db.add(event)
                events.append(event)
    db.commit()
    return events
