"""
Phase 7 tests — blockchain hash anchoring.

The Hardhat contract itself is tested separately via ``npx hardhat test``
(see ../blockchain/test). These backend tests verify the FastAPI integration
using a mocked BlockchainService so they run without a live Hardhat node, and
they exercise the graceful-degradation paths explicitly.

Mocking target note
-------------------
The API functions perform a *local* import::

    from app.services.blockchain_service import get_blockchain_service

inside each handler, so the symbol that must be patched is the attribute on the
``app.services.blockchain_service`` module — NOT ``app.api.blockchain.get_blockchain_service``
(which would create an unused attribute the handlers never import).
"""

from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch

import pytest

from app.core.hashing import sha256_hex
from app.main import app
from app.services.blockchain_service import BlockchainError, BlockchainService
from app.storage import InMemoryStorage, get_storage

CASES = "/api/cases"
DOCS = "/api/documents"
BLOCKCHAIN = "/api/blockchain"
PASSWORD = "Str0ngPass!x"

V1_BYTES = b"%PDF-1.4\nversion one content\n"
V2_BYTES = b"%PDF-1.4\nversion two content (updated)\n"


@pytest.fixture
def mem_storage(client):
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.pop(get_storage, None)


def register(client, email, username, role="INVESTIGATING_OFFICER"):
    resp = client.post("/api/auth/register", json={
        "email": email, "username": username, "password": PASSWORD,
        "full_name": username.replace("_", " ").title(), "role": role,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def login(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def make_case(client, token):
    resp = client.post(CASES, json={
        "title": "Blockchain case", "crime_type": "FRAUD",
        "police_station": "Central PS",
    }, headers=auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


def upload_doc(client, token, case_id, file_bytes=V1_BYTES, filename="doc.pdf"):
    resp = client.post(
        f"{DOCS}/upload",
        files={"file": (filename, file_bytes, "application/pdf")},
        data={"case_id": case_id, "document_type": "INVESTIGATION_REPORT",
              "classification": "RESTRICTED", "description": "blockchain test"},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def add_version(client, token, document_id, file_bytes=V2_BYTES,
                change_note="updated", filename="doc.pdf"):
    resp = client.post(
        f"{DOCS}/{document_id}/versions",
        files={"file": (filename, file_bytes, "application/pdf")},
        data={"change_note": change_note}, headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def setup_doc(client):
    """Register io1/io2, create a case + document (v1). Returns (io1, io2, doc).

    Anchoring is NOOPed during upload so no PENDING/FAILED BlockchainRecord is
    created — each test builds the blockchain state it needs from a clean slate.
    """
    register(client, "io1@example.com", "io_officer_1")
    register(client, "io2@example.com", "io_officer_2")
    io1 = login(client, "io1@example.com")
    io2 = login(client, "io2@example.com")
    case = make_case(client, io1)
    with patch("app.api.documents._anchor_version"):
        doc = upload_doc(client, io1, case["id"])
    return io1, io2, doc


PATCH = "app.services.blockchain_service.get_blockchain_service"


def _fake_register_result(tx_hex="0x" + "ab" * 32, block=42):
    return {
        "tx_hash": tx_hex,
        "block_number": block,
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }


# --- Phase 7 tests --------------------------------------------------------


def test_contract_abi_exposes_expected_interface():
    """Solidity contract exposes the functions the service relies on."""
    abi = BlockchainService._load_abi()
    names = {f["name"] for f in abi if f.get("type") == "function"}
    assert "registerDocumentHash" in names
    assert "isAnchored" in names
    assert "getAnchor" in names


def test_register_success_stores_tx_hash_and_confirmed_status(client, mem_storage):
    """A successful on-chain registration stores tx_hash + CONFIRMED."""
    io1, _, doc = setup_doc(client)
    fake = _fake_register_result(tx_hex="0x" + "de" * 32, block=7)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = fake
        resp = client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "CONFIRMED"
    assert body["transaction_hash"] == fake["tx_hash"]
    assert body["block_number"] == 7
    assert body["anchored_at"] is not None


def test_status_endpoint_returns_anchored_fields(client, mem_storage):
    """Hash retrieval: /status reflects the persisted CONFIRMED anchor."""
    io1, _, doc = setup_doc(client)
    fake = _fake_register_result(block=99)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = fake
        client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
    resp = client.get(f"{BLOCKCHAIN}/{doc['id']}/status", headers=auth(io1))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "CONFIRMED"
    assert body["version_number"] == 1
    assert body["blockchain_key"] == f"{doc['id']}:1"
    assert body["transaction_hash"] == fake["tx_hash"]
    assert body["block_number"] == 99
    assert body["anchored_at"] is not None


def test_register_returns_confirmed_with_transaction_status(client, mem_storage):
    """Transaction/hash status behavior: confirmed + queryable via /status."""
    io1, _, doc = setup_doc(client)
    fake = _fake_register_result(block=4242)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = fake
        resp = client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "CONFIRMED"
    assert body["block_number"] == 4242
    st = client.get(
        f"{BLOCKCHAIN}/{doc['id']}/status", headers=auth(io1)
    ).json()
    assert st["status"] == "CONFIRMED"
    assert st["transaction_hash"] == fake["tx_hash"]
    assert st["block_number"] == 4242


def test_duplicate_register_is_idempotent(client, mem_storage):
    """Calling register twice must NOT perform a second on-chain tx."""
    io1, _, doc = setup_doc(client)
    fake = _fake_register_result()
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = fake
        r1 = client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "CONFIRMED"
        first_calls = mock_dep.return_value.register_hash.call_count
        r2 = client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "CONFIRMED"
        assert mock_dep.return_value.register_hash.call_count == first_calls


def test_register_nonexistent_document_returns_404(client, mem_storage):
    """Invalid/absent document_id -> 404 (no existence leak)."""
    io1, _, _ = setup_doc(client)
    bogus = str(uuid4())
    resp = client.post(
        f"{BLOCKCHAIN}/register?document_id={bogus}",
        headers=auth(io1),
    )
    assert resp.status_code == 404


def test_register_anchors_specific_version(client, mem_storage):
    """Anchoring targets the requested version (v2), keyed as <doc>:2."""
    io1, _, doc = setup_doc(client)
    with patch("app.api.documents._anchor_version"):
        add_version(client, io1, doc["id"], V2_BYTES, "updated findings")
    fake = _fake_register_result(block=12)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = fake
        resp = client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}&version_number=2",
            headers=auth(io1),
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "CONFIRMED"
    assert body["version_number"] == 2
    assert body["blockchain_key"] == f"{doc['id']}:2"
    mock_dep.return_value.register_hash.assert_called_once()
    args = mock_dep.return_value.register_hash.call_args[0]
    assert args[0] == f"{doc['id']}:2"
    assert args[1] == sha256_hex(V2_BYTES)


def test_confirm_status_persisted_as_confirmed(client, mem_storage):
    """CONFIRMED blockchain status is persisted and queryable."""
    io1, _, doc = setup_doc(client)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = _fake_register_result()
        client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
    st = client.get(
        f"{BLOCKCHAIN}/{doc['id']}/status", headers=auth(io1)
    ).json()
    assert st["status"] == "CONFIRMED"
    assert st["transaction_hash"].startswith("0x")
    assert st["blockchain_key"] == f"{doc['id']}:1"


def test_verify_all_layers_match_returns_verified(client, mem_storage):
    """File hash == DB hash == blockchain hash -> VERIFIED."""
    io1, _, doc = setup_doc(client)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = _fake_register_result()
        client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
        mock_dep.return_value.get_anchor.return_value = {
            "hash": "0x" + sha256_hex(V1_BYTES),
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }
        resp = client.get(f"{BLOCKCHAIN}/{doc['id']}/verify", headers=auth(io1))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "VERIFIED"
    assert body["file_hash"] == body["stored_hash"] == body["blockchain_hash"]
    assert body["file_hash"] == sha256_hex(V1_BYTES)


def test_verify_file_mismatch_detected(client, mem_storage):
    """Stored bytes differ from the DB hash -> FILE_INTEGRITY_FAILURE."""
    io1, _, doc = setup_doc(client)
    tampered = b"%PDF-1.4\nTAMPERED\n"
    mem_storage.save(
        f"case/{doc['case_id']}/doc-{doc['id']}/v1/doc.pdf",
        tampered, "application/pdf",
    )
    resp = client.get(f"{BLOCKCHAIN}/{doc['id']}/verify", headers=auth(io1))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "FILE_INTEGRITY_FAILURE"
    assert body["file_hash"] == sha256_hex(tampered)
    assert body["stored_hash"] != body["file_hash"]


def test_verify_blockchain_mismatch_detected(client, mem_storage):
    """DB hash differs from the on-chain hash -> BLOCKCHAIN_MISMATCH."""
    io1, _, doc = setup_doc(client)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = _fake_register_result()
        client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
        mock_dep.return_value.get_anchor.return_value = {
            "hash": "0x" + "ff" * 32,
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }
        resp = client.get(f"{BLOCKCHAIN}/{doc['id']}/verify", headers=auth(io1))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "BLOCKCHAIN_MISMATCH"
    assert body["blockchain_hash"] == "ff" * 32
    assert body["blockchain_hash"] != body["stored_hash"]


def test_upload_succeeds_when_blockchain_unavailable(client, mem_storage):
    """Graceful degradation: blockchain unconfigured -> upload still 201, FAILED record."""
    register(client, "io1@example.com", "io_officer_1")
    io1 = login(client, "io1@example.com")
    case = make_case(client, io1)
    # Force the unavailable condition explicitly so the test does not depend on
    # whether a real Hardhat node happens to be running: the anchored service
    # raises on register_hash, exactly like an unreachable/unconfigured node.
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.side_effect = BlockchainError("node down")
        # The upload must still succeed and the record must be marked FAILED.
        # upload_doc asserts 201 and returns the JSON body.
        doc = upload_doc(client, io1, case["id"])
    status = client.get(f"{BLOCKCHAIN}/{doc['id']}/status", headers=auth(io1))
    assert status.status_code == 200
    assert status.json()["status"] == "FAILED"
    # Document is still usable despite the blockchain failure.
    dl = client.get(f"{DOCS}/{doc['id']}/download", headers=auth(io1))
    assert dl.status_code == 200


def test_verify_blockchain_unavailable_degraded(client, mem_storage):
    """When the on-chain lookup raises, verify degrades to BLOCKCHAIN_UNAVAILABLE."""
    io1, _, doc = setup_doc(client)
    with patch(PATCH) as mock_dep:
        mock_dep.return_value.register_hash.return_value = _fake_register_result()
        client.post(
            f"{BLOCKCHAIN}/register?document_id={doc['id']}",
            headers=auth(io1),
        )
        mock_dep.return_value.get_anchor.side_effect = BlockchainError("node down")
        resp = client.get(f"{BLOCKCHAIN}/{doc['id']}/verify", headers=auth(io1))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "BLOCKCHAIN_UNAVAILABLE"
    # File layer is still evaluated (hash reported even when blockchain is down).
    assert body["file_hash"] == sha256_hex(V1_BYTES)


def test_unauthorized_cannot_register_or_verify(client, mem_storage):
    """io2 cannot register/verify io1's document (no access -> 404, no leak)."""
    io1, io2, doc = setup_doc(client)
    reg = client.post(
        f"{BLOCKCHAIN}/register?document_id={doc['id']}",
        headers=auth(io2),
    )
    assert reg.status_code == 404
    verify = client.get(
        f"{BLOCKCHAIN}/{doc['id']}/verify", headers=auth(io2)
    )
    assert verify.status_code == 404
    status = client.get(
        f"{BLOCKCHAIN}/{doc['id']}/status", headers=auth(io2)
    )
    assert status.status_code == 404


def test_unauthenticated_blockchain_endpoints_return_401(client, mem_storage):
    """No JWT -> 401 on register, verify and status."""
    _, _, doc = setup_doc(client)
    assert client.post(
        f"{BLOCKCHAIN}/register?document_id={doc['id']}"
    ).status_code == 401
    assert client.get(
        f"{BLOCKCHAIN}/{doc['id']}/verify"
    ).status_code == 401
    assert client.get(
        f"{BLOCKCHAIN}/{doc['id']}/status"
    ).status_code == 401

