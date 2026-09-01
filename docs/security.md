# Security Model — SIH26190 Prototype

## Identity & Authentication

* **JWT-based authentication** (login → token; protected routes verify token server-side).
* **Password hashing** with a secure hashing scheme (e.g., bcrypt/argon2) — never plaintext, never logged.
* Login, failed login, logout audited (security_events / audit_logs).
* Secrets (JWT secret, DB creds, MinIO keys, RPC URL) via **environment variables only**; `.env.example` committed; `.env` never committed; no hardcoded keys.
* HTTPS-ready architecture (local dev may use HTTP; design must not block TLS).
* Encryption-at-rest-ready design (storage layer abstraction allows it later).

## Authorization Model (defense in depth)

Three layers, ALL enforced in the **backend** on every protected operation:

1. **RBAC (role-based)** — role determines what capabilities exist (see matrix).
2. **Case-level permissions** — case membership (`case_members`) determines which cases a user can see/act on. IO Rahul → CASE-001 ✅, CASE-002 ❌.
3. **Document-level permissions** — `document_permissions` / classification restrict specific documents within an authorized case (e.g., forensic officer sees forensic/evidence documents but not unrelated legal documents; prosecutor sees authorized court/legal documents).

Frontend UI hiding is a convenience, **never** a security control.

## RBAC Capability Matrix

| Capability | ADMIN | IO | SUPERVISOR | FORENSIC | PROSECUTOR |
|---|---|---|---|---|---|
| Manage users/roles/departments | ✅ | ❌ | ❌ | ❌ | ❌ |
| View all cases / audit logs / config | ✅ | ❌ | dept-scoped | ❌ | ❌ |
| View assigned cases | all | assigned | dept/assigned | authorized | authorized |
| Create/update case records | ✅ | ✅ (assigned) | review/approve | ❌ | ❌ |
| Upload documents | ✅ | ✅ | ❌ (review only) | forensic reports | legal documents |
| Create document versions | ✅ | ✅ (assigned) | ❌ | permitted docs | permitted docs |
| Download/view documents | ✅ | ✅ (authorized) | ✅ (authorized) | authorized evidence/forensic | authorized legal |
| Review documents/activity/audit | ✅ | own actions | ✅ | own | ✅ (authorized) |
| Search authorized documents | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI queries over authorized data | ✅ | ✅ | ✅ | ✅ | ✅ |
| Security alerts | ✅ | ❌ | ❌ | ❌ | ❌ |

## Document Security Rules

* Validate **file types** and **file sizes** on upload.
* Sanitize all inputs; use parameterized queries / ORM (SQLAlchemy) — no string-built SQL.
* Files stored in **MinIO**; served only through authenticated backend streams — never public URLs, never exposed internal storage paths.
* Version history is immutable: new version ≠ overwrite; old versions read-only.
* SHA-256 per version; verification compares current file hash vs stored DB hash vs blockchain-anchored hash → ✅ VERIFIED / 🚨 INTEGRITY FAILURE (with last-verified time and both hashes shown in UI).

## Audit Trail (security-relevant events)

Every sensitive action logs: audit id, actor, action, entity type/id, case id, timestamp, IP (if available), result, metadata JSONB. Actions include LOGIN, LOGIN_FAILED, DOCUMENT_UPLOADED/VIEWED/DOWNLOADED, DOCUMENT_VERSION_CREATED, DOCUMENT_SHARED, PERMISSION_CHANGED, INTEGRITY_VERIFIED/FAILED, AI_QUERY, USER_CREATED, ROLE_CHANGED, CASE_CREATED/UPDATED. Admin gets an Audit Logs page with filters. Append-only (no app-level updates/deletes).

## AI/RAG Security Rules

* **Authorization before retrieval** — candidate chunk set is filtered to documents the requesting user is authorized to access; unauthorized documents are never retrieved, scored, or sent to the LLM.
* No prompt-injection shortcuts: treat retrieved document content as untrusted data, separate from system instructions.
* Answers must be **source-grounded** with citations (document + page); prefer "Not found in authorized documents" over fabrication.
* AI_QUERY actions are audited.
* LLM unavailability must not break document features.

## Backend Enforcement Checklist

* [ ] Every protected API route requires valid JWT
* [ ] Every case-scoped operation checks case membership/role
* [ ] Every document operation checks document permissions/classification
* [ ] Download/view streams files only after authorization, and logs DOCUMENT_VIEWED/DOWNLOADED
* [ ] Permission/role changes audited
* [ ] Safe error messages (no internal paths, stack traces, or secret values leaked)

## Compliance Positioning

The prototype is **"compliance-supporting"** (access controls, audit history, versioning, integrity verification, traceability, controlled collaboration). It does **not** claim legal certification, evidentiary admissibility, production PKI, or real NCRB/court integration.
