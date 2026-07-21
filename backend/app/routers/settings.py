from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Configuration

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def list_settings(db: Session = Depends(get_db)) -> list[Configuration]:
    return db.query(Configuration).all()


@router.post("")
def set_setting(key: str, value: str, db: Session = Depends(get_db)) -> Configuration:
    config = db.query(Configuration).filter(Configuration.key == key).first()
    if config is None:
        config = Configuration(key=key, value=value)
        db.add(config)
    else:
        config.value = value
    db.commit()
    db.refresh(config)
    return config
