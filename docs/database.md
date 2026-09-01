# Database Design — SIH26190 Prototype

PostgreSQL with the **pgvector** extension. Keep the schema minimal but sufficient — no speculative tables.

## Entity Overview

```
roles ─┐
departments ─┤
             users ── case_members ── cases
                          │              │
                     (user↔case)         ├── documents ── document_versions
                                         │        │           (file ref, SHA-256)
                                         │        ├── document_permissions
                                         │        ├── document_shares
                                         │        ├── document_text / document_chunks (pgvector)
                                         ├── evidence_assets ── asset_transfers
                                         └── audit_logs (case-scoped events)
security_events   (auth/security events)
blockchain anchor info lives on document_versions / documents (tx hash, status)
```

## Core Tables

### users
id, username, email, password_hash, full_name, role_id (FK roles), department_id (FK departments), is_active, created_at, updated_at.

### roles
id, name (ADMIN, INVESTIGATING_OFFICER, SUPERVISOR/SENIOR_OFFICER, FORENSIC_OFFICER, PROSECUTOR/LEGAL_OFFICER), description.

### departments
id, name, code.

### cases
id, case_number (e.g., CASE-2026-001), title, description, crime_category, police_station/department, status (OPEN, UNDER_INVESTIGATION, UNDER_REVIEW, CHARGESHEET_FILED, COURT_STAGE, CLOSED, ARCHIVED), created_by (FK users), assigned_io (FK users), created_at, updated_at.

### case_members
id, case_id, user_id, role_in_case, added_by, added_at. *(User ↔ Case membership — primary visibility control.)*

### documents
id, case_id, file_name, document_type (FIR, INVESTIGATION_REPORT, WITNESS_STATEMENT, EVIDENCE_RECORD, FORENSIC_REPORT, CHARGE_SHEET, COURT_FILING, LEGAL_NOTICE, JUDGMENT, OTHER), classification, description, uploaded_by, current_version, current_hash (denormalized for fast checks), storage_path/object_key, status, created_at, updated_at.

### document_versions
id, document_id, version_number, file_ref (MinIO key), sha256_hash, uploaded_by, uploaded_at, change_note, blockchain_tx_hash (nullable), blockchain_status (PENDING / ANCHORED / UNAVAILABLE). *Old versions are immutable, read-only history — never destructively replaced.*

### document_permissions
id, document_id, user_id or role_id, permission (VIEW/DOWNLOAD/SHARE), granted_by, granted_at. *(Document-level restrictions on top of case membership — e.g., forensic officer sees forensic docs only.)*

### document_shares
id, document_id, shared_with_user_id, shared_by, permission, shared_at, expires_at (optional).

### evidence_assets
id, evidence_code (EV-001), case_id, type, description, status (REGISTERED, SECURE_STORAGE, ASSIGNED, UNDER_EXAMINATION, ARCHIVED, …), current_holder (FK users), related_document_id (optional), created_at, updated_at.

### asset_transfers
id, evidence_asset_id, from_user, to_user, action, timestamp, related_document_hash, notes. *(Chain-of-custody style history.)*

### document_text
id, document_id, version_id, extracted_text, extraction_method (PYMUPDF / OCR), page_count, created_at.

### document_chunks
id, document_id, version_id, chunk_index, chunk_text, page_number, embedding VECTOR(…) via pgvector. *(RAG retrieval — always filtered by authorization first.)*

### audit_logs
id, actor_user_id, action (see enum below), entity_type, entity_id, case_id (nullable), timestamp, ip_address, result/status, metadata (JSONB). *Append-only style; no updates/deletes in app code.*

### security_events
id, user_id, event_type (LOGIN, LOGIN_FAILED, LOGOUT, PERMISSION_CHANGED, ROLE_CHANGED, …), timestamp, ip, details.

## Audit Action Enum (initial)

LOGIN, LOGIN_FAILED, LOGOUT, CASE_CREATED, CASE_UPDATED, DOCUMENT_UPLOADED, DOCUMENT_VIEWED, DOCUMENT_DOWNLOADED, DOCUMENT_VERSION_CREATED, DOCUMENT_SHARED, PERMISSION_CHANGED, DOCUMENT_DELETED_REQUESTED, DOCUMENT_RESTORED, INTEGRITY_VERIFIED, INTEGRITY_FAILED, AI_QUERY, USER_CREATED, ROLE_CHANGED.

## Key Relationships

* User → Role, User → Department
* Case ↔ many Users (case_members); Case → many Documents; Case → many Evidence Assets
* Document → many Versions; Document → audit events; Document → text/chunks
* Evidence Asset → many Transfers
* Document version → blockchain anchor (tx hash + status)

## Indexing / Search Notes

* B-tree indexes: case_number, cases.status, documents.case_id, documents.document_type, audit_logs.timestamp/action, audit_logs.case_id.
* PostgreSQL full-text search (tsvector) on document_text / document metadata for content search.
* pgvector index (e.g., ivfflat/hnsw) on document_chunks.embedding once populated.

## Blockchain Anchor Placement

Anchor data (tx hash, timestamp, status) is stored alongside the document/version in PostgreSQL for fast status UI, with the **authoritative hash proof in the smart contract**. Verification: recompute SHA-256 of current file → compare with DB hash AND blockchain-registered hash.

## Seeding (demo)

Seed roles, departments, demo users per role, 3+ synthetic cases (CASE-2026-001/002/003), and fictional documents so RBAC restrictions are demonstrable. Synthetic data only.
