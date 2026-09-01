"""
Phase 3 case management tests.

Authorization rules under test (docs/security.md + Phase 3 task):
- ADMIN sees/edits all cases; deletion is ADMIN-only
- INVESTIGATING_OFFICER creates cases; creator and assigned IO become members
- Visibility: membership or assigned-IO only (others get 404 — no existence leak)
- Membership management: ADMIN/creator/assigned IO; duplicates rejected
"""

from uuid import uuid4

from fastapi.testclient import TestClient

CASES = "/api/cases"
USERS = "/api/users"
PASSWORD = "Str0ngPass!x"


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


def create_case(client: TestClient, token: str, **overrides):
    payload = {
        "title": "Robbery at Central Market",
        "description": "Synthetic demo case",
        "crime_type": "ROBBERY",
        "police_station": "Central Police Station",
        **overrides,
    }
    return client.post(CASES, json=payload, headers=auth(token))


def test_io_can_create_case(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")

    response = create_case(client, token)
    assert response.status_code == 201, response.text
    case = response.json()
    assert case["case_number"].startswith("CASE-")
    assert case["status"] == "OPEN"
    # Creator automatically became a case member.
    assert any(m["username"] == "io_one" for m in case["members"])


def test_create_case_requires_authentication(client):
    response = client.post(
        CASES,
        json={
            "title": "No auth case",
            "crime_type": "THEFT",
            "police_station": "Somewhere PS",
        },
    )
    assert response.status_code == 401


def test_create_case_forbidden_for_forensic_role(client):
    register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    token = login(client, "f@example.com")
    assert create_case(client, token).status_code == 403


def test_case_visible_to_authorized_user(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    token = login(client, "io1@example.com")
    case = create_case(client, token).json()

    listed = client.get(CASES, headers=auth(token)).json()
    assert any(c["id"] == case["id"] for c in listed)

    detail = client.get(f"{CASES}/{case['id']}", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["case_number"] == case["case_number"]


def test_unauthorized_user_cannot_retrieve_case(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")

    case = create_case(client, io1).json()

    # Changing the case ID in the URL must not leak the case.
    assert client.get(f"{CASES}/{case['id']}", headers=auth(io2)).status_code == 404
    listed = client.get(CASES, headers=auth(io2)).json()
    assert all(c["id"] != case["id"] for c in listed)


def test_admin_can_access_all_cases(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    admin = login(client, "admin@example.com")

    case = create_case(client, io1).json()

    assert client.get(f"{CASES}/{case['id']}", headers=auth(admin)).status_code == 200
    listed = client.get(CASES, headers=auth(admin)).json()
    assert any(c["id"] == case["id"] for c in listed)


def test_assigned_io_can_access_case_without_membership(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    io2_reg = register(
        client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER"
    )
    admin = login(client, "admin@example.com")
    io2 = login(client, "io2@example.com")

    case = create_case(client, admin, assigned_io_id=io2_reg["id"]).json()

    # Admin removes io_two's membership; io_two must still see the case
    # through the assigned-IO rule.
    removed = client.delete(
        f"{CASES}/{case['id']}/members/{io2_reg['id']}", headers=auth(admin)
    )
    assert removed.status_code == 200

    detail = client.get(f"{CASES}/{case['id']}", headers=auth(io2))
    assert detail.status_code == 200
    assert detail.json()["assigned_io"]["id"] == io2_reg["id"]


def test_assigned_io_synced_into_members_on_create(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io2_reg = register(
        client, "io2@example.com", "io_two", "INVESTIGATING_OFFICER"
    )
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1, assigned_io_id=io2_reg["id"]).json()
    assert case["assigned_io"]["id"] == io2_reg["id"]
    assert io2_reg["id"] in {m["user_id"] for m in case["members"]}


def test_add_case_member(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1).json()
    response = client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": f_reg["id"], "role_in_case": "FORENSIC_EXAMINER"},
        headers=auth(io1),
    )
    assert response.status_code == 201, response.text
    assert response.json()["role_in_case"] == "FORENSIC_EXAMINER"

    # The new member can now access the case.
    f_token = login(client, "f@example.com")
    assert client.get(f"{CASES}/{case['id']}", headers=auth(f_token)).status_code == 200


def test_add_member_by_email(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1).json()
    response = client.post(
        f"{CASES}/{case['id']}/members",
        json={"email": "f@example.com"},
        headers=auth(io1),
    )
    assert response.status_code == 201
    assert response.json()["username"] == "forensic_user"


def test_duplicate_membership_rejected(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1).json()
    response = client.post(
        f"{CASES}/{case['id']}/members",
        json={"email": "io1@example.com"},
        headers=auth(io1),
    )
    assert response.status_code == 409


def test_membership_removal_works(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    admin = login(client, "admin@example.com")
    f_token = login(client, "f@example.com")

    case = create_case(client, admin).json()
    client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": f_reg["id"]},
        headers=auth(admin),
    )
    assert client.get(f"{CASES}/{case['id']}", headers=auth(f_token)).status_code == 200

    removed = client.delete(
        f"{CASES}/{case['id']}/members/{f_reg['id']}", headers=auth(admin)
    )
    assert removed.status_code == 200
    # Membership gone → forensic user can no longer access the case.
    assert client.get(f"{CASES}/{case['id']}", headers=auth(f_token)).status_code == 404


def test_unauthorized_membership_modification_rejected(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    register(client, "out@example.com", "outsider", "PROSECUTOR")
    io1 = login(client, "io1@example.com")
    f_token = login(client, "f@example.com")
    outsider = login(client, "out@example.com")

    case = create_case(client, io1).json()
    # Make the forensic user a plain member (no management rights).
    client.post(
        f"{CASES}/{case['id']}/members",
        json={"email": "f@example.com"},
        headers=auth(io1),
    )
    # Plain member → cannot manage members (403).
    as_member = client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": str(uuid4())},
        headers=auth(f_token),
    )
    assert as_member.status_code == 403
    # Outsider cannot even see the case → 404 (no existence leak).
    as_outsider = client.post(
        f"{CASES}/{case['id']}/members",
        json={"email": "f@example.com"},
        headers=auth(outsider),
    )
    assert as_outsider.status_code == 404


def test_case_update_works(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1).json()
    response = client.put(
        f"{CASES}/{case['id']}",
        json={"status": "UNDER_INVESTIGATION", "title": "Robbery — updated"},
        headers=auth(io1),
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "UNDER_INVESTIGATION"
    assert updated["title"] == "Robbery — updated"


def test_case_update_forbidden_for_plain_member(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    f_reg = register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    admin = login(client, "admin@example.com")
    f_token = login(client, "f@example.com")

    case = create_case(client, admin).json()
    client.post(
        f"{CASES}/{case['id']}/members",
        json={"user_id": f_reg["id"]},
        headers=auth(admin),
    )
    response = client.put(
        f"{CASES}/{case['id']}", json={"status": "CLOSED"}, headers=auth(f_token)
    )
    assert response.status_code == 403


def test_case_deletion_admin_only(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    admin = login(client, "admin@example.com")
    io1 = login(client, "io1@example.com")

    case = create_case(client, io1).json()

    assert client.delete(f"{CASES}/{case['id']}", headers=auth(io1)).status_code == 403
    assert client.delete(f"{CASES}/{case['id']}", headers=auth(admin)).status_code == 200
    assert client.get(f"{CASES}/{case['id']}", headers=auth(admin)).status_code == 404


def test_invalid_status_rejected(client):
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    io1 = login(client, "io1@example.com")
    assert create_case(client, io1, status="ON_HOLD").status_code == 422


def test_officers_listing_for_assignment(client):
    register(client, "admin@example.com", "admin_user", "ADMIN")
    register(client, "io1@example.com", "io_one", "INVESTIGATING_OFFICER")
    register(client, "f@example.com", "forensic_user", "FORENSIC_OFFICER")
    admin = login(client, "admin@example.com")
    f_token = login(client, "f@example.com")

    officers = client.get(f"{USERS}/officers", headers=auth(admin))
    assert officers.status_code == 200
    assert [o["username"] for o in officers.json()] == ["io_one"]

    assert client.get(f"{USERS}/officers", headers=auth(f_token)).status_code == 403
