from __future__ import annotations

import logging
import signal
import time

try:
    from celery import Celery
except ImportError:  # pragma: no cover - worker dependencies are optional in unit tests
    Celery = None

from app.config import settings
from app.database import SessionLocal
from app.models import Event
from app.services.detection_service import run_detections
from app.services.realtime_service import publish_notification, utcnow
from app.services.ioc_matching_service import match_event

logger = logging.getLogger("neurosoc.worker")
_closing = False

if Celery is not None and settings.celery_broker_url:
    celery = Celery(
        "neurosoc",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend or None,
    )
else:
    celery = None


def process_event(event_id: int) -> dict:
    db = SessionLocal()
    try:
        event = db.get(Event, event_id)
        if event is None:
            return {"event_id": event_id, "status": "missing"}
        if event.processing_status == "processed":
            return {"event_id": event_id, "status": "duplicate"}
        event.processing_status = "processing"
        event.processing_attempts = (event.processing_attempts or 0) + 1
        db.commit()

        run_detections(db)
        match_event(db, event)
        event = db.get(Event, event_id)
        event.processing_status = "processed"
        event.processed_at = utcnow()
        event.last_processing_error = None
        publish_notification(
            db,
            "event.processed",
            "event",
            event.id,
            {
                "severity": event.severity,
                "source": event.source,
            },
        )
        db.commit()
        return {"event_id": event_id, "status": "processed"}
    except Exception as exc:
        db.rollback()
        event = db.get(Event, event_id)
        if event is not None:
            event.processing_status = "retrying"
            event.processing_attempts = (event.processing_attempts or 0) + 1
            event.last_processing_error = str(exc)
            if event.processing_attempts >= settings.worker_max_attempts:
                event.processing_status = "failed"
            db.commit()
        logger.exception("event processing failed event_id=%s", event_id)
        raise
    finally:
        db.close()


if celery is not None:
    process_event_task = celery.task(name="neurosoc.process_event")(process_event)


def _handle_signal(signum, frame):
    global _closing
    logger.info("worker shutdown requested signal=%s", signum)
    _closing = True


def run_worker() -> None:
    """Database-backed fallback worker for installations without Celery."""
    if celery is not None:
        raise RuntimeError("Use `celery -A app.worker.celery worker` for Redis-backed workers")
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    logger.info("starting database polling worker")
    while not _closing:
        db = SessionLocal()
        try:
            event = (
                db.query(Event).filter(Event.processing_status.in_(["pending", "retrying"])).first()
            )
            if event is None:
                time.sleep(settings.worker_poll_seconds)
                continue
            if (event.processing_attempts or 0) >= settings.worker_max_attempts:
                event.processing_status = "failed"
                db.commit()
                continue
            process_event(event.id)
        except Exception as exc:
            logger.error("worker iteration failed: %s", exc)
            time.sleep(settings.worker_poll_seconds)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker()
