from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Configuration
from app.core.permissions import Permission
from app.security import require_permission

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=None)
def list_settings(
    db: Session = Depends(get_db), _actor=Depends(require_permission(Permission.SETTINGS_MANAGE))
) -> list[dict[str, object]]:
    return [
        {"key": str(item.key), "value": str(item.value)} for item in db.query(Configuration).all()
    ]


@router.post("", response_model=None)
def set_setting(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    _actor=Depends(require_permission(Permission.SETTINGS_MANAGE)),
) -> dict[str, object]:
    config = db.query(Configuration).filter(Configuration.key == key).first()
    if config is None:
        config = Configuration(key=key, value=value)
        db.add(config)
    else:
        setattr(config, "value", value)
    db.commit()
    db.refresh(config)
    return {"key": str(config.key), "value": str(config.value)}
