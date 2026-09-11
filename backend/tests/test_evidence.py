"""Chain-of-custody (evidence) endpoint tests.

Verifies:
  * register -> first REGISTERED custody event exists
  * transfers append and update asset status/current_holder
  * chain endpoint returns the full ordered timeline (real data only)
  * authorization: non-member officer -> 404, anonymous -> 401
  * EVIDENCE_REGISTERED / EVIDENCE_TRANSFERRED audit events are written
  * invalid asset_type/action rejected with 422
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app

EVID = "/api/evidence"
CASES = "/api/cases"
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


def _make_case(client: TestClient, token: str) -> dict:
    response = client.post(
        CASES,
        json={
            "title": "Custody case",
            "crime_type": "THEFT",
            "police_station": "Central PS",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _register_asset(client: TestClient, token: str, case_id: str) -> dict:
    response = client.post(
        f"{EVID}?payload_case_id={case_id}",
        json={
            "name": "Seized Laptop",
            "asset_type": "LAPTOP",
            "current_holder": "Investigating Officer",
        },
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_register_creates_first_custody_event(client):
    register(client, "ev_io@example.com", "ev_io", "INVESTIGATING_OFFICER")
    token = login(client, "ev_io@example.com")
    case = _make_case(client, token)
    asset = _register_asset(client, token, case["id"])

    assert asset["asset_tag"] == "EV-0001"
    assert asset["status"] == "REGISTERED"
    assert len(asset["transfers"]) == 1
    assert asset["transfers"][0]["action"] == "REGISTERED"
    assert asset["transfers"][0]["to_party"] == "Investigating Officer"


def test_transfer_updates_chain_and_status(client):
    register(client, "ev_io2@example.com", "ev_io2", "INVESTIGATING_OFFICER")
    token = login(client, "ev_io2@example.com")
    case = _make_case(client, token)
    asset = _register_asset(client, token, case["id"])

    r = client.post(
        f"{EVID}/{asset['id']}/transfers",
        json={
            "action": "TRANSFERRED",
            "from_party": "Investigating Officer",
            "to_party": "Central Forensic Lab",
            "purpose": "Forensic examination of seized laptop",
        },
        headers=auth(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "IN_CUSTODY"
    assert body["current_holder"] == "Central Forensic Lab"
    assert [t["action"] for t in body["transfers"]] == [
        "REGISTERED",
        "TRANSFERRED",
    ]

    # Chain endpoint returns the same ordered timeline with case context.
    r = client.get(f"{EVID}/{asset['id']}/chain", headers=auth(token))
    assert r.status_code == 200, r.text
    chain = r.json()
    assert chain["case_number"] == case["case_number"]
    assert len(chain["transfers"]) == 2
    assert chain["transfers"][1]["purpose"] == "Forensic examination of seized laptop"


def test_chain_authorization_non_member_gets_404(client):
    register(client, "ev_owner@example.com", "ev_owner", "INVESTIGATING_OFFICER")
    register(client, "ev_other@example.com", "ev_other", "INVESTIGATING_OFFICER")
    owner = login(client, "ev_owner@example.com")
    other = login(client, "ev_other@example.com")
    case = _make_case(client, owner)
    asset = _register_asset(client, owner, case["id"])

    # Non-member cannot list, read chain, or transfer (404 — not existence-revealing).
    assert (
        client.get(f"{EVID}?case_id={case['id']}", headers=auth(other)).status_code
        == 404
    )
    assert (
        client.get(f"{EVID}/{asset['id']}/chain", headers=auth(other)).status_code
        == 404
    )
    assert (
        client.post(
            f"{EVID}/{asset['id']}/transfers",
            json={"action": "EXAMINED"},
            headers=auth(other),
        ).status_code
        == 404
    )
    # Anonymous -> 401.
    assert client.get(f"{EVID}?case_id={case['id']}").status_code == 401


def test_invalid_type_and_action_rejected(client):
    register(client, "ev_io3@example.com", "ev_io3", "INVESTIGATING_OFFICER")
    token = login(client, "ev_io3@example.com")
    case = _make_case(client, token)

    r = client.post(
        f"{EVID}?payload_case_id={case['id']}",
        json={
            "name": "Bad type asset",
            "asset_type": "SPACESHIP",
            "current_holder": "IO",
        },
        headers=auth(token),
    )
    assert r.status_code == 422

    asset = _register_asset(client, token, case["id"])
    r = client.post(
        f"{EVID}/{asset['id']}/transfers",
        json={"action": "VANISHED"},
        headers=auth(token),
    )
    assert r.status_code == 422


def test_evidence_audit_events_written(client):
    register(client, "ev_admin@example.com", "ev_admin", "ADMIN")
    token = login(client, "ev_admin@example.com")
    case = _make_case(client, token)
    asset = _register_asset(client, token, case["id"])
    client.post(
        f"{EVID}/{asset['id']}/transfers",
        json={"action": "STORED", "to_party": "Malkhana"},
        headers=auth(token),
    )

    r = client.get(f"/api/audit?limit=100", headers=auth(token))
    assert r.status_code == 200, r.text
    entries = r.json()
    relevant = {
        e["action"] for e in entries if e.get("entity_id") == asset["id"]
    }
    assert "EVIDENCE_REGISTERED" in relevant
    assert "EVIDENCE_TRANSFERRED" in relevant
