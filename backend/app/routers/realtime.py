from __future__ import annotations

import asyncio
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.permissions import Permission, has_permission
from app.database import get_db
from app.models import Notification, ProcessingJob, User
from app.security import decode_token
from app.security import require_permission
from app.services.realtime_service import utcnow
from app.services.realtime_service import serialize_notification

router = APIRouter(prefix="/realtime", tags=["realtime"])


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        sockets = self.connections.get(user_id)
        if sockets:
            sockets.discard(websocket)
            if not sockets:
                self.connections.pop(user_id, None)

    async def broadcast(self, payload: dict) -> None:
        disconnected: list[WebSocket] = []
        for user_sockets in list(self.connections.values()):
            for websocket in list(user_sockets):
                try:
                    await websocket.send_json(payload)
                except Exception:
                    disconnected.append(websocket)
        for websocket in disconnected:
            for user_id, sockets in list(self.connections.items()):
                sockets.discard(websocket)
                if not sockets:
                    self.connections.pop(user_id, None)


manager = ConnectionManager()
_redis_listener_task: asyncio.Task | None = None


@router.get("/notifications")
def notifications(
    after: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.EVENTS_READ)),
) -> list[dict]:
    query = db.query(Notification).order_by(Notification.timestamp.asc(), Notification.id.asc())
    if after is not None:
        query = query.filter(Notification.timestamp > after)
    rows = query.limit(limit).all()
    return [serialize_notification(row) for row in rows]


def _notification_dict(notification: Notification) -> dict:
    return serialize_notification(notification)


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = auth_message.get("token") if isinstance(auth_message, dict) else None
        if not isinstance(token, str):
            await websocket.close(code=4401, reason="Authentication required")
            return
        payload = decode_token(token)
        user = (
            db.query(User).filter(User.username == payload.get("sub"), User.disabled == 0).first()
        )
        if user is None or not has_permission(str(user.role), Permission.EVENTS_READ):
            await websocket.close(code=4403, reason="Insufficient permissions")
            return
        manager.connections.setdefault(user.id, set()).add(websocket)
        await websocket.send_json({"type": "connected", "timestamp": utcnow().isoformat()})
        _ensure_redis_listener()
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                await websocket.send_json(
                    {"type": "error", "message": "Message must be a JSON object"}
                )
                continue
            action = message.get("type")
            if action == "ping":
                await websocket.send_json({"type": "pong", "timestamp": utcnow().isoformat()})
            else:
                await websocket.send_json({"type": "error", "message": "Unsupported message type"})
    except asyncio.TimeoutError:
        await websocket.close(code=4408, reason="Authentication timeout")
    except (WebSocketDisconnect, jwt.PyJWTError):
        pass
    finally:
        for sockets in list(manager.connections.values()):
            sockets.discard(websocket)


def _ensure_redis_listener() -> None:
    global _redis_listener_task
    if _redis_listener_task is None or _redis_listener_task.done():
        _redis_listener_task = asyncio.create_task(_redis_notification_listener())


async def _redis_notification_listener() -> None:
    try:
        import json
        import redis.asyncio as redis_asyncio

        from app.config import settings

        redis_client = redis_asyncio.Redis.from_url(settings.redis_url)
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe("neurosoc:notifications")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("data"):
                    payload = json.loads(message["data"])
                    await manager.broadcast(payload)
                await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        raise
    except (ConnectionError, TimeoutError, OSError):
        return


@router.get("/health")
def realtime_health(
    db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.SETTINGS_MANAGE))
) -> dict:
    active = sum(len(sockets) for sockets in manager.connections.values())
    queue_depth = (
        db.query(ProcessingJob).filter(ProcessingJob.status.in_(["pending", "retrying"])).count()
    )
    failed = db.query(ProcessingJob).filter(ProcessingJob.status == "failed").count()
    return {
        "status": "ok",
        "active_connections": active,
        "queue_depth": queue_depth,
        "failed_jobs": failed,
    }
