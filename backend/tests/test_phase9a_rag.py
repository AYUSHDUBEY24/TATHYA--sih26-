"""
Phase 9A tests — RAG foundation: chunking + embeddings + vector retrieval.

All tests run against the in-memory SQLite test DB with the deterministic
fallback embedding provider (no paid API calls, no external services).

Security-critical tests verify authorization: search/retrieval must never
surface chunks from cases/documents the user cannot access.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_text import DocumentText
from app.models.document_version import DocumentVersion
from app.services.chunking_service import chunk_text
from app.services.embedding_service import (
    embed_texts,
    get_embedding_provider,
    reset_embedding_provider,
)
from app.services.retrieval_service import retrieve_chunks
from app.storage import InMemoryStorage, get_storage
from tests.conftest import TestSession
from tests.test_documents import auth, login, make_case, register

PASSWORD = "Str0ngPass!x"


@pytest.fixture
def mem_storage(client):
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_storage, None)
    reset_embedding_provider()


def make_text_pdf(text: str) -> bytes:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


def upload_pdf(client, token, case_id, text, document_type="FIR"):
    return client.post(
        "/api/documents/upload",
        files={"file": ("report.pdf", make_text_pdf(text), "application/pdf")},
        data={
            "case_id": case_id,
            "document_type": document_type,
            "classification": "RESTRICTED",
            "description": "phase 9a",
        },
        headers=auth(token),
    )


def latest_document_text():
    db = TestSession()
    try:
        return (
            db.execute(
                select(DocumentText).order_by(DocumentText.created_at.desc())
            )
            .scalars()
            .first()
        )
    finally:
        db.close()


def chunks_for_version(version_id):
    version_uuid = (
        version_id if isinstance(version_id, uuid.UUID) else uuid.UUID(str(version_id))
    )
    db = TestSession()
    try:
        return (
            db.execute(
                select(DocumentChunk).where(DocumentChunk.version_id == version_uuid)
            )
            .scalars()
            .all()
        )
    finally:
        db.close()


def latest_version_id_for_doc(document_id):
    """Latest immutable version id for a document (highest version_number)."""
    document_uuid = (
        document_id if isinstance(document_id, uuid.UUID) else uuid.UUID(str(document_id))
    )
    db = TestSession()
    try:
        return (
            db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_uuid)
                .order_by(DocumentVersion.version_number.desc())
            )
            .scalars()
            .first()
            .id
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 1+3. Deterministic chunking + same text -> same chunks
# ---------------------------------------------------------------------------


def test_chunking_is_deterministic():
    text = (
        "The forensic examination of the mobile phone recovered from the "
        "scene confirmed the fingerprint evidence. The suspect's vehicle "
        "was identified from CCTV footage near the location. Witness "
        "statements corroborate the timeline of events on the night of "
        "the incident. The stolen property was recovered during a raid."
    )
    first = chunk_text(text, page_count=2)
    second = chunk_text(text, page_count=2)
    assert first.chunk_count == second.chunk_count
    assert [c.text for c in first.chunks] == [c.text for c in second.chunks]
    assert [c.page_start for c in first.chunks] == [c.page_start for c in second.chunks]
    assert first.chunk_count >= 1


def test_same_text_produces_same_chunks():
    text = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
    a = chunk_text(text, target_size=3, overlap=0, page_count=1)
    b = chunk_text(text, target_size=3, overlap=0, page_count=1)
    assert [c.text for c in a.chunks] == [c.text for c in b.chunks]
    assert a.total_chars == b.total_chars


# ---------------------------------------------------------------------------
# 2. Chunking respects target size
# ---------------------------------------------------------------------------


def test_chunking_respects_target_size():
    text = ("word " * 2000).strip()
    result = chunk_text(text, target_size=500, overlap=50)
    assert result.chunk_count >= 2
    assert result.total_chars == len(text)


# ---------------------------------------------------------------------------
# 4+5. Embedding + indexing flow (deterministic fallback provider)
# ---------------------------------------------------------------------------


def test_embedding_deterministic_for_same_text():
    reset_embedding_provider()
    outcome1 = embed_texts(["the quick brown fox", "lazy dog sleeping"])
    outcome2 = embed_texts(["the quick brown fox", "lazy dog sleeping"])
    assert outcome1.vector == outcome2.vector
    assert outcome1.dimension == outcome2.dimension
    assert outcome1.provider == "fallback"


def test_embedding_different_for_different_text():
    reset_embedding_provider()
    outcome = embed_texts(["fingerprint evidence", "stolen vehicle recovery"])
    assert len(outcome.vector) == 2
    assert outcome.vector[0] != outcome.vector[1]



# ---------------------------------------------------------------------------
# 6+7. Upload -> extract -> chunk -> embed -> retrieve (authorized)
# ---------------------------------------------------------------------------


def test_upload_persists_chunks_and_embeddings(client, mem_storage):
    register(client, "io_rag1@example.com", "io_rag1", "INVESTIGATING_OFFICER")
    token = login(client, "io_rag1@example.com")
    case = make_case(client, token, title="Rag case one")

    response = upload_pdf(
        client,
        token,
        case["id"],
        "The forensic examination of the mobile phone recovered from the "
        "scene confirmed the fingerprint evidence linking the suspect to "
        "the stolen property recovered during the investigation.",
    )
    assert response.status_code == 201, response.text
    doc_id = response.json()["id"]

    record = latest_document_text()
    assert record.extraction_status == "COMPLETED"
    version_id = record.version_id

    chunks = chunks_for_version(version_id)
    assert len(chunks) >= 1
    assert all(c.status == "INDEXED" for c in chunks)
    assert all(c.embedding is not None for c in chunks)


def test_retrieval_returns_authorized_chunks(client, mem_storage):
    register(client, "io_rag2@example.com", "io_rag2", "INVESTIGATING_OFFICER")
    token = login(client, "io_rag2@example.com")
    case = make_case(client, token, title="Rag case two")

    response = upload_pdf(
        client,
        token,
        case["id"],
        "The forensic examination of the mobile phone recovered from the "
        "scene confirmed the fingerprint evidence linking the suspect to "
        "the stolen property recovered during the investigation.",
    )
    assert response.status_code == 201, response.text

    db = TestSession()
    try:
        from app.models.user import User

        user = db.execute(
            select(User).where(User.username == "io_rag2")
        ).scalars().one()
        result = retrieve_chunks(db, "fingerprint evidence", user, top_k=5)
        assert result.total_candidates >= 1
        assert len(result.results) >= 1
        hit = result.results[0]
        assert hit.chunk_text is not None
        assert hit.score > 0
    finally:
        db.close()


def test_retrieval_endpoint_returns_results(client, mem_storage):
    register(client, "io_rag3@example.com", "io_rag3", "INVESTIGATING_OFFICER")
    token = login(client, "io_rag3@example.com")
    case = make_case(client, token, title="Rag case three")

    response = upload_pdf(
        client,
        token,
        case["id"],
        "The forensic examination of the mobile phone recovered from the "
        "scene confirmed the fingerprint evidence linking the suspect to "
        "the stolen property recovered during the investigation.",
    )
    assert response.status_code == 201, response.text

    result = client.get(
        "/api/retrieval",
        params={"q": "fingerprint evidence", "top_k": 5},
        headers=auth(token),
    )
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["total_candidates"] >= 1
    assert len(payload["results"]) >= 1
    assert payload["results"][0]["chunk_text"] is not None

# ---------------------------------------------------------------------------
# 8+9. Security: unauthorized document / inaccessible case excluded
# ---------------------------------------------------------------------------


def test_unauthorized_document_excluded_from_retrieval(client, mem_storage):
    # Author A uploads a sensitive document
    register(client, "io_raga@example.com", "io_raga", "INVESTIGATING_OFFICER")
    token_a = login(client, "io_raga@example.com")
    case_a = make_case(client, token_a, title="Restricted case A")

    response = upload_pdf(
        client,
        token_a,
        case_a["id"],
        "Highly confidential witness statement about the murder weapon "
        "recovered from the river and the suspect's fingerprints on it.",
    )
    assert response.status_code == 201, response.text

    # Author B (different IO) uploads unrelated content
    register(client, "io_ragb@example.com", "io_ragb", "INVESTIGATING_OFFICER")
    token_b = login(client, "io_ragb@example.com")
    case_b = make_case(client, token_b, title="Unrelated case B")

    response = upload_pdf(
        client,
        token_b,
        case_b["id"],
        "Annual traffic violation statistics for the district showing "
        "speeding citations and parking fines issued last quarter.",
    )
    assert response.status_code == 201, response.text

    # Author B searches for the sensitive content — must get ZERO hits
    result = client.get(
        "/api/retrieval",
        params={"q": "confidential witness statement murder weapon", "top_k": 10},
        headers=auth(token_b),
    )
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["total_candidates"] == 0
    assert payload["results"] == []

    # Author A searching the same terms DOES find the document
    result_a = client.get(
        "/api/retrieval",
        params={"q": "confidential witness statement", "top_k": 10},
        headers=auth(token_a),
    )
    assert result_a.status_code == 200, result_a.text
    assert result_a.json()["total_candidates"] >= 1


def test_admin_sees_all_cases(client, mem_storage):
    register(client, "io_ragc@example.com", "io_ragc", "INVESTIGATING_OFFICER")
    token_c = login(client, "io_ragc@example.com")
    case_c = make_case(client, token_c, title="IO-owned case")

    response = upload_pdf(
        client,
        token_c,
        case_c["id"],
        "Ballistics report confirming the bullet was fired from the "
        "service weapon issued to the suspect officer.",
    )
    assert response.status_code == 201, response.text

    # Admin can retrieve across all cases (bypasses the IO-only filter).
    register(client, "admin_rag@example.com", "admin_rag", "ADMIN")
    admin_token = login(client, "admin_rag@example.com")

    from app.models.user import User

    db = TestSession()
    try:
        admin = db.execute(
            select(User).where(User.username == "admin_rag")
        ).scalars().one()
        result = retrieve_chunks(db, "ballistics report", admin, top_k=10)
        assert len(result.results) >= 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 10. New version re-indexed separately
# ---------------------------------------------------------------------------


def test_new_version_creates_new_chunks(client, mem_storage):
    register(client, "io_ragd@example.com", "io_ragd", "INVESTIGATING_OFFICER")
    token = login(client, "io_ragd@example.com")
    case = make_case(client, token, title="Versioned case")

    v1 = upload_pdf(
        client,
        token,
        case["id"],
        "Original report about a bicycle theft in the downtown market area.",
    )
    assert v1.status_code == 201, v1.text
    doc_id = v1.json()["id"]

    v1_version_id = latest_version_id_for_doc(doc_id)
    v1_chunks = chunks_for_version(v1_version_id)
    assert len(v1_chunks) >= 1

    v2 = client.post(
        f"/api/documents/{doc_id}/versions",
        files={
            "file": (
                "report.pdf",
                make_text_pdf(
                    "Updated report: stolen laptop recovered in Mumbai warehouse."
                ),
                "application/pdf",
            )
        },
        data={"change_note": "v2 with new findings"},
        headers=auth(token),
    )
    assert v2.status_code == 201, v2.text

    v2_version_id = latest_version_id_for_doc(doc_id)
    v2_chunks = chunks_for_version(v2_version_id)
    assert v2_version_id != v1_version_id
    assert len(v2_chunks) >= 1
    # Different text -> different chunk contents
    v1_texts = {c.chunk_text for c in v1_chunks}
    v2_texts = {c.chunk_text for c in v2_chunks}
    assert not v1_texts.intersection(v2_texts)


# ---------------------------------------------------------------------------
# 11. Empty / failed extraction does NOT create fake embeddings
# ---------------------------------------------------------------------------


def test_empty_extraction_creates_no_chunks(client, mem_storage):
    register(client, "io_rage@example.com", "io_rage", "INVESTIGATING_OFFICER")
    token = login(client, "io_rage@example.com")
    case = make_case(client, token, title="Empty extraction case")

    # A corrupt PDF: passes signature check, fails to parse
    response = client.post(
        "/api/documents/upload",
        files={"file": ("report.pdf", b"%PDF-1.4 definitely broken", "application/pdf")},
        data={
            "case_id": case["id"],
            "document_type": "FIR",
            "classification": "RESTRICTED",
            "description": "corrupt pdf",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text

    record = latest_document_text()
    assert record.extraction_status in ("FAILED", "EMPTY")

    # No chunks should be created for a failed extraction
    chunks = chunks_for_version(record.version_id)
    assert len(chunks) == 0


def test_ocr_unavailable_creates_no_chunks(client, mem_storage, monkeypatch):
    # A scanned PDF with no Tesseract -> OCR_UNAVAILABLE -> no chunks.
    # Force "no Tesseract" regardless of the host environment.
    from app.services import extraction_service as _es

    monkeypatch.setattr(_es, "_tesseract_path", None)
    assert not _es.ocr_available()
    import pymupdf

    doc = pymupdf.open()
    doc.new_page()
    scanned_bytes = doc.tobytes()

    register(client, "io_ragf@example.com", "io_ragf", "INVESTIGATING_OFFICER")
    token = login(client, "io_ragf@example.com")
    case = make_case(client, token, title="OCR-unavailable case")

    response = client.post(
        "/api/documents/upload",
        files={"file": ("scanned.pdf", scanned_bytes, "application/pdf")},
        data={
            "case_id": case["id"],
            "document_type": "FIR",
            "classification": "RESTRICTED",
            "description": "scanned pdf",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text

    record = latest_document_text()
    assert record.extraction_status == "OCR_UNAVAILABLE"
    chunks = chunks_for_version(record.version_id)
    assert len(chunks) == 0


def test_fallback_provider_available_without_credentials():
    reset_embedding_provider()
    provider = get_embedding_provider()
    assert provider.available() is True
    assert provider.name == "fallback"


def test_unavailable_embedding_provider_falls_back_gracefully():
    """A provider that raises must NOT break indexing/tests — it falls back."""
    import app.services.embedding_service as embedding_module

    class BrokenProvider:
        name = "broken"

        def available(self) -> bool:
            return False

        def embed(self, texts: list[str]):
            raise RuntimeError("embedding service unavailable")

    original = embedding_module.get_embedding_provider
    embedding_module.get_embedding_provider = lambda: BrokenProvider()
    try:
        outcome = embed_texts(["some searchable text"])
    finally:
        embedding_module.get_embedding_provider = original
    assert outcome.provider == "fallback"
    assert len(outcome.vector) == 1
    assert len(outcome.vector[0]) == outcome.dimension
