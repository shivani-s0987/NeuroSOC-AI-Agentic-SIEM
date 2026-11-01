from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import DATABASE_PATH, settings

database_url = settings.database_url
if database_url == "sqlite:///./neurosoc.db":
    database_url = f"sqlite:///{str(DATABASE_PATH).replace(chr(92), '/')}"

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine_options: dict = {"connect_args": connect_args, "pool_pre_ping": True}
if database_url.startswith(("postgresql://", "postgresql+psycopg://")):
    engine_options.update(
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )
engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
