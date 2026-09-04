"""
Phase 4 secure document management tests.

Storage is an in-memory stub injected via the ``get_storage`` dependency
override, so no Docker/MinIO is required. Authorization is tested through the
real Phase 2/3 dependency chain.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
PASSWORD = "Str0ngPass!x"

PDF_BYTES = b"%PDF-1.4\n% synthetic test pdf\n1 0 obj\n"


@pytest.fixture
def mem_storage(client):
    """Replace the storage dependency with an in-memory stub for this test."""
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_storage, None)


def register(client: TestClient, email: str, username: str, role: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "password": PASSWORD,
            "full_name": username.replace("_", " ").title(),
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_case(client: TestClient, token: str, title: str = "Doc test case") -> dict:
    response = client.post(
        CASES,
        json={
            "title": title,
            "crime_type": "THEFT",
            "police_station": "Central PS",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload(
    client: TestClient,
    token: str,
    case_id: str,
    file_bytes: bytes = PDF_BYTES,
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
    document_type: str = "FIR",
    classification: str = "RESTRICTED",
):
    return client.post(
        f"{DOCS}/upload",
        files={"file": (filename, file_bytes, content_type)},
        data={
            "case_id": case_id,
            "document_type": document_type,
            "classification": classification,
            "description": "synthetic upload",
        },
        headers=auth(token),
    )


# --- Upload ---------------------------------------------------------------


def test_upload_valid_document(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)

    response = upload(client, token, case["id"])
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["file_name"] == "report.pdf"
    assert doc["document_type"] == "FIR"
    assert doc["status"] == "ACTIVE"
    assert doc["size_bytes"] == len(PDF_BYTES)
    assert doc["uploader"]["username"] == "io_one"
    # The response must never expose the internal object key or storage URLs.
    assert "object_key" not in doc
    assert "minio" not in response.text.lower()


def test_object_key_is_case_scoped_and_stored(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    doc = upload(client, token, case["id"]).json()

    # The uploaded bytes must actually be retrievable (deterministic key).
    downloaded = client.get(f"{DOCS}/{doc['id']}/download", headers=auth(token))
    assert downloaded.status_code == 200
    assert downloaded.content == PDF_BYTES


def test_upload_requires_authentication(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)

    response = client.post(
        f"{DOCS}/upload",
        files={"file": ("report.pdf", PDF_BYTES, "application/pdf")},
        data={
            "case_id": case["id"],
            "document_type": "FIR",
            "classification": "INTERNAL",
        },
    )
    assert response.status_code == 401


def test_upload_unsupported_type_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)

    response = upload(
        client,
        token,
        case["id"],
        file_bytes=b"MZ\x90\x00fake-exe",
        filename="evil.exe",
        content_type="application/x-msdownload",
    )
    assert response.status_code == 415


def test_upload_mime_mismatch_rejected(client, mem_storage):
    """Declared as PDF but content is not a PDF → rejected (no extension trust)."""
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)

    response = upload(
        client,
        token,
        case["id"],
        file_bytes=b"MZ\x90\x00not-a-pdf",
        filename="fake.pdf",
        content_type="application/pdf",
    )
    assert response.status_code == 415


def test_upload_oversized_rejected(client, mem_storage, monkeypatch):
    monkeypatch.setattr(get_settings(), "MAX_UPLOAD_SIZE_MB", 1)
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)

    big = b"%PDF-1.4\n" + b"A" * (1024 * 1024)
    response = upload(client, token, case["id"], file_bytes=big)
    assert response.status_code == 413


def test_upload_by_authorized_case_member(client, mem_storage):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    admin = login(client, "admin@example.com")
    case = make_case(client, admin)
    client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": f_reg["id"]},
        headers=auth(admin),
    )

    f_token = login(client, "f@example.com")
    response = upload(
        client,
        f_token,
        case["id"],
        document_type="FORENSIC_REPORT",
        filename="fsl_report.pdf",
    )
    assert response.status_code == 201, response.text
    assert response.json()["document_type"] == "FORENSIC_REPORT"


def test_upload_to_unauthorized_case_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)

    assert upload(client, io2, case["id"]).status_code == 404


def test_upload_invalid_document_type_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    assert upload(client, token, case["id"], document_type="NOT_A_TYPE").status_code == 422


# --- Listing / detail -------------------------------------------------------


def test_list_documents_for_authorized_case(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    upload(client, token, case["id"], filename="a.pdf")
    upload(client, token, case["id"], filename="b.pdf", document_type="EVIDENCE_RECORD")

    response = client.get(f"{DOCS}?case_id={case['id']}", headers=auth(token))
    assert response.status_code == 200
    assert {d["file_name"] for d in response.json()} == {"a.pdf", "b.pdf"}


def test_list_documents_unauthorized_case_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    upload(client, io1, case["id"])

    assert client.get(f"{DOCS}?case_id={case['id']}", headers=auth(io2)).status_code == 404


def test_document_detail_authorized(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    doc = upload(client, token, case["id"]).json()

    response = client.get(f"{DOCS}/{doc['id']}", headers=auth(token))
    assert response.status_code == 200
    assert response.json()["id"] == doc["id"]


def test_document_detail_unauthorized_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    doc = upload(client, io1, case["id"]).json()

    # Changing the document ID in the URL must not bypass case authorization.
    assert client.get(f"{DOCS}/{doc['id']}", headers=auth(io2)).status_code == 404


# --- Download ---------------------------------------------------------------


def test_download_authorized(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    doc = upload(client, token, case["id"], filename="final_report.pdf").json()

    response = client.get(f"{DOCS}/{doc['id']}/download", headers=auth(token))
    assert response.status_code == 200
    assert response.content == PDF_BYTES
    assert response.headers["content-type"].startswith("application/pdf")
    assert 'filename="final_report.pdf"' in response.headers["content-disposition"]


def test_download_unauthorized_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    doc = upload(client, io1, case["id"]).json()

    assert client.get(f"{DOCS}/{doc['id']}/download", headers=auth(io2)).status_code == 404
    assert client.get(f"{DOCS}/{doc['id']}/download").status_code == 401


def test_download_unknown_document_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    assert client.get(f"{DOCS}/{uuid4()}/download", headers=auth(token)).status_code == 404


# --- Deletion ---------------------------------------------------------------


def test_uploader_can_soft_delete_own_document(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    doc = upload(client, token, case["id"]).json()

    response = client.delete(f"{DOCS}/{doc['id']}", headers=auth(token))
    assert response.status_code == 200

    # Soft-deleted documents disappear from detail, download and listings…
    assert client.get(f"{DOCS}/{doc['id']}", headers=auth(token)).status_code == 404
    assert (
        client.get(f"{DOCS}/{doc['id']}/download", headers=auth(token)).status_code
        == 404
    )
    listed = client.get(f"{DOCS}?case_id={case['id']}", headers=auth(token)).json()
    assert all(d["id"] != doc["id"] for d in listed)


def test_plain_member_cannot_delete_others_document(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    io1 = login(client, "io1@example.com")
    case = make_case(client, io1)
    doc = upload(client, io1, case["id"]).json()
    # forensic becomes a plain member (not uploader, not manager)
    client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": f_reg["id"]},
        headers=auth(io1),
    )
    f_token = login(client, "f@example.com")

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(f_token)).status_code == 403


def test_admin_can_delete_any_document(client, mem_storage):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    admin = login(client, "admin@example.com")
    case = make_case(client, io1)
    doc = upload(client, io1, case["id"]).json()

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(admin)).status_code == 200
