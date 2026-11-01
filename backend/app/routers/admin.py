from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.pagination import paginated
from app.core.permissions import normalize_role
from app.database import get_db
from app.models import AuditLog, User
from app.schemas import UserOut
from app.security import get_current_user

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _admin(actor):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    query = db.query(User).order_by(User.id.asc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return paginated(users, page, page_size, total)


@router.patch("/users/{user_id}/role")
def change_role(
    user_id: int, role: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserOut:
    if not _admin(actor):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if user_id == actor.id:
        raise HTTPException(status_code=403, detail="Users cannot modify their own role")
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in {"ADMIN", "SOC_ANALYST", "SECURITY_VIEWER"}:
        raise HTTPException(status_code=422, detail="Invalid role")
    target.role = role
    db.commit()
    db.refresh(target)
    return target


@router.patch("/users/{user_id}/status")
def change_status(
    user_id: int,
    disabled: bool,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if not _admin(actor):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if user_id == actor.id:
        raise HTTPException(status_code=403, detail="Users cannot deactivate their own account")
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if disabled:
        active_admins = (
            db.query(User)
            .filter(
                User.role.in_(["ADMIN", "Administrator", "admin", "administrator"]),
                User.disabled == 0,
            )
            .count()
        )
        if normalize_role(str(target.role)) == "ADMIN" and active_admins <= 1:
            raise HTTPException(
                status_code=409, detail="The last active administrator cannot be deactivated"
            )
    target.disabled = int(disabled)
    db.commit()
    db.refresh(target)
    return target


@router.get("/audit-logs")
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _admin(actor):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    total = query.count()
    return paginated(
        query.offset((page - 1) * page_size).limit(page_size).all(), page, page_size, total
    )


def _admin(actor: User) -> bool:
    return normalize_role(str(actor.role)) == "ADMIN"
