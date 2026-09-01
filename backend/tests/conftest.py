"""
Pytest fixtures.

Uses an in-memory SQLite database so tests run without Docker/PostgreSQL.
The real engine from app.db.database is never touched: the get_db dependency
is overridden for the test client, and the TestClient is constructed without
a context manager so the app lifespan (which targets the real DB) does not run.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.seed import seed_default_data

test_engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """Create the schema once and seed the five roles + departments."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSession()
    seed_default_data(db)
    db.close()


@pytest.fixture(autouse=True)
def _clean_users(_init_db):
    """Delete case data and users after each test so tests stay independent."""
    yield
    db = TestSession()
    db.execute(delete(AuditLog))
    db.execute(delete(DocumentVersion))
    db.execute(delete(Document))
    db.execute(delete(CaseMember))
    db.execute(delete(Case))
    db.execute(delete(User))
    db.commit()
    db.close()


@pytest.fixture
def client():
    """TestClient with the database dependency pointed at the test session."""

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
