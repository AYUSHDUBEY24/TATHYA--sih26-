"""
Phase 10A demo seed tests.

Uses the in-memory SQLite test infrastructure from conftest.py.
Verifies that demo users, cases, documents, versions, and audit entries
are created correctly and that the seed is idempotent.
"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.hashing import sha256_hex, is_sha256_hex
from app.db.database import Base, get_db
from app.main import app
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_text import DocumentText
from app.models.document_version import DocumentVersion
from app.models.user import User
from app.seed import seed_default_data
from app.seed_demo import (
    DEMO_CASES,
    DEMO_PASSWORD,
    DEMO_USERS,
    reset_demo,
    seed_demo,
    seed_demo_users,
)
from app.storage import InMemoryStorage, get_storage

from tests.conftest import TestSession, test_engine


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """Create schema and seed baseline data once."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSession()
    seed_default_data(db)
    db.close()


@pytest.fixture(autouse=True)
def _clean_data(_init_db):
    """Clean up demo data after each test."""
    yield
    db = TestSession()
    reset_demo(db)
    db.close()


@pytest.fixture
def client():
    """TestClient with in-memory storage and test database."""

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_storage, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def demo_storage():
    """In-memory storage passed directly to seed_demo (bypasses FastAPI DI)."""
    return InMemoryStorage()


def test_seed_creates_users(client, demo_storage):
    """Demo users are created with correct roles."""
    db = TestSession()
    users = seed_demo_users(db)

    assert len(users) == len(DEMO_USERS)

    for spec in DEMO_USERS:
        assert spec["username"] in users
        user = users[spec["username"]]
        assert user.email == spec["email"]
        assert user.full_name == spec["full_name"]
        assert user.is_active is True
        assert user.role.name == spec["role"]


def test_seed_creates_cases(client, demo_storage):
    """Demo cases are created with correct statuses."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    for case_spec in DEMO_CASES:
        case = db.scalar(select(Case).where(Case.case_number == case_spec["case_number"]))
        assert case is not None, f"Case {case_spec['case_number']} not found"
        assert case.title == case_spec["title"]
        assert case.status == case_spec["status"]
        assert case.crime_type == case_spec["crime_type"]


def test_seed_creates_case_members(client, demo_storage):
    """Case memberships are created correctly."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    for case_spec in DEMO_CASES:
        case = db.scalar(select(Case).where(Case.case_number == case_spec["case_number"]))
        assert case is not None

        members = db.scalars(
            select(CaseMember).where(CaseMember.case_id == case.id)
        ).all()
        member_usernames = {m.user.username for m in members}

        for member_spec in case_spec.get("members", []):
            assert member_spec["username"] in member_usernames


def test_seed_creates_documents(client, demo_storage):
    """Documents are created with correct metadata."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    total_docs = sum(len(c.get("documents", [])) for c in DEMO_CASES)
    demo_case_numbers = {c["case_number"] for c in DEMO_CASES}
    demo_cases = db.scalars(
        select(Case).where(Case.case_number.in_(demo_case_numbers))
    ).all()

    doc_count = 0
    for case in demo_cases:
        docs = db.scalars(select(Document).where(Document.case_id == case.id)).all()
        doc_count += len(docs)
        for doc in docs:
            assert doc.status == "ACTIVE"
            assert doc.content_type == "text/plain"
            assert doc.size_bytes > 0
            assert doc.current_version_number >= 1
            assert doc.current_hash is not None
            assert is_sha256_hex(doc.current_hash)

    assert doc_count == total_docs


def test_seed_creates_versions(client, demo_storage):
    """Document versions have correct hashes."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    demo_case_numbers = {c["case_number"] for c in DEMO_CASES}
    demo_cases = db.scalars(
        select(Case).where(Case.case_number.in_(demo_case_numbers))
    ).all()

    for case in demo_cases:
        docs = db.scalars(select(Document).where(Document.case_id == case.id)).all()
        for doc in docs:
            versions = db.scalars(
                select(DocumentVersion).where(DocumentVersion.document_id == doc.id)
            ).all()
            assert len(versions) >= 1
            v1 = next((v for v in versions if v.version_number == 1), None)
            assert v1 is not None
            assert is_sha256_hex(v1.hash)
            assert v1.file_size == doc.size_bytes


