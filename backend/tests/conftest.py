import pytest

from app.database import Base, engine, SessionLocal
import app.models  # noqa: F401


@pytest.fixture(autouse=True, scope="session")
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_database(database_schema):
    from app.core.rate_limit import _buckets
    _buckets.clear()
    db = SessionLocal()
    for model in (
        __import__("app.models", fromlist=["InvestigationFeedback"]).InvestigationFeedback,
        __import__("app.models", fromlist=["InvestigationResult"]).InvestigationResult,
        __import__("app.models", fromlist=["Investigation"]).Investigation,
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
