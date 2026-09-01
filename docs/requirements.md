# Requirements — SIH26190

## Problem Statement

* **PS ID:** SIH26190 — Secure Digital Document Management System for Legal and Investigation Documents
* **Org:** Ministry of Home Affairs → NCRB, Women Safety Division
* **Category:** Software | **Theme:** Blockchain & Cybersecurity

Pain points addressed: slow document retrieval, unauthorized access, tampering risk, no version control, poor cross-department collaboration, weak auditability.

Official system requirements:

1. Digitize and centralize document storage
2. Ensure secure access and confidentiality
3. Prevent unauthorized modifications
4. Maintain a complete audit trail
5. Efficient document search and retrieval
6. Collaboration among authorized stakeholders
7. Compliance-supporting workflows

> "Police assets" in the expected-solution sentence is interpreted as **case-related digital assets/evidence/documents lifecycle** (the statement body is about legal/investigation documents).

## Document / Evidence Types in Scope

FIR, Investigation Report, Witness Statement, Evidence Record, Forensic Report, Charge Sheet, Court Filing, Legal Notice, Judgment, Other.

## Users / Roles (Prototype)

| Role | Capabilities |
|---|---|
| **ADMIN** | Users, roles, departments, all cases, audit logs, system config, security alerts |
| **INVESTIGATING_OFFICER (IO)** | Assigned cases only; create/update case records; upload documents; create versions; download permitted docs; search authorized docs; AI queries over authorized data |
| **SUPERVISOR / SENIOR_OFFICER** | Department/assigned cases; review documents & activity; audit trail; reports; workflow approvals |
| **FORENSIC_OFFICER** | Authorized evidence/forensic cases; upload forensic reports; view evidence; update permitted forensic versions |
| **PROSECUTOR / LEGAL_OFFICER** | Authorized legal/court documents; upload legal documents; review charge sheets/filings; search; AI over authorized data |

All authorization is **backend-enforced** (RBAC + case-level + document-level checks). Frontend hiding of buttons is never a security control.

## Functional Requirements (MVP)

1. **Authentication** — login, JWT sessions, logout, failed-login audit.
2. **RBAC + case/document permissions** — role determines capability; case membership determines visibility; document classification adds restrictions.
3. **Case management** — create/list/view cases; status lifecycle: OPEN → UNDER_INVESTIGATION → UNDER_REVIEW → CHARGESHEET_FILED → COURT_STAGE → CLOSED → ARCHIVED; assigned IO; stakeholders; case page with overview, members, documents, evidence, timeline, activity, alerts.
4. **Secure document management** — upload with type/size validation; store file in MinIO; metadata in PostgreSQL; SHA-256 hash; permission checks on view/download; never expose storage paths.
5. **Version control** — new upload to same document = new version (v1, v2, …); each version keeps file ref, hash, uploader, timestamp, change note; old versions read-only; no destructive overwrite.
6. **Integrity verification** — recompute SHA-256 and compare with stored/anchored hash → ✅ VERIFIED / 🚨 INTEGRITY FAILURE; last-verified time; clear UI presentation; simulate-tamper demo support.
7. **Audit trail** — every security-sensitive action logged (LOGIN, LOGIN_FAILED, CASE_CREATED, DOCUMENT_UPLOADED, DOCUMENT_VIEWED, DOCUMENT_DOWNLOADED, DOCUMENT_VERSION_CREATED, DOCUMENT_SHARED, PERMISSION_CHANGED, INTEGRITY_VERIFIED, INTEGRITY_FAILED, AI_QUERY, USER_CREATED, ROLE_CHANGED, …) with actor, action, entity, case, timestamp, IP, result, metadata; admin audit page with filters.
8. **Evidence/asset lifecycle** — register → secure storage → assign → access → transfer → examine → update documentation → verify integrity → archive; transfers record from/to/timestamp/action (chain-of-custody style history).
9. **Search** — by case number/ID, document name, type, uploader, date, tags/metadata, extracted text (PostgreSQL FTS; no separate search cluster).
10. **OCR (nice-to-have)** — detect scanned PDFs → extract text → store/index; modular; failure must not affect original file access.
11. **AI/RAG assistant** — case/document/evidence summary, natural-language questions, comparison, cross-document lookup; **permission-aware retrieval only**; answers with source citations (doc + page); "not found in authorized documents" instead of hallucination; LLM-unavailable must not break normal search.

## Non-Functional Requirements

* Modular monolith (no microservices), easy local run via Docker Compose.
* Graceful degradation: blockchain unavailable → anchor marked pending; LLM unavailable → search continues; OCR failure → file still accessible.
* Secrets via environment variables only; `.env.example` committed; `.env` never committed.
* Demo reliability over feature count; every claimed feature must be testable.

## Scope Constraints (Explicitly Out of Scope)

Not a production NCRB deployment: no real police/court/NCRB integrations, no legal-compliance certification, no production PKI, no national scale. Compliance is **"compliance-supporting"** (access controls, audit, versioning, integrity, traceability) — no legal certification claims.

## Demo Data Policy

Synthetic fictional data only (e.g., CASE-2026-001/002/003; FIR.pdf, Witness_Statement_01.pdf, Evidence_Report.pdf, Forensic_Report.pdf, Charge_Sheet.pdf, Court_Order.pdf). Seed multiple roles and cases to demonstrate RBAC. Never use real police/criminal data.

## Critical Demo Scenario (must be reliable)

Login as IO → open CASE-2026-001 → upload FIR → MinIO + SHA-256 + PostgreSQL metadata + blockchain anchor + audit event → upload v2 → show v1/v2 → login as other role → show restricted access → search → open document → verify integrity (✅) → simulate tampering → verify (🚨) → ask AI "Summarize this case" → authorized answer with citations → open audit log → full lifecycle shown.