def test_seed_creates_v2_version(client, demo_storage):
    """Documents with have_v2=True have a second version."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    case = db.scalar(select(Case).where(Case.case_number == "CASE-2026-001"))
    assert case is not None

    doc = db.scalar(
        select(Document).where(
            Document.case_id == case.id, Document.file_name == "Investigation_Report_v1.txt"
        )
    )
    assert doc is not None
    assert doc.current_version_number == 2

    versions = db.scalars(
        select(DocumentVersion).where(DocumentVersion.document_id == doc.id)
    ).all()
    assert len(versions) == 2
    assert all(is_sha256_hex(v.hash) for v in versions)


def test_seed_processes_text(client, demo_storage):
    """Documents have extracted text for search/RAG."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    demo_case_numbers = {c["case_number"] for c in DEMO_CASES}
    demo_cases = db.scalars(
        select(Case).where(Case.case_number.in_(demo_case_numbers))
    ).all()

    for case in demo_cases:
        docs = db.scalars(select(Document).where(Document.case_id == case.id)).all()
        for doc in docs:
            text_record = db.scalar(
                select(DocumentText).where(DocumentText.document_id == doc.id)
            )
            assert text_record is not None
            assert text_record.extraction_status == "COMPLETED"
            assert text_record.extracted_text is not None
            assert len(text_record.extracted_text) > 0


def test_seed_creates_chunks(client, demo_storage):
    """Documents have RAG chunks."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    demo_case_numbers = {c["case_number"] for c in DEMO_CASES}
    demo_cases = db.scalars(
        select(Case).where(Case.case_number.in_(demo_case_numbers))
    ).all()

    total_chunks = 0
    for case in demo_cases:
        docs = db.scalars(select(Document).where(Document.case_id == case.id)).all()
        for doc in docs:
            chunks = db.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            ).all()
            total_chunks += len(chunks)
            for chunk in chunks:
                assert chunk.status == "INDEXED"
                assert len(chunk.chunk_text) > 0
                assert chunk.embedding is not None

    assert total_chunks > 0, "No chunks were created"


def test_seed_is_idempotent(client, demo_storage):
    """Running seed twice does not create duplicates."""
    db = TestSession()

    result1 = seed_demo(db, storage=demo_storage)
    result2 = seed_demo(db, storage=demo_storage)

    assert result1["users"] == result2["users"]
    assert result1["cases"] == result2["cases"]
    assert result1["documents"] == result2["documents"]

    for spec in DEMO_USERS:
        users = db.scalars(select(User).where(User.username == spec["username"])).all()
        assert len(users) == 1, f"Duplicate user: {spec['username']}"


def test_reset_demo(client, demo_storage):
    """Reset removes all demo data."""
    db = TestSession()

    seed_demo(db, storage=demo_storage)

    demo_users = db.scalars(select(User).where(User.email.like("%@demo.sih"))).all()
    assert len(demo_users) > 0

    result = reset_demo(db)
    assert result["users"] == len(DEMO_USERS)
    assert result["cases"] == len(DEMO_CASES)

    demo_users = db.scalars(select(User).where(User.email.like("%@demo.sih"))).all()
    assert len(demo_users) == 0

    demo_cases = db.scalars(
        select(Case).where(Case.case_number.like("CASE-2026-%"))
    ).all()
    assert len(demo_cases) == 0


def test_demo_passwords_work(client, demo_storage):
    """Demo user passwords can be verified."""
    db = TestSession()
    seed_demo_users(db)

    from app.core.security import verify_password

    for spec in DEMO_USERS:
        user = db.scalar(select(User).where(User.username == spec["username"]))
        assert user is not None
        assert verify_password(DEMO_PASSWORD, user.password_hash)


def test_all_case_statuses_covered(client, demo_storage):
    """Demo cases cover ALL documented statuses."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    expected_statuses = {
        "OPEN", "UNDER_INVESTIGATION", "UNDER_REVIEW",
        "CHARGESHEET_FILED", "COURT_STAGE", "CLOSED", "ARCHIVED",
    }
    demo_statuses = {c["status"] for c in DEMO_CASES}

    assert expected_statuses.issubset(demo_statuses), (
        f"Missing statuses: {expected_statuses - demo_statuses}"
    )


def test_seed_creates_audit_entries(client, demo_storage):
    """Seeding generates realistic audit activity via existing services."""
    db = TestSession()
    seed_demo(db, storage=demo_storage)

    from app.models.audit_log import AuditLog
    from app.services.audit_service import AuditAction

    actions = {row[0] for row in db.execute(select(AuditLog.action)).all()}

    for expected in (
        AuditAction.CASE_CREATED.value,
        AuditAction.CASE_MEMBER_ADDED.value,
        AuditAction.DOCUMENT_UPLOADED.value,
        AuditAction.DOCUMENT_VERSION_CREATED.value,
        AuditAction.DOCUMENT_TEXT_EXTRACTED.value,
    ):
        assert expected in actions, f"Missing audit action: {expected}"

    # No sensitive document contents in audit metadata.
    for row in db.scalars(select(AuditLog)).all():
        for value in (row.meta or {}).values() if isinstance(row.meta, dict) else []:
            if isinstance(value, str):
                assert "COMPLAINANT" not in value
                assert "SEIZED PROPERTY" not in value

