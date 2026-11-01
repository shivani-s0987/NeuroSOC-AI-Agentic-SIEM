import json
import logging
import sys
from datetime import datetime, timezone


def configure_logging(level: str) -> None:
    logging.basicConfig(
        stream=sys.stdout, level=getattr(logging, level.upper(), logging.INFO), format="%(message)s"
    )


def log_request(
    method: str, path: str, status_code: int, duration_ms: float, request_id: str
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "logger": "neurosoc.http",
        "method": method,
        "path": path,
        "status": status_code,
        "duration_ms": duration_ms,
        "request_id": request_id,
    }
    logging.getLogger("neurosoc.http").info(json.dumps(record))
