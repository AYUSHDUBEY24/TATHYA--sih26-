# SIH26190 — Secure Case, Evidence & Legal Document Management System

Smart India Hackathon 2026 prototype (PS ID: **SIH26190**, NCRB / Ministry of Home Affairs).

A case-centric platform for legal/investigation documents: secure storage, versioning,
SHA-256 integrity verification, blockchain hash anchoring, audit trails, search and a
permission-aware AI assistant. **Phase 1 (Foundation) is implemented.**

## Project Structure

```
/frontend    Next.js (App Router) + TypeScript + Tailwind CSS
/backend     FastAPI + SQLAlchemy 2.x + Pydantic v2 (Python 3.11+)
/blockchain  Hardhat skeleton (Solidity contract arrives in Phase 7)
/docs        Requirements, architecture, database, security, implementation plan
/docker      docker-compose.yml — PostgreSQL 16 (pgvector) + MinIO
```

## Prerequisites

* **Docker Desktop** (for PostgreSQL + MinIO)
* **Python 3.11+**
* **Node.js 18+** (tested on Node 24)

## 1. Environment Variables

```bash
# from the repository root
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
```

Never commit the real `.env` — only `.env.example` is versioned.

## 2. Start Infrastructure (PostgreSQL + MinIO)

```bash
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

* PostgreSQL → `localhost:5432` (user `sih`, db `sih26190`, values from `.env`)
* MinIO S3 API → `http://localhost:9000`, Web console → `http://localhost:9001`
* To enable the pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
  (run once inside the database; the image already ships with pgvector)

## 3. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt     # Windows
# .venv/bin/pip install -r requirements.txt       # macOS/Linux
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

* API root → `http://localhost:8000`
* Health check → `http://localhost:8000/health` (also reports database reachability)
* Swagger docs → `http://localhost:8000/docs`

## 4. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:3000
```

## 5. Blockchain (Hardhat skeleton)

```bash
cd blockchain
npm install
npm run compile    # verifies the toolchain (no contracts yet)
npx hardhat node   # local Ethereum node (needed from Phase 7)
```

## Verification Checklist (Phase 1)

- [x] `docker compose up` starts PostgreSQL 16 (pgvector) and MinIO
- [x] PostgreSQL reachable on `localhost:5432`
- [x] MinIO reachable on `localhost:9000` / console `:9001`
- [x] Backend starts; `GET /health` returns `{"status": "ok", ...}`
- [x] Frontend renders the landing page at `http://localhost:3000`
- [x] Hardhat installs and compiles runs cleanly

## Phase 2 — Authentication + RBAC

Implemented: `users`/`roles`/`departments` models (UUID PKs), the five seeded
roles, bcrypt password hashing, JWT auth and the endpoints
`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`,
`POST /api/auth/logout` plus the ADMIN-only `GET /api/users`
(backend-enforced RBAC reference endpoint).

### Run backend tests

```bash
cd backend
.venv\Scripts\pip install -r requirements-dev.txt      # Windows
.venv\Scripts\python -m pytest tests -v
```

Tests use an in-memory SQLite database — Docker/PostgreSQL is not required.

### Seed data

The five roles (ADMIN, INVESTIGATING_OFFICER, SUPERVISOR, FORENSIC_OFFICER,
PROSECUTOR) and demo departments are seeded automatically at backend startup.
To seed manually:

```bash
cd backend
.venv\Scripts\python -m app.seed
```

### Quick local run without Docker (optional)

```bash
# use SQLite instead of PostgreSQL for a quick demo
set DATABASE_URL=sqlite:///./sih_dev.db        # Windows cmd
$env:DATABASE_URL="sqlite:///./sih_dev.db"     # PowerShell
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### Frontend login flow

1. Open `http://localhost:3000` → "Go to login"
2. Register (choose a role — prototype demo behaviour) or sign in
3. The home page shows your name, email and role; "Log out" clears the session

> JWTs are stateless: logout simply discards the token client-side.
> Registration role selection exists for the RBAC demo; a real deployment
> would restrict role assignment to ADMIN.

## Phase 3 — Case Management

Implemented: `cases` and `case_members` models (UUID PKs), documented case
statuses, auto-generated case numbers (`CASE-<year>-<seq>`), and backend-enforced
case authorization.

### Authorization rules (all enforced server-side)

* **Visibility:** ADMIN sees all cases; everyone else sees only cases where they
  are a member or the assigned IO. Unauthorized case IDs return **404** (no
  existence leak).
* **Create:** ADMIN and INVESTIGATING_OFFICER. Creator auto-becomes a member;
  an assigned IO is synced into `cases` and `case_members`.
* **Edit / manage members:** ADMIN, case creator, or assigned IO.
* **Delete:** ADMIN only.
* Frontend pages (`/cases`, `/cases/new`, `/cases/[id]`) reflect these rules
  but never enforce them.

### Run all backend tests

```bash
cd backend
.venv\Scripts\python -m pytest tests -v     # Phase 2 (auth) + Phase 3 (cases)
```

### Frontend pages

* `/cases` — case list (number, title, crime type, status, assigned IO, updated)
* `/cases/new` — create case (ADMIN/IO; IO assignment dropdown)
* `/cases/[id]` — details, members, edit, add/remove members (email-based)

## Phase 4 — Secure Document Management

Implemented: `documents` model, MinIO-backed storage (modular `StorageService`
with dependency injection), secure upload/download with server-side file
validation, and case-scoped document authorization.

### File security safeguards

* Max upload size **50 MB** (`MAX_UPLOAD_SIZE_MB`, enforced while reading)
* **MIME whitelist** (PDF, PNG/JPEG images, plain text/CSV, Word/Excel) —
  enforced server-side, filename extensions are never trusted
