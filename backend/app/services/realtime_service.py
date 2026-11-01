from __future__ import annotations

import logging
import uuid
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Event, Notification, ProcessingJob


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def publish_notification(
    db: Session,
    event_type: str,
    resource_type: str,
    resource_id: str | int,
    data: dict[str, Any] | None = None,
    notification_id: str | None = None,
) -> Notification:
    notification = Notification(
        notification_id=notification_id or uuid.uuid4().hex,
        event_type=event_type,
        schema_version=1,
        timestamp=utcnow(),
        resource_type=resource_type,
        resource_id=str(resource_id),
        data=data or {},
    )
    db.add(notification)
    db.flush()
    publish_realtime_notification(notification)
    return notification


def serialize_notification(notification: Notification) -> dict[str, Any]:
    return {
        "event_id": notification.notification_id,
        "event_type": notification.event_type,
        "schema_version": notification.schema_version,
        "timestamp": notification.timestamp.isoformat(),
        "resource": {
            "type": notification.resource_type,
            "id": notification.resource_id,
        },
        "data": notification.data or {},
    }


def publish_realtime_notification(notification: Notification) -> None:
    try:
        import redis

        redis.Redis.from_url(settings.redis_url).publish(
            "neurosoc:notifications",
            json.dumps(serialize_notification(notification)),
        )
    except Exception as exc:
        logging.getLogger("neurosoc.realtime").warning(
            "realtime notification pubsub publish failed notification=%s error=%s",
            notification.notification_id,
            exc,
        )


def queue_event(db: Session, event: Event) -> ProcessingJob:
    job = db.query(ProcessingJob).filter(ProcessingJob.event_id == event.id).one_or_none()
    if job is None:
        job = ProcessingJob(
            event_id=event.id,
            status="pending",
            max_attempts=settings.worker_max_attempts,
        )
        db.add(job)
    return job


def enqueue_celery_event(event_id: int) -> None:
    if not settings.celery_broker_url:
        return
    try:
        from app.worker import process_event

        process_event.apply_async(args=[event_id])
    except Exception as exc:
        logging.getLogger("neurosoc.queue").warning(
            "event=%s celery enqueue failed; durable job remains pending error=%s",
            event_id,
            exc,
        )
