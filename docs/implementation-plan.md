# Implementation Plan — SIH26190 Prototype

Incremental build strategy: **each phase must be runnable and verifiable before the next begins.** No big-bang implementation.

## Phase 1 — Foundation
* Repo scaffold: `/frontend` (Next.js + Tailwind), `/backend` (FastAPI), `/blockchain`, `/docs`, `/docker`
* `docker-compose.yml`: PostgreSQL (+ pgvector), MinIO, Hardhat node
* `.env.example`, README with setup commands
* **Verify:** `docker compose up` starts infra; backend `/health` responds; frontend renders

## Phase 2 — Authentication
* User/Role/Department models; seed users
* Login endpoint, password hashing, JWT issue/verify; protected route dependency; logout
* LOGIN / LOGIN_FAILED / LOGOUT audit events
* **Verify:** valid login ✅, invalid login ❌ (audited), protected route rejects no-token

## Phase 3 — Case Management
* Case model + CRUD (create/list/details/status transitions)
* case_members assignment; case detail page (overview, members, documents, timeline placeholder)
* CASE_CREATED / CASE_UPDATED audit events
* **Verify:** IO sees only assigned cases; supervisor sees department cases; unauthorized case access returns 403

## Phase 4 — Secure Document Management
* Upload flow: validate type/size → permission check → MinIO store → SHA-256 → metadata row → audit event
* View/download via authorized backend streaming (no public URLs); DOCUMENT_VIEWED / DOCUMENT_DOWNLOADED audited
* **Verify:** valid file uploads; invalid type and oversized file rejected; unauthorized download denied

## Phase 5 — Versioning + Integrity
* Upload to existing document creates version v2+ (never overwrite); version history UI
* Integrity verification endpoint: recompute SHA-256 vs stored hash (+ blockchain hash when present) → VERIFIED / INTEGRITY FAILURE; UI shows ✅/🚨, hashes, last-verified time
* **Verify:** v1+v2 created, v1 preserved; matching hash → VERIFIED; tampered file → INTEGRITY FAILURE

## Phase 6 — Audit + Access Control (deepening)
* Audit page with filters (action, user, case, date); document_permissions + document_shares; PERMISSION_CHANGED audited
* **Verify:** upload/download/permission-change each produce audit events; document-level restriction enforced

## Phase 7 — Blockchain
* One simple Solidity contract: `registerDocumentHash(documentId, hash)`, `getDocumentHash(documentId)`; Hardhat deploy script; FastAPI web3 integration
* Anchor on upload; status PENDING/ANCHORED/UNAVAILABLE (graceful if node down)
* **Verify:** hash registered, hash retrieved, verification flow works; node-down does not break uploads

## Phase 8 — Search + OCR
* Text extraction (PyMuPDF); modular OCR for scanned PDFs (failure-tolerant)
* PostgreSQL FTS over extracted text + metadata filters (type, uploader, date, case, tags)
* **Verify:** search by name/type/uploader/content; scanned doc OCR'd; OCR failure leaves file accessible

## Phase 9 — RAG
* Chunk extracted text → embeddings → pgvector
* Permission-aware retrieval (filter chunks to authorized documents BEFORE retrieval) → LLM → grounded answer + citations (doc, page)
* "Not found in authorized documents" fallback; AI_QUERY audit; AI-unavailable status
* **Verify:** authorized documents retrieved; unauthorized documents excluded from answers; citations returned

## Phase 10 — Demo & Polish
* Dashboard widgets (active cases, documents, evidence, integrity alerts, recent activity)
* Evidence lifecycle UI + transfers (chain-of-custody); integrity verification page; security alerts (optional)
* Seed synthetic demo data (CASE-2026-001/002/003, all document types, all roles)
* End-to-end demo rehearsal; error handling; docs finalized
* **Verify:** full Critical Demo Scenario runs reliably start-to-finish

## Demo Data & RBAC Seeding
* Roles: ADMIN, IO, SUPERVISOR, FORENSIC_OFFICER, PROSECUTOR
* Cases: CASE-2026-001 (with FIR, witness statements, evidence, forensic, investigation report, charge sheet, court order), CASE-2026-002, CASE-2026-003
* Multiple roles across cases so restricted access is demonstrable

## Verification Matrix (per phase, from AGENTS.md §37)

| Area | Checks |
|---|---|
| Auth | valid login, invalid login, protected route |
| RBAC | authorized access ✅, unauthorized denied ❌ |
| Upload | valid file, invalid type, oversized |
| Versioning | v1/v2 created, previous preserved |
| Integrity | matching hash ✅, mismatching hash 🚨 |
| Blockchain | register, retrieve, verify |
| Audit | upload/download/permission-change events |
| RAG | authorized retrieved, unauthorized excluded, citations present |

## Definition of Done (prototype)

Core flow works end-to-end and is demonstrable:
Case → Document/Evidence → Secure Storage → Access Control → Version → Hash → Audit → Blockchain → Search → AI/RAG → Integrity Verification → Audit/History.

---

# First Implementation Task

**Phase 1 — Foundation:** create the repository scaffold (Next.js frontend, FastAPI backend, `/blockchain`, `/docker/docker-compose.yml` with PostgreSQL+pgvector, MinIO, Hardhat node; `.env.example`; README with exact local-run commands) and confirm `docker compose up` brings up infrastructure, backend `/health` responds, and the frontend renders. Nothing else until this is verified.