* **Magic-byte signature check** — declared type must match the file's leading
  bytes (a `.pdf` containing non-PDF bytes is rejected with 415)
* Filenames sanitised (no path separators/traversal, safe characters only);
  object keys are backend-generated: `case/{case_id}/doc-{document_id}/{name}`
* Files live in a **private MinIO bucket**; downloads are proxied through the
  authenticated backend — no public URLs or object keys are ever exposed
* Delete is a **soft delete** (`status=DELETED`) — history preserved for later
  phases (versioning, integrity)

### Authorization rules (backend-enforced, reuse Phase 2/3 helpers)

* Upload / view / download: any user authorized on the document's **case**
  (ADMIN, case member, assigned IO); unauthorized case/document IDs → 404
* Delete: ADMIN, case manager (creator/assigned IO), or the original uploader
* `STORAGE_BACKEND=memory` exists ONLY for tests/local demos without Docker —
  production and normal development use MinIO (`docker compose up`)

### Run document tests

```bash
cd backend
.venv\Scripts\python -m pytest tests -v     # Phases 2–4, no Docker required
```

### Quick demo without Docker (optional)

```powershell
$env:DATABASE_URL="sqlite:///./sih_dev.db"
$env:STORAGE_BACKEND="memory"
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

> Live MinIO verification requires Docker: `docker compose -f
> docker/docker-compose.yml --env-file .env up -d`, then leave
> `STORAGE_BACKEND=minio` (default).

## Phase 5 — Document Versioning + SHA-256 Integrity

Implemented: immutable version history (`document_versions`), SHA-256 hashing
of every version's exact stored bytes, and integrity verification.

### Versioning behavior

* Initial upload creates **v1**; `POST /api/documents/{id}/versions` creates
  v2, v3, … — numbers increment per document (DB-unique)
* Every version gets its own immutable object key:
  `case/{case_id}/doc-{document_id}/v{n}/{name}` — historical objects are
  **never overwritten or deleted**
* `documents.current_version_id / current_version_number / current_hash`
  follow the latest version (nullable — backward compatible with Phase 4 rows)
* Version history, single-version metadata and **per-version download** are
  available to authorized users only (authorization flows through the parent
  document's case)
* Soft-delete (Phase 4) unchanged: deleted documents disappear from the API
  but their version rows/objects remain as a historical record

### Integrity verification

`GET /api/documents/{id}/integrity` → retrieves the current version's bytes
from storage, recomputes SHA-256, compares with the stored hash:

```json
{"status": "VERIFIED", "document_id": "...", "version": 2,
 "stored_hash": "...", "current_hash": "...", "verified_at": "..."}
```

Mismatch → `"INTEGRITY_FAILURE"` (no `verified_at`, **no auto-repair**, file
contents never exposed). Storage unavailable → clear 502, no metadata changes.

The frontend case page shows current version, current hash, a
**Verify integrity** action (✅ VERIFIED / 🚨 INTEGRITY FAILURE with both
hashes), full version history with per-version download, and an
**Upload new version** form with change notes.

## Phase 6 — Audit Trail + Access Control Deepening

Implemented: centralized audit service + `audit_logs` table, end-to-end audit
integration, ADMIN-only audit API/UI, and a review of the authorization model.

### Audit service

All entries go through `audit_service.log_audit(...)`:

* **Actions:** LOGIN, LOGIN_FAILED, LOGOUT, CASE_CREATED/UPDATED/DELETED,
  CASE_MEMBER_ADDED/REMOVED, DOCUMENT_UPLOADED/VIEWED/DOWNLOADED/DELETED,
  DOCUMENT_VERSION_CREATED, INTEGRITY_VERIFIED/FAILED, PERMISSION_CHANGED
  (reserved), ACCESS_DENIED
* **Results:** SUCCESS / FAILURE / DENIED
* **Never logs** passwords, JWT secrets, or file contents
* SUCCESS entries join the operation's transaction (atomic, via SAVEPOINT);
  FAILURE/DENIED entries commit themselves; an audit write failure is logged as
  a warning and never breaks the main operation
* Access-denials (404 no-existence-leak path) also record a safe `ACCESS_DENIED`
  entry with ids only

### Audit API & UI

* `GET /api/audit` — **ADMIN only**, read-only, append-oriented; filters:
  `action`, `actor_id`, `case_id`, `entity_id`, `result`, date range, `limit`
* No update/delete audit endpoints exist (the trail is immutable via the app)
* Frontend: `/audit` (admin link on the home page) with a filterable table
  showing timestamp, actor, action, entity, case, result, IP and metadata
* Non-admins get 403 on `/api/audit` (verified in tests and manually)

### Access-control review (no rewrite)

The existing model already implements exactly the documented layers:

* **RBAC** — role capability matrix (`deps.py`)
* **Case membership** — `case_members` + assigned-IO (+ ADMIN all-access)
* **Document/version access** — derived from the parent case; direct ID
  changing cannot bypass (404, no existence leak)
* **Frontend visibility is never a security control** — all checks are
  backend-enforced; UI tooltips only hide buttons

Per the docs, document-level permissions/sharing (`document_permissions`,
`document_shares`, and the `PERMISSION_CHANGED` action) are reserved rather
than duplicated — the current RBAC + case-membership model remains the
enforcement layer for this prototype.

## Documentation

See `docs/requirements.md`, `docs/architecture.md`, `docs/database.md`,
`docs/security.md` and `docs/implementation-plan.md` for the full design and
the phased roadmap (authentication is Phase 2 — do not skip phases).
