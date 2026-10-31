import pytest

from app.database import Base, engine, SessionLocal
import app.models  # noqa: F401


@pytest.fixture(autouse=True, scope="session")
def database_schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_database(database_schema):
    db = SessionLocal()
    for model in (
        __import__("app.models", fromlist=["RefreshTokenSession"]).RefreshTokenSession,
        __import__("app.models", fromlist=["PasswordResetToken"]).PasswordResetToken,
        __import__("app.models", fromlist=["AuditLog"]).AuditLog,
        __import__("app.models", fromlist=["User"]).User,
    ):
        db.query(model).delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.close()
