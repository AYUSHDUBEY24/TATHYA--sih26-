"""
Phase 8 tests — text extraction, persistence, and authorized search.

Extraction is exercised through the real upload flow (in-memory storage, in-
memory SQLite). OCR-specific behaviour is tested with monkeypatched Tesseract
so the suite never depends on a locally installed OCR binary.
"""

import pymupdf
import pytest
from fastapi.testclient import TestClient

import app.services.extraction_service as extraction_service
from app.main import app
from app.storage import InMemoryStorage, get_storage
from tests.test_documents import auth, login, make_case, register

PASSWORD = "Str0ngPass!x"


@pytest.fixture
def mem_storage(client):
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_storage, None)


def make_text_pdf(text: str) -> bytes:
    """A real PDF with a genuine text layer (passes the %PDF- signature check)."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


def make_scanned_pdf() -> bytes:
    """A real PDF with no text layer (simulates a scanned document)."""
    doc = pymupdf.open()
    doc.new_page()
    return doc.tobytes()


def upload_file(
    client: TestClient,
    token: str,
    case_id: str,
    file_bytes: bytes,
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
    document_type: str = "FIR",
):
    return client.post(
        "/api/documents/upload",
        files={"file": (filename, file_bytes, content_type)},
        data={
            "case_id": case_id,
            "document_type": document_type,
            "classification": "RESTRICTED",
            "description": "phase 8 test upload",
        },
        headers=auth(token),
    )


def search(client: TestClient, token: str, query: str, **params):
    return client.get("/api/search", params={"q": query, **params}, headers=auth(token))


def get_text_entries() -> list:
    """All DocumentText rows in the per-test database."""
    from sqlalchemy import select

    from app.models.document_text import DocumentText
    from tests.conftest import TestSession

    db = TestSession()
    try:
        return db.execute(select(DocumentText)).scalars().all()
    finally:
        db.close()


# --- 1+5. Extraction from a normal text PDF + persistence -------------------


def test_text_pdf_extracted_and_persisted(client, mem_storage):
    register(client, "io8a@example.com", "io_eight_a", "INVESTIGATING_OFFICER")
    token = login(client, "io8a@example.com")
    case = make_case(client, token)

    response = upload_file(
        client,
        token,
        case["id"],
        make_text_pdf(
            "The forensic examination of the mobile phone confirmed the "
            "fingerprint evidence recovered at the scene."
        ),
    )
    assert response.status_code == 201, response.text
    document_id = response.json()["id"]

    entries = get_text_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert str(entry.document_id) == document_id
    assert entry.extraction_method == "PYMUPDF"
    assert entry.extraction_status == "COMPLETED"
    assert "fingerprint" in entry.extracted_text
    assert entry.page_count == 1
    assert entry.error_message is None


# --- 2. Empty / scanned document handling ------------------------------------


def test_scanned_pdf_ocr_unavailable_does_not_break_upload(client, mem_storage, monkeypatch):
    """No Tesseract installed: scanned PDF -> OCR_UNAVAILABLE, upload succeeds."""
    # Force "no Tesseract" regardless of the host environment (Tesseract may
    # be installed locally; tests must not depend on that).
    monkeypatch.setattr(extraction_service, "_tesseract_path", None)
    assert not extraction_service.ocr_available()

    register(client, "io8b@example.com", "io_eight_b", "INVESTIGATING_OFFICER")
    token = login(client, "io8b@example.com")
    case = make_case(client, token)

    response = upload_file(client, token, case["id"], make_scanned_pdf())
    assert response.status_code == 201, response.text

    entries = get_text_entries()
    assert len(entries) == 1
    assert entries[0].extraction_status == "OCR_UNAVAILABLE"
    assert entries[0].extracted_text is None
    assert "OCR" in entries[0].error_message

    # The document remains fully accessible despite the missing text.
    doc_id = response.json()["id"]
    assert client.get(f"/api/documents/{doc_id}", headers=auth(token)).status_code == 200


# --- 3. OCR path when available (mocked Tesseract) ---------------------------


def test_ocr_used_when_available(client, mem_storage, monkeypatch):
    monkeypatch.setattr(extraction_service, "ocr_available", lambda: True)
    monkeypatch.setattr(
        extraction_service,
        "_run_tesseract",
        lambda images, lang="eng": "OCR recovered text: suspect vehicle "
        "registration number was identified from the scanned page",
    )

    register(client, "io8c@example.com", "io_eight_c", "INVESTIGATING_OFFICER")
    token = login(client, "io8c@example.com")
    case = make_case(client, token)

    response = upload_file(client, token, case["id"], make_scanned_pdf())
    assert response.status_code == 201, response.text

    entries = get_text_entries()
    assert len(entries) == 1
    assert entries[0].extraction_method == "OCR"
    assert entries[0].extraction_status == "COMPLETED"
    assert "registration number" in entries[0].extracted_text


# --- 4. Extraction failure handling ------------------------------------------


def test_extraction_failure_keeps_document_usable(client, mem_storage):
    register(client, "io8d@example.com", "io_eight_d", "INVESTIGATING_OFFICER")
    token = login(client, "io8d@example.com")
    case = make_case(client, token)


    # A corrupt "PDF": magic bytes pass upload validation, parser then fails.
    response = upload_file(client, token, case["id"], b"%PDF-1.4 definitely broken")
    assert response.status_code == 201, response.text
    doc_id = response.json()["id"]

    entries = get_text_entries()
    assert len(entries) == 1
    assert entries[0].extraction_status == "FAILED"

    # Document + download still work; extraction never breaks the core flow.
    assert client.get(f"/api/documents/{doc_id}", headers=auth(token)).status_code == 200
    download = client.get(f"/api/documents/{doc_id}/download", headers=auth(token))
    assert download.status_code == 200


# --- 6. Version-specific extracted text ---------------------------------------


def test_each_version_has_its_own_extracted_text(client, mem_storage):
    register(client, "io8e@example.com", "io_eight_e", "INVESTIGATING_OFFICER")
    token = login(client, "io8e@example.com")
    case = make_case(client, token)

    first = upload_file(
        client, token, case["id"], make_text_pdf("Original report about a bicycle theft.")
    )
    assert first.status_code == 201, first.text
    doc_id = first.json()["id"]

    second = client.post(
        f"/api/documents/{doc_id}/versions",
        files={
            "file": (
                "report.pdf",
                make_text_pdf("Updated report: stolen laptop recovered in Mumbai."),
                "application/pdf",
            )
        },
        data={"change_note": "v2 with new findings"},
        headers=auth(token),
    )
    assert second.status_code == 201, second.text

    entries = get_text_entries()
    assert len(entries) == 2  # one row per immutable version
    texts = {e.extracted_text for e in entries}
    assert any("bicycle" in t for t in texts)
    assert any("laptop" in t for t in texts)


# --- 7+9. Authorized search over content and metadata ------------------------


def test_search_finds_by_content_and_metadata(client, mem_storage):
    register(client, "io8f@example.com", "io_eight_f", "INVESTIGATING_OFFICER")
    token = login(client, "io8f@example.com")
    case = make_case(client, token)

    # Document whose text layer contains the searched term.
    uploaded = upload_file(
        client,
        token,
        case["id"],
        make_text_pdf("Witness statement describing a red hatchback near the market."),
        filename="witness_01.pdf",
        document_type="WITNESS_STATEMENT",
    )
    assert uploaded.status_code == 201, uploaded.text

    # Content match against extracted text.
    body = search(client, token, "hatchback").json()
    assert body["total"] == 1
    hit = body["results"][0]
    assert hit["file_name"] == "witness_01.pdf"
    assert hit["case_number"] == case["case_number"]
    assert hit["matched_text"] is True
    assert "hatchback" in hit["snippet"].lower()
    assert hit["extraction_method"] == "PYMUPDF"
    assert hit["document_type"] == "WITNESS_STATEMENT"
    assert hit["uploader_username"] == "io_eight_f"

    # Metadata match on file name.
    body = search(client, token, "witness_01").json()
    assert body["total"] == 1

    # Multi-term AND semantics: both terms must match somewhere.
    assert search(client, token, "witness red").json()["total"] == 1
    assert search(client, token, "witness motorbike").json()["total"] == 0

    # Metadata filter by document type.
    body = search(client, token, "hatchback", document_type="FIR").json()
    assert body["total"] == 0
    body = search(client, token, "hatchback", document_type="WITNESS_STATEMENT").json()
    assert body["total"] == 1


def test_unauthorized_document_excluded_from_search(client, mem_storage):
    """Search never leaks documents from cases the user cannot access."""
    # IO-A uploads to their case.
    register(client, "io8g@example.com", "io_eight_g", "INVESTIGATING_OFFICER")
    token_a = login(client, "io8g@example.com")
    case_a = make_case(client, token_a)
    uploaded = upload_file(
        client,
        token_a,
        case_a["id"],
        make_text_pdf("Secret charge sheet details about the smuggling ring."),
        filename="charge_sheet.pdf",
        document_type="CHARGE_SHEET",
    )
    assert uploaded.status_code == 201, uploaded.text

    # IO-B has their own case but no access to case_a.
    register(client, "io8h@example.com", "io_eight_h", "INVESTIGATING_OFFICER")
    token_b = login(client, "io8h@example.com")
    make_case(client, token_b)

    body = search(client, token_b, "smuggling").json()
    assert body["total"] == 0
    assert body["results"] == []

    # Same query from an ADMIN (full visibility) finds it — proves the term
    # is indexed and the exclusion above is authorization, not extraction.
    register(client, "adm8@example.com", "adm_eight", "ADMIN")
    token_admin = login(client, "adm8@example.com")
    assert search(client, token_admin, "smuggling").json()["total"] == 1

    # No-token requests are rejected outright.
    assert client.get("/api/search", params={"q": "smuggling"}).status_code in (401, 403)



# --- 10. Empty / invalid search query behaviour -------------------------------


def test_search_empty_and_invalid_queries(client, mem_storage):
    register(client, "io8i@example.com", "io_eight_i", "INVESTIGATING_OFFICER")
    token = login(client, "io8i@example.com")
    make_case(client, token)

    # Missing/blank/whitespace queries are rejected (422), not echoed as results.
    assert client.get("/api/search", headers=auth(token)).status_code == 422
    assert search(client, token, "").status_code == 422
    assert search(client, token, "   ").status_code == 422

    # Over-length query rejected by validation.
    assert search(client, token, "x" * 201).status_code == 422

    # Valid query that matches nothing returns a clean empty result set.
    body = search(client, token, "zzz_no_such_term").json()
    assert body["total"] == 0
    assert body["results"] == []


# --- 11. Pagination / limit behaviour ------------------------------------------


def test_search_pagination(client, mem_storage):
    register(client, "io8j@example.com", "io_eight_j", "INVESTIGATING_OFFICER")
    token = login(client, "io8j@example.com")
    case = make_case(client, token)

    for index in range(5):
        response = upload_file(
            client,
            token,
            case["id"],
            make_text_pdf(f"Pagination test document number {index} about evidence."),
            filename=f"evidence_{index}.pdf",
        )
        assert response.status_code == 201, response.text

    # limit/offset paging over the same authorized result set.
    page1 = search(client, token, "evidence", limit=2, offset=0).json()
    page2 = search(client, token, "evidence", limit=2, offset=2).json()
    page3 = search(client, token, "evidence", limit=2, offset=4).json()

    assert page1["total"] == 5
    assert len(page1["results"]) == 2
    assert len(page2["results"]) == 2
    assert len(page3["results"]) == 1

    seen = [hit["file_name"] for hit in page1["results"] + page2["results"] + page3["results"]]
    assert len(set(seen)) == 5  # pages do not overlap

    # limit outside 1..100 is rejected by validation.
    assert search(client, token, "evidence", limit=0).status_code == 422
    assert search(client, token, "evidence", limit=101).status_code == 422


# --- 12. Audit events for extraction + search ----------------------------------


def test_extraction_and_search_audited(client, mem_storage):
    from sqlalchemy import select

    from app.models.audit_log import AuditLog
    from tests.conftest import TestSession

    register(client, "io8k@example.com", "io_eight_k", "INVESTIGATING_OFFICER")
    token = login(client, "io8k@example.com")
    case = make_case(client, token)

    uploaded = upload_file(
        client,
        token,
        case["id"],
        make_text_pdf("Audit trail verification document about a forged passport."),
    )
    assert uploaded.status_code == 201, uploaded.text

    response = search(client, token, "forged passport")
    assert response.status_code == 200

    db = TestSession()
    try:
        actions = {row.action for row in db.execute(select(AuditLog)).scalars()}
    finally:
        db.close()
    assert "DOCUMENT_TEXT_EXTRACTED" in actions
    assert "SEARCH_QUERIED" in actions

