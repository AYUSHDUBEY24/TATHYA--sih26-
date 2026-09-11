"""LIVE end-to-end blockchain + integrity + tamper test against the running
backend (FastAPI on :8000, PostgreSQL, MinIO, Hardhat on :8545).

This creates a brand-new user/case/document so we are NOT relying on any old
database records. It registers a REAL blockchain transaction, reads it back
from the Solidity contract, verifies, then runs the tamper -> detect ->
restore -> verified flow.

Run: backend/.venv/Scripts/python.exe tools/live_e2e_test.py
"""
import time
import uuid

import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = None


def api(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    resp = httpx.request(method, BASE + path, headers=headers, timeout=60, **kwargs)
    return resp


def main():
    global TOKEN
    ts = int(time.time())
    email = f"live_{ts}@demo.sih"
    uname = f"live_{ts}"

    r = api("POST", "/api/auth/register", json={
        "email": email, "username": uname, "password": "Str0ngPass!x",
        "full_name": f"Live E2E Officer {ts}", "role": "INVESTIGATING_OFFICER",
    })
    print("register:", r.status_code)
    assert r.status_code == 201, r.text

    r = api("POST", "/api/auth/login", json={"email": email, "password": "Str0ngPass!x"})
    print("login:", r.status_code)
    TOKEN = r.json()["access_token"]

    r = api("POST", "/api/cases", json={
        "title": "LIVE E2E - Fresh Blockchain Test",
        "crime_type": "CYBER_FRAUD",
        "police_station": "Live Test Station",
        "status": "OPEN",
        "description": "Automated live end-to-end verification (no old DB records)",
    })
    print("create case:", r.status_code)
    case_id = r.json()["id"]

    doc_bytes = ("LIVE E2E forensic test document %s\nFingerprint and device "
                 "analysis findings." % uuid.uuid4().hex).encode()
    r = api("POST", "/api/documents/upload", files={
        "file": ("live_e2e_evidence.txt", doc_bytes, "text/plain"),
    }, data={"case_id": case_id, "document_type": "EVIDENCE_RECORD",
             "classification": "RESTRICTED", "description": "live e2e"})
    print("upload doc:", r.status_code)
    assert r.status_code == 201, r.text
    doc = r.json()
    doc_id = doc["id"]
    print("  document_id:", doc_id)
    print("  current_hash:", doc["current_hash"])

    # Wait for background blockchain anchoring (best-effort thread) to finish.
    for _ in range(30):
        r = api("GET", f"/api/blockchain/{doc_id}/status")
        st = r.json()
        if st.get("status") == "CONFIRMED":
            break
        time.sleep(1)
    print("blockchain status:", st.get("status"))
    tx = st.get("transaction_hash")
    block = st.get("block_number")
    anchored = st.get("anchored_at")
    print("  tx:", tx)
    print("  block:", block)
    print("  anchored_at:", anchored)

    # Live verify: the real backend compares file hash vs DB hash vs on-chain hash.
    r = api("GET", f"/api/blockchain/{doc_id}/verify")
    print("verify status:", r.status_code)
    v = r.json()
    print("  verify.status:", v.get("status"))
    print("  file_hash:", v.get("file_hash"))
    print("  stored_hash:", v.get("stored_hash"))
    print("  blockchain_hash:", v.get("blockchain_hash"))
    print("  verified_at:", v.get("verified_at"))
    match_ok = (v.get("status") == "VERIFIED"
                and v.get("file_hash") == v.get("stored_hash")
                and v.get("stored_hash") == v.get("blockchain_hash"))
    print("  HASHES MATCH:", match_ok)
    assert match_ok

    # SHA-256 integrity check (DB layer).
    r = api("GET", f"/api/documents/{doc_id}/integrity")
    print("integrity:", r.status_code, r.json().get("status"))

    # TAMPER -> detect -> restore.
    r = api("POST", f"/api/demo/{doc_id}/tamper")
    print("tamper:", r.status_code)
    r = api("GET", f"/api/documents/{doc_id}/integrity")
    ti = r.json()
    print("integrity after tamper:", ti.get("status"))
    assert ti.get("status") == "INTEGRITY_FAILURE"
    r = api("GET", f"/api/blockchain/{doc_id}/verify")
    tv = r.json()
    print("blockchain verify after tamper:", tv.get("status"))
    r = api("POST", f"/api/demo/{doc_id}/restore")
    print("restore:", r.status_code)
    r = api("GET", f"/api/documents/{doc_id}/integrity")
    ri = r.json()
    print("integrity after restore:", ri.get("status"))
    assert ri.get("status") == "VERIFIED"

    print("\n=== LIVE E2E RESULT: ALL PASSED ===")
    print({
        "case": case_id, "doc": doc_id, "doc_sha256": doc["current_hash"],
        "blockchain_status": st.get("status"), "tx": tx, "block": block,
        "verified": v.get("status"), "tampered_detected": ti.get("status"),
        "restored": ri.get("status"),
    })


if __name__ == "__main__":
    main()
