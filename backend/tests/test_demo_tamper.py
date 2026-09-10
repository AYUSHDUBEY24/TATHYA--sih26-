"""Demo tampering simulation tests (demo-only feature).

Verifies the exact SIH demo sequence:
  VERIFIED -> tamper (no new version, DB hash untouched) -> real integrity
  verification reports INTEGRITY_FAILURE -> restore -> VERIFIED again.

Storage is the in-memory stub, so no MinIO is required.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
DEMO = "/api/demo"
PASSWORD = "Str0ngPass!x"
PDF_BYTES = b"%PDF-1.4\n% synthetic test pdf\n1 0 obj\n"


@pytest.fixture
def mem_storage(client):
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


def _make_document(client: TestClient, token: str) -> dict:
    case = client.post(
        CASES,
        json={
            "title": "Demo tamper case",
            "crime_type": "FRAUD",
            "police_station": "Central PS",
        },
        headers=auth(token),
    )
    assert case.status_code == 201, case.text
    uploaded = client.post(
        f"{DOCS}/upload",
        files={"file": ("report.pdf", PDF_BYTES, "application/pdf")},
        data={
            "case_id": case.json()["id"],
            "document_type": "FIR",
            "classification": "RESTRICTED",
        },
        headers=auth(token),
    )
    assert uploaded.status_code == 201, uploaded.text
    return uploaded.json()

def test_tamper_restore_roundtrip(client, mem_storage):
    register(client, "demo_io@example.com", "demo_io", "INVESTIGATING_OFFICER")
    token = login(client, "demo_io@example.com")
    doc = _make_document(client, token)

    # 1. Baseline: document is VERIFIED.
    integrity = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(token))
    assert integrity.status_code == 200
    assert integrity.json()["status"] == "VERIFIED"

    # 2. Simulate tampering.
    tamper = client.post(f"{DEMO}/{doc['id']}/tamper", headers=auth(token))
    assert tamper.status_code == 200, tamper.text
    assert tamper.json()["tampered"] is True

    # 3. NO new version was created.
    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(token))
    assert versions.status_code == 200
    assert len(versions.json()) == 1

    # 4. The REAL integrity verification detects the modified file.
    integrity = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(token))
    assert integrity.status_code == 200
    body = integrity.json()
    assert body["status"] == "INTEGRITY_FAILURE"
    # 5. Stored (expected) and actual hashes genuinely differ.
    assert body["stored_hash"] != body["current_hash"]

    # 6. Restore the exact original bytes.
    restore = client.post(f"{DEMO}/{doc['id']}/restore", headers=auth(token))
    assert restore.status_code == 200, restore.text
    assert restore.json()["tampered"] is False

    # 7. Verification is VERIFIED again with matching hashes.
    integrity = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(token))
    assert integrity.status_code == 200
    body = integrity.json()
    assert body["status"] == "VERIFIED"
    assert body["stored_hash"] == body["current_hash"]

    # 8. Versions still untouched by the whole roundtrip.
    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(token))
    assert len(versions.json()) == 1

def test_restore_without_tamper_conflicts(client, mem_storage):
    register(client, "demo_io2@example.com", "demo_io2", "INVESTIGATING_OFFICER")
    token = login(client, "demo_io2@example.com")
    doc = _make_document(client, token)

    response = client.post(f"{DEMO}/{doc['id']}/restore", headers=auth(token))
    assert response.status_code == 409


def test_tamper_requires_case_access(client, mem_storage):
    register(client, "demo_io3@example.com", "demo_io3", "INVESTIGATING_OFFICER")
    owner_token = login(client, "demo_io3@example.com")
    doc = _make_document(client, owner_token)

    # A different, unrelated officer cannot tamper with the document.
    register(client, "demo_other@example.com", "demo_other", "INVESTIGATING_OFFICER")
    other_token = login(client, "demo_other@example.com")

    response = client.post(f"{DEMO}/{doc['id']}/tamper", headers=auth(other_token))
    assert response.status_code == 404

    # Anonymous requests are rejected as well.
    assert client.post(f"{DEMO}/{doc['id']}/tamper").status_code == 401


def test_tamper_updates_download_bytes(client, mem_storage):
    register(client, "demo_io4@example.com", "demo_io4", "INVESTIGATING_OFFICER")
    token = login(client, "demo_io4@example.com")
    doc = _make_document(client, token)

    assert (
        client.post(f"{DEMO}/{doc['id']}/tamper", headers=auth(token)).status_code
        == 200
    )
    tampered_download = client.get(
        f"{DOCS}/{doc['id']}/download", headers=auth(token)
    )
    assert tampered_download.status_code == 200
    assert tampered_download.content != PDF_BYTES
    assert b"TATHYA-DEMO" in tampered_download.content

    assert (
        client.post(f"{DEMO}/{doc['id']}/restore", headers=auth(token)).status_code
        == 200
    )
    restored_download = client.get(
        f"{DOCS}/{doc['id']}/download", headers=auth(token)
    )
    assert restored_download.content == PDF_BYTES
