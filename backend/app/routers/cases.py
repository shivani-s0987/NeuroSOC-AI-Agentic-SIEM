from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case
from app.schemas import CaseCreate, CaseOut
from app.services.case_service import add_note, create_case

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db)) -> list[Case]:
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.post("", response_model=CaseOut)
def create(payload: CaseCreate, db: Session = Depends(get_db)) -> Case:
    return create_case(db, payload.title, payload.priority, payload.assigned_to, payload.summary)


@router.post("/{case_id}/notes")
def add_case_note(case_id: int, author: str, content: str, db: Session = Depends(get_db)) -> dict[str, str]:
    note = add_note(db, case_id, author, content)
    return {"id": str(note.id), "content": note.content}
