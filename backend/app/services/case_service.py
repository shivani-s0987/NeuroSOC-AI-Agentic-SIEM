from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Case, CaseNote


def create_case(
    db: Session, title: str, priority: str, assigned_to: str | None, summary: str | None
) -> Case:
    case = Case(title=title, priority=priority, assigned_to=assigned_to, summary=summary)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def add_note(db: Session, case_id: int, author: str, content: str) -> CaseNote:
    note = CaseNote(case_id=case_id, author=author, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
