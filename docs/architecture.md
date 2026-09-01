# Architecture — SIH26190 Prototype

## Style: Modular Monolith

One FastAPI backend, one Next.js frontend, shared infrastructure via Docker Compose. **No microservices.** Optional services (blockchain, OCR, RAG/LLM) must never take down the core DMS.

## Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | Next.js + React + Tailwind CSS | UI pages (login, dashboard, cases, documents, audit, search, evidence, integrity, AI, admin) |
| Backend | FastAPI (Python) | Modular monolith; REST API |
| Database | PostgreSQL (+ pgvector) | Metadata, audit, FTS, vector search |
| Object storage | MinIO | Actual files (PDFs/images) — never on blockchain, never public URLs |
| Auth | JWT | Password hashing (secure hash), token-based sessions |
| Authz | RBAC + case/document permissions | Backend-enforced on every protected operation |
| Doc processing | PyMuPDF (+ modular OCR) | Text extraction for search/RAG |
| Integrity | SHA-256 | Per document version |
| Blockchain | Hardhat + Solidity + local Ethereum | Tamper-evident hash anchor ONLY |
| AI | LLM + embeddings + RAG | Permission-aware retrieval, cited answers |
| Deployment | Docker / Docker Compose | postgres, minio, hardhat node + app services |

## Component Diagram (logical)

```
User (browser)
  ↓ HTTPS
Next.js Frontend (UI only — no security logic trusted)
  ↓ REST + JWT
FastAPI Backend (modular monolith)
  ├── Auth (JWT issue/verify)
  ├── Authorization (RBAC + case/document checks)   ← gatekeeper for EVERYTHING below
  ├── Cases API
  ├── Documents API ──→ MinIO (file bytes)
  │                 └─→ PostgreSQL (metadata, versions, FTS)
  ├── Integrity service (SHA-256 compute/compare)
  ├── Audit service ──→ PostgreSQL audit_logs
  ├── Blockchain service ──→ Hardhat local node (hash anchor only)
  ├── Search service ──→ PostgreSQL FTS
  ├── Evidence/asset service ──→ PostgreSQL (lifecycle + transfers)
  └── RAG service ──→ pgvector (authorized chunks) ──→ LLM (grounded answer + citations)
```

## Core Flow (must be preserved)

Case → Document/Evidence → Secure Storage → Access Control → Version → Hash → Audit → Blockchain → Search → AI/RAG → Integrity Verification → Audit/History.

## Upload Data Flow

1. Receive file → validate type & size
2. Validate user/case permissions
3. Store file in MinIO
4. Compute SHA-256
5. Extract metadata; extract text (OCR if scanned) — non-blocking on failure
6. Create document record + version record in PostgreSQL
7. Create audit event
8. Anchor hash on blockchain (if unavailable → mark pending, continue)
9. Chunk text → embeddings → pgvector (if AI enabled)

## Blockchain Role (strictly limited)

* Stores ONLY: `documentId`, `documentHash`, `timestamp` via one simple Solidity contract (`registerDocumentHash`, `getDocumentHash`).
* **Never** store files, metadata, or confidential content on-chain.
* No tokens, NFTs, mainnets, multi-chain, multiple contracts.
* Verification = `SHA-256(current file) == blockchain hash` (plus stored DB hash).
* If Hardhat node is down: system continues; anchor status = pending/unavailable.

## RAG Architecture (permission-aware only)

```
Question → authenticate → authorize
  → restrict candidate set to documents/chunks the user can access
  → semantic retrieval (pgvector) over THAT set
  → relevant chunks as context → LLM → answer + sources (doc, page)
```

* NEVER: User → LLM → entire database.
* Never retrieve unauthorized documents, even for retrieval scoring.
* Distinguish trusted document content from instructions (prompt-injection aware).
* If not found in authorized docs → say so; never fabricate.
* LLM unavailable → normal search/UI keep working; show "AI unavailable".

## Recommended Folder Structure (adapt, don't over-engineer)

```
/frontend        (Next.js: /app /components /lib /hooks)
/backend
  /app
    /api          (routers)
    /models       (SQLAlchemy)
    /schemas      (Pydantic)
    /services     (business logic)
    /repositories (DB access)
    /auth  /security
    /documents /cases /audit /search /rag /blockchain /storage
/blockchain       (/contracts /scripts /test)
/docs             (these documents)
/docker           (docker-compose.yml)
.env.example  README.md  AGENTS.md
```

## Architectural Principles

1. Security first 2. Case-centric 3. Backend-enforced authorization 4. Immutable-style audit 5. Versioned documents 6. Cryptographic integrity 7. Blockchain = hash anchor only 8. AI over authorized info only 9. Source-grounded answers 10. Modular, not over-engineered 11. Easy local setup 12. Demo reliability first.

## Graceful Degradation

| Failure | Behavior |
|---|---|
| Blockchain down | Doc system works; anchor marked pending |
| LLM down | Search & documents work; AI shows unavailable |
| OCR failure | Original file accessible; searchable text missing |
| Storage failure | Meaningful error; no partial records |

## Deployment (local dev)

`docker compose up` → PostgreSQL + MinIO + Hardhat node. Frontend & backend run locally (or containerized). `git clone → install deps → configure .env → compose up → run app → run demo` — exact commands go in README.
