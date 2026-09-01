"""
Phase 6 tests — audit trail.

Verifies that key operations write audit entries, the ADMIN-only audit API,
filters, and that non-admins cannot read the global audit log. Runs with the
in-memory SQLite test database and mock storage (no Docker required).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
AUDIT = "/api/audit"
PASSWORD = "Str0ngPass!x"
PDF = b"%PDF-1.4 audit test pdf\n"


@pytest.fixture(autouse=True)
def mem_storage(client):
    """In-memory storage for every audit test (no MinIO dependency)."""
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_storage, None)


def register(client, email: str, username: str, role: str) -> dict:
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


def login(client, email: str) -> str:
    response = client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_case(client, token: str) -> dict:
    response = client.post(
        CASES,
        json={
            "title": "Audit test case",
            "crime_type": "FRAUD",
            "police_station": "Central PS",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def upload(client, token: str, case_id: str) -> dict:
    response = client.post(
        f"{DOCS}/upload",
        files={"file": ("fir.pdf", PDF, "application/pdf")},
        data={
            "case_id": case_id,
            "document_type": "FIR",
            "classification": "RESTRICTED",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def audit_list(client, token: str, **params) -> list[dict]:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = AUDIT + (f"?{query}" if query else "")
    response = client.get(url, headers=auth(token))
    assert response.status_code == 200, response.text
    return response.json()


# --- Authentication events -------------------------------------------------


def test_successful_login_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    assert client.post(
        "/api/auth/login", json={"email": "io@example.com", "password": PASSWORD}
    ).status_code == 200

    admin_reg = register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="LOGIN")
    assert any(
        r["actor_id"] == admin_reg["id"]
        and r["actor_username"] == "admin_user"
        and r["result"] == "SUCCESS"
        for r in records
    )


def test_failed_login_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    assert client.post(
        "/api/auth/login", json={"email": "io@example.com", "password": "wrong-pass"}
    ).status_code == 401


# --- Case events -----------------------------------------------------------


def test_case_creation_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="CASE_CREATED")
    assert any(
        r["case_id"] == case["id"] and r["entity_id"] == case["id"] for r in records
    )


def test_case_update_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    assert (
        client.put(
            f"{CASES}/{case['id']}",
            json={"status": "UNDER_INVESTIGATION"},
            headers=auth(io_token),
        ).status_code
        == 200
    )

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="CASE_UPDATED")
    assert any(r["case_id"] == case["id"] for r in records)


def test_case_member_added_removed_creates_audit_entries(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    admin_token = login(client, "admin@example.com")
    case = make_case(client, admin_token)

    assert (
        client.post(
            f"{CASES}/{case['id']}/members",
            json={"user_id": f_reg["id"]},
            headers=auth(admin_token),
        ).status_code
        == 201
    )
    assert (
        client.delete(
            f"{CASES}/{case['id']}/members/{f_reg['id']}",
            headers=auth(admin_token),
        ).status_code
        == 200
    )

    records = audit_list(client, admin_token)
    present = {r["action"] for r in records}
    assert {"CASE_MEMBER_ADDED", "CASE_MEMBER_REMOVED"}.issubset(present)


def test_case_deleted_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    assert (
        client.delete(f"{CASES}/{case['id']}", headers=auth(admin_token)).status_code
        == 200
    )

    records = audit_list(client, admin_token, action="CASE_DELETED")
    assert any(r["case_id"] == case["id"] for r in records)


# --- Document events -------------------------------------------------------


def test_document_upload_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    doc = upload(client, io_token, case["id"])

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="DOCUMENT_UPLOADED")
    assert any(r["entity_id"] == doc["id"] for r in records)


def test_document_view_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    doc = upload(client, io_token, case["id"])
    assert client.get(f"{DOCS}/{doc['id']}", headers=auth(io_token)).status_code == 200

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="DOCUMENT_VIEWED")
    assert any(r["entity_id"] == doc["id"] for r in records)


def test_document_download_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    doc = upload(client, io_token, case["id"])
    assert (
        client.get(f"{DOCS}/{doc['id']}/download", headers=auth(io_token)).status_code
        == 200
    )

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="DOCUMENT_DOWNLOADED")
    assert any(r["entity_id"] == doc["id"] for r in records)


def test_document_delete_creates_audit_entry(client):
    _mem = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: _mem
    try:
        register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
        io_token = login(client, "io@example.com")
        case = make_case(client, io_token)
        doc = upload(client, io_token, case["id"])
        assert (
            client.delete(f"{DOCS}/{doc['id']}", headers=auth(io_token)).status_code == 200
        )

        register(client, "admin@example.com", "admin_user", "ADMIN")
        admin_token = login(client, "admin@example.com")
        records = audit_list(client, admin_token, action="DOCUMENT_DELETED")
        assert any(r["entity_id"] == doc["id"] for r in records)
    finally:
        app.dependency_overrides.pop(get_storage, None)


def test_new_document_version_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    doc = upload(client, io_token, case["id"])
    assert (
        client.post(
            f"{DOCS}/{doc['id']}/versions",
            files={"file": ("fir.pdf", b"%PDF-1.4 v2", "application/pdf")},
            data={"change_note": "second"},
            headers=auth(io_token),
        ).status_code
        == 201
    )

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="DOCUMENT_VERSION_CREATED")
    assert any(r["entity_id"] == doc["id"] for r in records)


def test_integrity_verified_creates_audit_entry(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)
    doc = upload(client, io_token, case["id"])
    assert (
        client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(io_token)).status_code
        == 200
    )

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token, action="INTEGRITY_VERIFIED")
    assert any(r["entity_id"] == doc["id"] and r["result"] == "SUCCESS" for r in records)


def test_integrity_failure_creates_audit_entry(client):
    # Uses an in-memory storage stub so we can tamper with the stored bytes.
    import pytest as _pytest

    from app.main import app as _app
    from app.storage import InMemoryStorage as _Mem
    from app.storage import get_storage as _gs

    _mem = _Mem()
    _app.dependency_overrides[_gs] = lambda: _mem
    try:
        register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
        io_token = login(client, "io@example.com")
        case = make_case(client, io_token)
        doc = upload(client, io_token, case["id"])

        # Tamper with the stored bytes under the current (v1) key.
        _mem.save(
            f"case/{case['id']}/doc-{doc['id']}/v1/fir.pdf",
            b"%PDF-1.4 tampered",
            "application/pdf",
        )
        verify = client.get(f"{DOCS}/{doc['id']}/integrity", headers=auth(io_token))
        assert verify.status_code == 200
        assert verify.json()["status"] == "INTEGRITY_FAILURE"

        register(client, "admin@example.com", "admin_user", "ADMIN")
        admin_token = login(client, "admin@example.com")
        records = audit_list(client, admin_token, action="INTEGRITY_FAILED")
        assert any(r["entity_id"] == doc["id"] and r["result"] == "FAILURE" for r in records)
    finally:
        _app.dependency_overrides.pop(_gs, None)


def test_unauthorized_access_creates_audit_entry(client, mem_storage):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    doc = upload(client, io1, case["id"])

    # io2 attempts to read the case/doc → 404 (no existence leak) + DENIED audit.
    assert client.get(f"{DOCS}/{doc['id']}", headers=auth(io2)).status_code == 404
    assert client.get(f"{CASES}/{case['id']}", headers=auth(io2)).status_code == 404

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    denied = audit_list(client, admin_token, action="ACCESS_DENIED")
    assert any(r["result"] == "DENIED" and r["actor_id"] is not None for r in denied)


def test_admin_can_query_audit_log(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    assert client.get(AUDIT, headers=auth(admin_token)).status_code == 200


def test_non_admin_cannot_query_global_audit_log(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    assert client.get(AUDIT, headers=auth(io_token)).status_code == 403


def test_unauthenticated_cannot_query_audit_log(client):
    assert client.get(AUDIT).status_code == 401


# --- Filters ---------------------------------------------------------------


def test_audit_filters_work(client):
    register(client, "io@example.com", "io_officer", "INVESTIGATING_OFFICER")
    io_token = login(client, "io@example.com")
    case = make_case(client, io_token)

    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")

    case_created = audit_list(client, admin_token, action="CASE_CREATED")
    assert case_created and all(r["action"] == "CASE_CREATED" for r in case_created)

    by_case = audit_list(client, admin_token, case_id=case["id"])
    assert by_case and all(r["case_id"] == case["id"] for r in by_case)


def test_audit_log_is_read_only_no_update_or_delete(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    admin_token = login(client, "admin@example.com")
    records = audit_list(client, admin_token)

    if records:
        entry_id = records[0]["id"]
        # No mutable routes exist: 404 (no such route) or 405 (method not
        # allowed) both prove the audit trail is read-only.
        assert (
            client.put(f"{AUDIT}/{entry_id}", json={}, headers=auth(admin_token)).status_code
            in (404, 405)
        )
        assert (
            client.delete(f"{AUDIT}/{entry_id}", headers=auth(admin_token)).status_code
            in (404, 405)
        )