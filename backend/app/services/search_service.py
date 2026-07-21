from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Event, SavedSearch


def search_events(
    db: Session,
    query: str | None = None,
    host: str | None = None,
    user: str | None = None,
    severity: str | None = None,
    src_ip: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Event]:
    q = db.query(Event)
    if query:
        q = q.filter(or_(Event.message.ilike(f"%{query}%"), Event.raw.ilike(f"%{query}%")))
    if host:
        q = q.filter(Event.host == host)
    if user:
        q = q.filter(Event.user == user)
    if severity:
        q = q.filter(Event.severity == severity)
    if src_ip:
        q = q.filter(Event.src_ip == src_ip)
    if start:
        q = q.filter(Event.timestamp >= start)
    if end:
        q = q.filter(Event.timestamp <= end)
    return q.order_by(Event.timestamp.desc()).limit(200).all()


def save_search(db: Session, name: str, query: str, owner: str) -> SavedSearch:
    saved = SavedSearch(name=name, query=query, owner=owner)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved
