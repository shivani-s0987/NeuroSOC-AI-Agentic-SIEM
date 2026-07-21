from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_PATH, settings

engine = create_engine(
    (
        str(DATABASE_PATH).replace("\\", "/")
        if str(DATABASE_PATH).startswith("/")
        else settings.database_url
    ),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
