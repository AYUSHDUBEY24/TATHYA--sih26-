"""Recycle bin (soft delete + restore) and Your Access endpoint tests.

Reuses the existing test patterns (in-memory storage stub, real dependency
chain). Verifies:
  * delete -> restore keeps ONE version, no new version created
  * restore returns the document to the ACTIVE list
  * recycle-bin listing shows deleted_by/deleted_at from real audit entries
  * restore authorization: unrelated officer -> 404, plain member -> 403
  * DOCUMENT_DELETED / DOCUMENT_RESTORED audit events are written
  * /api/cases/{id}/access reflects the real computed permissions
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
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


def _make_case_and_doc(client: TestClient, token: str) -> tuple[dict, dict]:
    case = client.post(
        CASES,
        json={
            "title": "Recycle bin case",
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
    return case.json(), uploaded.json()


def test_delete_restore_roundtrip(client, mem_storage):
    register(client, "rb_io@example.com", "rb_io", "INVESTIGATING_OFFICER")
    token = login(client, "rb_io@example.com")
    case, doc = _make_case_and_doc(client, token)

    # Baseline ACTIVE, then soft-delete.
    deleted = client.delete(f"{DOCS}/{doc['id']}", headers=auth(token))
    assert deleted.status_code == 200, deleted.text

    # Document gone from the ACTIVE list...
    active = client.get(f"{DOCS}?case_id={case['id']}", headers=auth(token))
    assert active.status_code == 200
    assert all(d["id"] != doc["id"] for d in active.json())

    # ...but present in the recycle bin with real deleted_by info.
    recycle = client.get(
        f"{DOCS}/deleted?case_id={case['id']}", headers=auth(token)
    )
    assert recycle.status_code == 200, recycle.text
    entry = next(d for d in recycle.json() if d["id"] == doc["id"])
    assert entry["status"] == "DELETED"
    assert entry["deleted_by"] == "rb_io"
    assert entry["deleted_at"] is not None
    assert entry["can_delete"] is True  # uploader may restore

    # Restore returns it to the ACTIVE list...
    restored = client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(token))
    assert restored.status_code == 200, restored.text
    active = client.get(f"{DOCS}?case_id={case['id']}", headers=auth(token))
    assert any(d["id"] == doc["id"] for d in active.json())
    recycle = client.get(
        f"{DOCS}/deleted?case_id={case['id']}", headers=auth(token)
    )
    assert all(d["id"] != doc["id"] for d in recycle.json())


def test_restore_does_not_create_version(client, mem_storage):
    register(client, "rb_io2@example.com", "rb_io2", "INVESTIGATING_OFFICER")
    token = login(client, "rb_io2@example.com")
    _, doc = _make_case_and_doc(client, token)

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(token)).status_code == 200
    assert (
        client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(token)).status_code
        == 200
    )

    versions = client.get(f"{DOCS}/{doc['id']}/versions", headers=auth(token))
    assert versions.status_code == 200
    assert len(versions.json()) == 1  # exactly the original version

    # Integrity still verifies the same stored bytes.
    integrity = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(token))
    assert integrity.status_code == 200
    assert integrity.json()["status"] == "VERIFIED"

def test_restore_authorization(client, mem_storage):
    register(client, "rb_owner@example.com", "rb_owner", "INVESTIGATING_OFFICER")
    owner_token = login(client, "rb_owner@example.com")
    case, doc = _make_case_and_doc(client, owner_token)

    # An unrelated officer cannot even see/restore the deleted document.
    register(client, "rb_other@example.com", "rb_other", "INVESTIGATING_OFFICER")
    other_token = login(client, "rb_other@example.com")
    listing = client.get(
        f"{DOCS}/deleted?case_id={case['id']}", headers=auth(other_token)
    )
    assert listing.status_code == 404  # case authorization first (no leak)
    restore = client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(other_token))
    assert restore.status_code == 404

    # A plain case member (not manager, not uploader) can see the recycle bin
    # but cannot restore — 403 from the delete-level rule.
    register(client, "rb_member@example.com", "rb_member", "FORENSIC_OFFICER")
    member_token = login(client, "rb_member@example.com")
    add = client.post(
        f"{CASES}/{case['id']}/members",
        json={"email": "rb_member@example.com"},
        headers=auth(owner_token),
    )
    assert add.status_code == 201, add.text

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(owner_token)).status_code == 200
    listing = client.get(
        f"{DOCS}/deleted?case_id={case['id']}", headers=auth(member_token)
    )
    assert listing.status_code == 200
    entry = next(d for d in listing.json() if d["id"] == doc["id"])
    assert entry["can_delete"] is False
    restore = client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(member_token))
    assert restore.status_code == 403

    # ADMIN can restore.
    register(client, "rb_admin@example.com", "rb_admin", "ADMIN")
    admin_token = login(client, "rb_admin@example.com")
    restore = client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(admin_token))
    assert restore.status_code == 200


def test_delete_and_restore_audit_events(client, mem_storage):
    register(client, "rb_aud@example.com", "rb_aud", "INVESTIGATING_OFFICER")
    token = login(client, "rb_aud@example.com")
    _, doc = _make_case_and_doc(client, token)

    assert client.delete(f"{DOCS}/{doc['id']}", headers=auth(token)).status_code == 200
    assert client.post(f"{DOCS}/{doc['id']}/restore", headers=auth(token)).status_code == 200

    register(client, "rb_aud_admin@example.com", "rb_aud_admin", "ADMIN")
    admin_token = login(client, "rb_aud_admin@example.com")
    logs = client.get("/api/audit?limit=100", headers=auth(admin_token))
    assert logs.status_code == 200
    actions = [e["action"] for e in logs.json()]
    assert "DOCUMENT_DELETED" in actions
    assert "DOCUMENT_RESTORED" in actions


def test_case_access_endpoint(client, mem_storage):
    register(client, "rb_acc_io@example.com", "rb_acc_io", "INVESTIGATING_OFFICER")
    io_token = login(client, "rb_acc_io@example.com")
    case, _ = _make_case_and_doc(client, io_token)

    # The case creator (IO) sees real computed permissions.
    access = client.get(f"{CASES}/{case['id']}/access", headers=auth(io_token))
    assert access.status_code == 200, access.text
    body = access.json()
    assert body["role"] == "INVESTIGATING_OFFICER"
    assert body["can_read"] is True
    assert body["can_upload"] is True
    assert body["can_create_version"] is True
    assert body["can_verify_integrity"] is True
    assert body["can_manage_case"] is True  # creator
    assert body["can_administer"] is False

    # An unrelated officer gets 404 (no existence leak), like every case route.
    register(client, "rb_acc_other@example.com", "rb_acc_other", "PROSECUTOR")
    other_token = login(client, "rb_acc_other@example.com")
    assert (
        client.get(f"{CASES}/{case['id']}/access", headers=auth(other_token)).status_code
        == 404
    )

    # ADMIN sees administer=True.
    register(client, "rb_acc_admin@example.com", "rb_acc_admin", "ADMIN")
    admin_token = login(client, "rb_acc_admin@example.com")
    body = client.get(f"{CASES}/{case['id']}/access", headers=auth(admin_token)).json()
    assert body["can_administer"] is True
    assert body["can_manage_case"] is True
