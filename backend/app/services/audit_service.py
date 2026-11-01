from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


_SENSITIVE_KEYS = {"password", "token", "refresh_token", "access_token", "authorization", "secret"}


def safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
    return {
        key: value
        for key, value in (details or {}).items()
        if key.lower() not in _SENSITIVE_KEYS
        and not any(secret in key.lower() for secret in _SENSITIVE_KEYS)
    }


def record_audit(
    db: Session,
    actor: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    request_id: str | None = None,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
    actor_user_id: int | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        outcome=outcome,
        details=safe_details(details),
    )
    db.add(entry)
    db.commit()
    return entry
