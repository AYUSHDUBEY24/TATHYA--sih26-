"""
Phase 5 tests — document versioning + SHA-256 integrity.

Storage is an in-memory stub (dependency override) so no Docker is needed.
The tampering test directly mutates the stored bytes to prove the integrity
check detects real modification (not just a hash compared to itself).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.hashing import sha256_hex
from app.main import app
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
VERSIONS = "/api/versions"
PASSWORD = "Str0ngPass!x"

V1_BYTES = b"%PDF-1.4\nversion one content\n"
V2_BYTES = b"%PDF-1.4\nversion two content (updated)\n"
V3_BYTES = b"%PDF-1.4\nversion three content\n"


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


def make_case(client: TestClient, token: str) -> dict:
    response = client.post(
        CASES,
        json={
            "title": "Versioning case",
            "crime_type": "FRAUD",
            "police_station": "Central PS",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload_doc(
    client: TestClient,
    token: str,
    case_id: str,
    file_bytes: bytes = V1_BYTES,
    filename: str = "report.pdf",
) -> dict:
    response = client.post(
        f"{DOCS}/upload",
        files={"file": (filename, file_bytes, "application/pdf")},
        data={
            "case_id": case_id,
            "document_type": "INVESTIGATION_REPORT",
            "classification": "RESTRICTED",
            "description": "versioning test",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_version(
    client: TestClient,
    token: str,
    document_id: str,
    file_bytes: bytes,
    change_note: str | None = None,
    filename: str = "report.pdf",
):
    data = {"change_note": change_note} if change_note else {}
    return client.post(
        f"{DOCS}/{document_id}/versions",
        files={"file": (filename, file_bytes, "application/pdf")},
        data=data,
        headers=auth(token),
    )


def setup_doc_with_versions(client: TestClient):
    """Register io1/io2 + case + document with v1/v2/v3."""
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    doc = upload_doc(client, io1, case["id"])
    assert add_version(client, io1, doc["id"], V2_BYTES, "updated findings").status_code == 201
    assert add_version(client, io1, doc["id"], V3_BYTES, "final revision").status_code == 201
    return io1, io2, case, doc


# --- Version creation & history ---------------------------------------------


def test_initial_upload_creates_v1_with_hash(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = make_case(client, token)
    doc = upload_doc(client, token, case["id"])

    assert doc["current_version_number"] == 1
    assert doc["current_hash"] == sha256_hex(V1_BYTES)

    history = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(token)).json()
    assert len(history) == 1
    v1 = history[0]
    assert v1["version_number"] == 1
    assert v1["hash"] == sha256_hex(V1_BYTES)
    # Lowercase 64-char hex digest.
    assert v1["hash"] == v1["hash"].lower()
    assert len(v1["hash"]) == 64


def test_new_versions_increment_and_history_complete(client, mem_storage):
    io1, _, _, doc = setup_doc_with_versions(client)

    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io1)).json()
    assert [v["version_number"] for v in versions] == [3, 2, 1]

    by_number = {v["version_number"]: v for v in versions}
    assert by_number[1]["hash"] == sha256_hex(V1_BYTES)
    assert by_number[2]["hash"] == sha256_hex(V2_BYTES)
    assert by_number[3]["hash"] == sha256_hex(V3_BYTES)
    # Historical metadata (change notes) is preserved.
    assert by_number[2]["change_note"] == "updated findings"
    assert by_number[3]["change_note"] == "final revision"
    # Distinct rows.
    assert len({v["id"] for v in versions}) == 3


def test_each_version_has_distinct_stored_object(client, mem_storage):
    """Historical objects are immutable: v1/v2/v3 still hold their own bytes."""
    io1, _, _, doc = setup_doc_with_versions(client)

    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io1)).json()
    per_version = {}
    for v in versions:
        response = client.get(f"{VERSIONS}/{v['id']}/download", headers=auth(io1))
        assert response.status_code == 200
        per_version[v["version_number"]] = response.content

    assert per_version[1] == V1_BYTES
    assert per_version[2] == V2_BYTES
    assert per_version[3] == V3_BYTES


def test_current_version_pointers_update(client, mem_storage):
    io1, _, _, doc = setup_doc_with_versions(client)

    detail = client.get(f"{DOCS}/{doc['id']}", headers=auth(io1)).json()
    assert detail["current_version_number"] == 3
    assert detail["current_hash"] == sha256_hex(V3_BYTES)
    assert detail["file_name"] == "report.pdf"


def test_version_metadata_endpoint(client, mem_storage):
    io1, _, _, doc = setup_doc_with_versions(client)
    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io1)).json()
    vid = versions[0]["id"]

    response = client.get(f"{VERSIONS}/{vid}", headers=auth(io1))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == vid
    # Internal object keys are never exposed.
    assert "object_key" not in body


# --- Authorization ------------------------------------------------------------


def test_unauthorized_user_cannot_create_version(client, mem_storage):
    io1, io2, _, doc = setup_doc_with_versions(client)
    assert add_version(client, io2, doc["id"], b"%PDF-1.4 rogue").status_code == 404


def test_unauthorized_user_cannot_access_version_history(client, mem_storage):
    io1, io2, _, doc = setup_doc_with_versions(client)
    assert (
        client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io2)).status_code == 404
    )


def test_unauthorized_user_cannot_download_version(client, mem_storage):
    io1, io2, _, doc = setup_doc_with_versions(client)
    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io1)).json()
    vid = versions[0]["id"]
    assert client.get(f"{VERSIONS}/{vid}/download", headers=auth(io2)).status_code == 404


def test_unknown_document_endpoints_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = auth(login(client, "io1@example.com"))
    missing = uuid4()
    assert client.get(f"{DOCS}/{missing}/versions", headers=token).status_code == 404
    assert client.get(f"{DOCS}/{missing}/integrity", headers=token).status_code == 404
    assert (
        client.post(
            f"{DOCS}/{missing}/versions",
            files={"file": ("x.pdf", V1_BYTES, "application/pdf")},
            headers=token,
        ).status_code
        == 404
    )


# --- Integrity ---------------------------------------------------------------


def test_integrity_verified_for_unchanged_file(client, mem_storage):
    io1, _, _, doc = setup_doc_with_versions(client)
    response = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(io1))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "VERIFIED"
    assert body["version"] == 3
    assert body["stored_hash"] == body["current_hash"] == sha256_hex(V3_BYTES)
    assert body["verified_at"] is not None


def test_integrity_detects_tampering(client, mem_storage):
    """
    Realistic tampering: replace the bytes stored UNDERNEATH the current
    version's object (as an attacker with storage access would), then verify.
    stored_hash != recomputed hash → INTEGRITY_FAILURE (no auto-repair).
    """
    io1, _, _, doc = setup_doc_with_versions(client)

    # Find the current version's internal object key via its metadata endpoint
    # (admin would not see it either — for the test we use the storage directly
    # through the known deterministic key pattern).
    tampered = b"%PDF-1.4\nTAMPERED CONTENT inserted by attacker\n"
    mem_storage.save(
        f"case/{doc['case_id']}/doc-{doc['id']}/v3/report.pdf",
        tampered,
        "application/pdf",
    )

    response = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(io1))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "INTEGRITY_FAILURE"
    assert body["version"] == 3
    assert body["stored_hash"] == sha256_hex(V3_BYTES)
    assert body["current_hash"] == sha256_hex(tampered)
    assert body["stored_hash"] != body["current_hash"]
    assert body["verified_at"] is None


def test_integrity_unknown_document_rejected(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = auth(login(client, "io1@example.com"))
    assert client.get(f"{DOCS}/{uuid4()}/integrity", headers=token).status_code == 404


# --- Soft-delete consistency ----------------------------------------------------


def test_soft_deleted_document_keeps_history_in_db(client, mem_storage):
    """Deleting a document hides it, but DB rows/storage stay for the record."""
    from uuid import UUID as UuidType

    from app.models.document_version import DocumentVersion as DV
    from tests.conftest import TestSession

    io1, _, _, doc = setup_doc_with_versions(client)

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(io1)).status_code == 200
    # Everything is inaccessible through the API…
    assert client.get(f"{DOCS}/{doc['id']}", headers=auth(io1)).status_code == 404
    assert (
        client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(io1)).status_code == 404
    )
    assert (
        client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(io1)).status_code == 404
    )
    # …but the version rows still exist in the database (historical record).
    db = TestSession()
    remaining = db.query(DV).filter(DV.document_id == UuidType(doc["id"])).count()
    db.close()
    assert remaining == 3
