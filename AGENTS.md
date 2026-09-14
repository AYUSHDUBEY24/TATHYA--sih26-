# SIH26190 — Secure Case, Evidence & Legal Document Management System

## 0. Project Context

We are building a Smart India Hackathon 2026 prototype for:::

* Problem Statement ID: SIH26190
* Title: Secure Digital Document Management System for Legal and Investigation Documents
* Organization: Ministry of Home Affairs
* Department: National Crime Records Bureau (NCRB), Women Safety Division
* Category: Software
* Theme: Blockchain & Cybersecurity

The official problem statement describes a secure, centralized, intelligent digital document management system for sensitive legal and investigation documents such as:

* FIRs and police reports
* Investigation records
* Witness statements
* Charge sheets
* Court filings
* Evidence records
* Forensic reports
* Legal notices
* Judgments

It identifies problems including:

* Difficulty locating documents quickly
* Unauthorized access to confidential information
* Document tampering risks
* Lack of version control
* Inefficient collaboration between departments
* Delays in legal/investigative processes
* Poor auditability and compliance tracking

The official system requirements are:

1. Digitize and centralize document storage
2. Ensure secure access and confidentiality
3. Prevent unauthorized modifications
4. Maintain a complete audit trail of document activities
5. Enable efficient document search and retrieval
6. Support collaboration among authorized stakeholders
7. Ensure compliance with legal and regulatory requirements

The challenge is to preserve legal validity and evidentiary integrity while making the platform secure, scalable, and intelligent.

The official statement also ends with an “Expected Solution” sentence about monitoring and managing police assets throughout their lifecycle. For this prototype, interpret police assets in the context of case-related digital assets/evidence/documents and their lifecycle, because the rest of the official statement is explicitly centered around legal and investigation documents.

---

# 1. Product Vision

Build a secure, case-centric digital platform for managing legal, investigation, and evidence-related digital assets across their lifecycle.

The product should be thought of as:

"Secure Google Drive + Case Management + Git-like document version history + RBAC + Audit Trail + Evidence Integrity Verification + AI Research Assistant"

but specifically designed for legal/investigation workflows.

The final system should make it possible to:

* Create and manage cases
* Register digital documents/evidence against cases
* Securely store documents
* Control access by user role and case assignment
* Maintain versions instead of silently overwriting files
* Detect document tampering
* Maintain detailed audit history
* Search and retrieve documents efficiently
* Share documents only with authorized stakeholders
* Track evidence/document lifecycle
* Use blockchain only as a tamper-evident integrity anchor
* Use AI/RAG to answer questions over authorized documents
* Show citations/sources for AI answers

The system must NOT behave like a generic file-upload website.

---

# 2. Core Design Principle

Everything is CASE-CENTRIC.

Primary relationship:

Case
→ Digital Asset / Document / Evidence
→ Metadata
→ Versions
→ Access permissions
→ Audit trail
→ Integrity information
→ Search index
→ AI/RAG knowledge

Example:

CASE-2026-001
├── FIR.pdf
├── Witness_Statement_01.pdf
├── Witness_Statement_02.pdf
├── Evidence_Report.pdf
├── Forensic_Report.pdf
├── Investigation_Report.pdf
├── Charge_Sheet.pdf
└── Court_Order.pdf

The system should allow an authorized user to understand the complete lifecycle and history of a document/evidence item.

---

# 3. Target Users / Roles

Prototype roles:

## ADMIN

* Manage users
* Manage roles
* Manage departments
* View all cases
* View audit logs
* Manage system configuration
* Manage permissions
* View security alerts

## INVESTIGATING_OFFICER (IO)

* View assigned cases
* Create or update permitted case records
* Upload documents
* Create document versions
* View/download permitted documents
* Search authorized documents
* Ask AI questions about authorized case information
* View relevant document history

## SUPERVISOR / SENIOR_OFFICER

* View assigned/department cases
* Review documents
* Review case activity
* Review audit trail
* Access reports
* Approve/monitor workflows where appropriate

## FORENSIC_OFFICER

* Access authorized evidence/forensic cases
* Upload forensic reports
* View relevant evidence documents
* Update permitted forensic document versions
* Review evidence metadata

## PROSECUTOR / LEGAL_OFFICER

* Access authorized legal/court documents
* View relevant case documents
* Upload legal documents
* Review charge sheets/court filings
* Search authorized information
* Use AI assistant over authorized data

The system must use backend-enforced authorization, not only frontend visibility rules.

---

# 4. Recommended Architecture

Use a modular monolith rather than microservices.

Recommended architecture:

Frontend:

* Next.js
* React
* Tailwind CSS

Backend:

* FastAPI
* Python

Database:

* PostgreSQL

Object/file storage:

* MinIO

Authentication:

* JWT

Authorization:

* RBAC
* Case-level and document-level permission checks

Document processing:

* PyMuPDF
* OCR for scanned documents

Search:

* PostgreSQL metadata/full-text search initially

Vector search:

* pgvector

AI:

* LLM
* Embeddings
* RAG

Integrity:

* SHA-256

Blockchain:

* Hardhat
* Local Ethereum development network
* Solidity smart contract
* Web3 integration from backend

Containerization:

* Docker / Docker Compose

---

# 5. High-Level System Flow

User
→ Next.js frontend
→ FastAPI backend
→ Authentication
→ Authorization/RBAC
→ Case management
→ Document management
→ Storage + metadata
→ Hashing
→ Audit logging
→ Blockchain integrity anchoring
→ Search/OCR
→ AI/RAG

Important separation:

PostgreSQL:

* users
* roles
* departments
* cases
* documents
* document versions
* permissions
* audit logs
* evidence metadata
* AI metadata

MinIO:

* actual files such as PDFs/images/documents

Blockchain:

* only document integrity proof / hash record
* never store actual confidential documents on blockchain

---

# 6. Main Data Flow: Document Upload

When an authorized user uploads a document:

1. Receive file at FastAPI
2. Validate file type and size
3. Validate user/case permissions
4. Generate a unique document ID
5. Store the actual file in MinIO
6. Calculate SHA-256 hash
7. Extract metadata
8. Extract text where possible
9. Run OCR if needed
10. Create document record in PostgreSQL
11. Create version record
12. Create audit log entry
13. Register the hash on the blockchain
14. If AI search is enabled, chunk/extract content and index it

Example:

FIR.pdf
→ MinIO
→ SHA-256 = A8F91C...72D
→ PostgreSQL metadata
→ Blockchain hash registry
→ Audit log
→ Search index

---

# 7. Case Management

A case should contain:

* Case ID
* Case number
* Title
* Description
* Crime/category type
* Police station / department
* Case status
* Created by
* Assigned investigating officer
* Relevant stakeholders
* Created date
* Updated date

Suggested statuses:

* OPEN
* UNDER_INVESTIGATION
* UNDER_REVIEW
* CHARGESHEET_FILED
* COURT_STAGE
* CLOSED
* ARCHIVED

A case page should display:

* Case overview
* Assigned users
* Documents
* Evidence
* Timeline
* Recent activity
* Integrity/security alerts

---

# 8. Document Management

Each document should have:

* Document ID
* Case ID
* File name
* Document type
* Classification
* Description
* Uploaded by
* Uploaded at
* Current version
* Hash
* Storage path/object key
* Status

Document types can include:

* FIR
* Investigation Report
* Witness Statement
* Evidence Record
* Forensic Report
* Charge Sheet
* Court Filing
* Legal Notice
* Judgment
* Other

Do not make the taxonomy unnecessarily complex for the prototype.

---

# 9. Version Control

Never silently overwrite important documents.

Example:

Investigation_Report.pdf

v1
v2
v3

Each version should preserve:

* version number
* file reference
* hash
* uploaded by
* timestamp
* optional change note

Users should be able to view version history.

Old versions should remain available as read-only history where appropriate.

---

# 10. Integrity and Anti-Tampering

Use SHA-256 for the cryptographic fingerprint of every document version.

Example:

FIR.pdf
→ SHA-256
→ ABC123...

Store the hash in PostgreSQL.

Also anchor the hash using the blockchain layer.

Verification flow:

Current file
→ calculate SHA-256
→ compare with trusted stored/anchored hash

If equal:

VERIFIED

If different:

INTEGRITY FAILURE / POSSIBLE TAMPERING

The UI should make this very understandable.

Example:

* ✅ Integrity Verified
* ⚠️ Integrity Mismatch
* Last verified time
* Stored hash
* Current hash

---

# 11. Blockchain — KEEP THIS SIMPLE

Blockchain is an integrity layer, NOT the storage layer.

Do NOT store PDFs on blockchain.

Only store:

* documentId
* documentHash
* timestamp

Use:

* Hardhat
* Local Ethereum development network
* Solidity
* A single simple smart contract

Conceptual smart contract API:

registerDocumentHash(documentId, hash)

getDocumentHash(documentId)

Potential record:

DOC-001
→ A8F91C...72D
→ timestamp

Verification:

Current file
→ SHA-256
→ currentHash

Blockchain
→ storedHash

Compare:

currentHash == storedHash
→ ✅ Verified

currentHash != storedHash
→ 🚨 Integrity Failure

The blockchain implementation must remain small and easy to run locally.

Do not introduce:

* tokens
* NFTs
* public mainnet
* complicated multi-chain logic
* multiple contracts
* complex consensus/network setup

The goal is a credible prototype of tamper-evident hash anchoring.

---

# 12. Audit Trail

Every security-sensitive and document-related action should generate an audit event.

Examples:

* LOGIN
* LOGIN_FAILED
* LOGOUT
* CASE_CREATED
* CASE_UPDATED
* DOCUMENT_UPLOADED
* DOCUMENT_VIEWED
* DOCUMENT_DOWNLOADED
* DOCUMENT_VERSION_CREATED
* DOCUMENT_SHARED
* PERMISSION_CHANGED
* DOCUMENT_DELETED_REQUESTED
* DOCUMENT_RESTORED
* INTEGRITY_VERIFIED
* INTEGRITY_FAILED
* AI_QUERY
* USER_CREATED
* ROLE_CHANGED

Audit fields:

* audit ID
* actor/user
* action
* entity type
* entity ID
* case ID if applicable
* timestamp
* IP if available
* result/status
* metadata/details

Admin should have an Audit Logs page with filters.

---

# 13. Access Control

Security is a first-class feature.

Use:

JWT authentication
+
RBAC
+
case-level permissions
+
document-level permission checks

Example:

IO Rahul:
→ CASE-001 ✅
→ CASE-002 ❌

Forensic officer:
→ CASE-001 forensic documents ✅
→ unrelated legal documents ❌

Prosecutor:
→ authorized court/legal documents ✅

The backend must check authorization on every protected operation.

Do not depend on frontend-hidden buttons for security.

---

# 14. Confidentiality

Prototype security measures:

* Password hashing
* JWT-based authentication
* HTTPS-ready architecture
* RBAC
* Access checks
* Secure file access
* Protected API routes
* Encryption-at-rest-ready design
* Audit logging

For local prototype:

* Use environment variables for secrets
* Never hardcode API keys
* Never commit secret values
* Use `.env.example`

---

# 15. Search

Users should be able to search documents by:

* case number
* case ID
* document name
* document type
* uploader
* date
* tags/metadata
* extracted text

Examples:

"all forensic reports for CASE-001"

"documents uploaded by Rahul"

"witness statements"

"mobile phone"

Start with PostgreSQL search if possible.

Do not overengineer search into a separate search cluster unless required.

---

# 16. OCR

Some legal documents may be scanned PDFs.

Pipeline:

PDF
→ detect text availability
→ if scanned:
→ OCR
→ extract text
→ store extracted text
→ index for search/RAG

Use practical Python libraries and keep OCR modular so it can be replaced later.

---

# 17. AI / RAG

AI is an intelligence layer on top of the secure DMS.

The AI assistant should support:

* Case summary
* Document summary
* Evidence summary
* Search-like natural language questions
* Investigation status questions
* Document comparison
* Finding relevant information across case documents

Example:

User:
"Summarize the current status of CASE-001."

System:

* checks user permissions
* retrieves only authorized documents
* retrieves relevant chunks
* sends relevant context to LLM
* returns answer
* cites source documents/pages where possible

VERY IMPORTANT:

Never implement:

User
→ LLM
→ entire database

Correct flow:

User
→ authentication
→ authorization
→ authorized documents
→ retrieval
→ relevant chunks
→ LLM
→ answer + sources

The RAG layer MUST respect user permissions.

---

# 18. RAG Pipeline

Document
→ text extraction
→ chunking
→ embeddings
→ pgvector
→ retrieval

Question
→ permission-aware filtering
→ semantic retrieval
→ relevant chunks
→ LLM
→ grounded answer
→ citations

For the prototype, pgvector is preferred because it allows vector search within PostgreSQL.

Keep the RAG implementation simple enough to run locally.

---

# 19. Source-Cited AI

Whenever practical, AI responses should provide source references.

Example:

Answer:
"The forensic report indicates that fingerprints were recovered from the submitted object."

Sources:

* Forensic_Report_v2.pdf — page 4
* Evidence_Report.pdf — page 2

The AI must not present unsupported information as fact.

Prefer "Not found in authorized documents" rather than hallucinating.

---

# 20. Evidence / Digital Asset Lifecycle

Treat case-related evidence/digital assets as lifecycle-managed records.

Example:

Evidence ID: EV-001
Type: Mobile Phone
Case: CASE-001
Status: Under Examination
Current Holder: Investigating Officer

Lifecycle:

REGISTER
→ SECURE STORAGE
→ ASSIGN
→ ACCESS
→ TRANSFER/SHARE
→ EXAMINE
→ UPDATE DOCUMENTATION
→ VERIFY INTEGRITY
→ ARCHIVE

For evidence transfers, maintain:

* from
* to
* timestamp
* action
* asset/evidence ID
* related document hash if applicable
* audit record

This provides a chain-of-custody style history for the prototype.

---

# 21. UI Pages

Minimum pages:

1. Login
2. Dashboard
3. Cases list
4. Case details
5. Create case
6. Document upload
7. Document details/viewer
8. Version history
9. Audit logs
10. Search
11. Evidence/asset lifecycle
12. Integrity verification
13. AI assistant
14. Admin/user management

Optional:

* Security alerts
* Analytics
* Notifications

---

# 22. Dashboard

Dashboard should show:

* Active cases
* Total documents
* Pending reviews
* Evidence count
* Recent activity
* Integrity alerts
* Recent document uploads

Example widgets:

Active Cases: 12
Documents: 186
Evidence Items: 23
Integrity Alerts: 2

Recent activity:

* FIR uploaded
* Forensic report added
* Version 2 created
* Document viewed
* Integrity verification completed

---

# 23. Recommended Database Entities

Core tables:

users
roles
departments
cases
case_members
documents
document_versions
document_permissions
evidence_assets
asset_transfers
audit_logs
document_shares
document_text
document_chunks
security_events

Do not create excessive tables unless they provide real value.

---

# 24. Suggested Relationships

User
→ Role

User
→ Department

Case
→ many Users

Case
→ many Documents

Case
→ many Evidence Assets

Document
→ many Versions

Document
→ many Audit Events

Evidence Asset
→ many Transfers

Document
→ extracted text/chunks

Document
→ blockchain hash anchor

---

# 25. Recommended Folder Structure

Use a clean monorepo/modular structure.

Example:

/frontend
/app
/components
/lib
/hooks

/backend
/app
/api
/models
/schemas
/services
/repositories
/auth
/security
/documents
/cases
/audit
/search
/rag
/blockchain
/storage

/blockchain
/contracts
/scripts
/test

/docs
architecture.md
api.md
database.md
security.md

/docker
docker-compose.yml

.env.example
README.md
AGENTS.md

Adapt the structure to project conventions rather than creating unnecessary complexity.

---

# 26. Development Strategy

DO NOT build the entire project in one huge step.

Build incrementally.

## Phase 1 — Foundation

* repository setup
* Next.js frontend
* FastAPI backend
* PostgreSQL
* Docker Compose
* basic project configuration

## Phase 2 — Authentication

* login
* password hashing
* JWT
* user model
* role model
* protected routes

## Phase 3 — Case Management

* create case
* list cases
* case details
* assignment
* case status

## Phase 4 — Secure Document Management

* upload
* metadata
* MinIO
* download/view
* file validation
* permission checks

## Phase 5 — Versioning + Integrity

* document versions
* SHA-256
* integrity verification
* version history

## Phase 6 — Audit + Access Control

* audit events
* audit UI
* case-level permissions
* document permissions

## Phase 7 — Blockchain

* Hardhat
* Solidity contract
* register document hash
* retrieve hash
* verification flow
* blockchain status in UI

## Phase 8 — Search + OCR

* metadata search
* text extraction
* OCR
* full-text search

## Phase 9 — RAG

* text chunking
* embeddings
* pgvector
* permission-aware retrieval
* LLM answering
* source citations

## Phase 10 — Demo & Polish

* better dashboard
* timeline
* security alerts
* clean UX
* seed/demo data
* automated tests
* error handling
* documentation

Always make each phase runnable before continuing.

---

# 27. MVP Priority

Must-have:

1. Authentication
2. RBAC
3. Case management
4. Secure document upload/storage
5. Document metadata
6. Version control
7. SHA-256 integrity verification
8. Audit trail
9. Blockchain hash anchoring
10. Search
11. Basic AI/RAG
12. Evidence/digital asset lifecycle

Nice-to-have:

* OCR
* MFA
* advanced analytics
* richer collaboration
* security alerts
* notifications

Avoid feature creep.

---

# 28. Synthetic Demo Data

Do NOT use real police/criminal sensitive data.

Use synthetic fictional data.

Example cases:

CASE-2026-001
CASE-2026-002
CASE-2026-003

Example documents:

FIR.pdf
Witness_Statement_01.pdf
Witness_Statement_02.pdf
Evidence_Report.pdf
Forensic_Report.pdf
Investigation_Report.pdf
Charge_Sheet.pdf
Court_Order.pdf

Create fictional names and data for demo purposes.

Seed the database with multiple roles and cases so role-based access can be demonstrated.

---

# 29. Critical Demo Scenario

The final prototype should support this story:

1. Login as Investigating Officer
2. Open CASE-2026-001
3. Upload FIR
4. System stores file in MinIO
5. System creates SHA-256 hash
6. System stores metadata in PostgreSQL
7. System stores hash anchor on blockchain
8. Audit event is created
9. Upload a second version
10. Show v1 and v2
11. Login as another role
12. Show restricted access
13. Search for a document/content
14. Open document
15. Verify integrity
16. Show "Verified"
17. Simulate tampering
18. Verify again
19. Show "Integrity Failure"
20. Ask AI:
    "Summarize this case"
21. AI answers using authorized documents
22. Show source citations
23. Open audit log
24. Show full document lifecycle

This flow should be reliable and rehearsed.

---

# 30. Integrity Demo

Example:

Original file:
FIR.pdf

Stored hash:
ABC123

Verification:
Current hash = ABC123

Result:
✅ VERIFIED

Then simulate modification.

Modified file:
FIR.pdf

Current hash:
XYZ999

Blockchain hash:
ABC123

Result:
🚨 INTEGRITY FAILURE

This should be easy to demonstrate to judges.

---

# 31. Security Rules for the Codebase

Always:

* validate file types
* validate file sizes
* sanitize inputs
* use parameterized DB queries/ORM
* hash passwords securely
* store secrets in environment variables
* protect API routes
* check user permissions server-side
* avoid exposing internal storage paths
* avoid putting private documents directly into public URLs
* log security-relevant events
* use least-privilege principles
* never log passwords or secret keys
* never commit `.env`
* use safe error messages for users

AI-specific:

* enforce authorization before retrieval
* never retrieve unauthorized documents
* avoid prompt injection shortcuts
* distinguish trusted document content from system instructions
* show sources where possible
* do not fabricate unavailable facts

---

# 32. Important Scope Constraint

This is an SIH prototype, NOT a production NCRB/government deployment.

Do not pretend that the prototype provides:

* production-grade government identity integration
* real NCRB integration
* real police databases
* real court APIs
* full legal compliance certification
* production PKI infrastructure
* national-scale deployment
* guaranteed evidentiary admissibility

Instead, build a technically credible proof of concept that demonstrates the required capabilities.

---

# 33. Compliance Positioning

The system should be described as:

"compliance-supporting"

through:

* access controls
* audit history
* document versioning
* integrity verification
* traceability
* controlled collaboration
* secure storage

Do not claim legal certification.

---

# 34. Architectural Principles

1. Security first
2. Case-centric design
3. Backend-enforced authorization
4. Immutable-style audit history
5. Versioned documents
6. Cryptographic integrity
7. Blockchain only for hash anchoring
8. AI only over authorized information
9. Source-grounded AI answers
10. Modular but not over-engineered
11. Easy local setup
12. Demo reliability over feature count

---

# 35. What OpenCode Must NOT Do

Do NOT:

* generate an enormous microservice architecture
* add technologies without need
* add blockchain complexity without benefit
* put actual files on blockchain
* hardcode API keys
* use real sensitive data
* skip authorization
* make frontend-only security
* replace old versions destructively
* allow AI to access all documents
* build features that cannot be demonstrated
* remove existing working functionality during refactoring
* rewrite the entire application unnecessarily

Prefer simple, working, testable implementations.

---

# 36. How OpenCode Should Work

Before implementing a major phase:

1. Inspect current repository
2. Understand existing structure
3. Identify dependencies
4. Create a concise implementation plan
5. Implement in small increments
6. Run the application
7. Run tests/lint/type checks
8. Fix issues
9. Summarize what changed
10. Explain any assumptions

Do not make large architectural changes without understanding the current codebase.

When uncertain between two implementation options, prefer the simpler reliable option that satisfies the SIH requirement.

---

# 37. Verification Requirements

Every major feature should have verification.

Examples:

Authentication:

* valid login
* invalid login
* protected route

RBAC:

* authorized case access
* unauthorized case denied

Upload:

* valid file
* invalid file type
* oversized file

Versioning:

* v1 created
* v2 created
* previous version preserved

Integrity:

* matching hash
* mismatching hash

Blockchain:

* hash registration
* hash retrieval
* verification

Audit:

* upload creates audit event
* download creates audit event
* permission changes create audit event

RAG:

* authorized documents retrieved
* unauthorized documents excluded
* source citations returned

---

# 38. Error Handling

The system should fail gracefully.

Examples:

Blockchain unavailable:

* document system should continue to function
* mark blockchain anchor as pending/unavailable
* do not lose document metadata

LLM unavailable:

* normal document search should continue
* show AI unavailable status

OCR failure:

* original file remains accessible
* searchable text may be unavailable

Storage failure:

* report meaningful error
* avoid partial records where possible

Do not allow optional services to bring down the entire DMS.

---

# 39. Local Development

Prefer a single Docker Compose workflow for infrastructure.

Potential services:

* PostgreSQL
* MinIO
* Hardhat/local blockchain

Run frontend and backend locally or containerized depending on simplicity.

Goal:

git clone
→ install dependencies
→ configure env
→ docker compose up
→ start app
→ run demo

The README should explain exact commands.

---

# 40. Final Product Architecture

Frontend:
Next.js / React / Tailwind

Backend:
FastAPI / Python

Auth:
JWT

Authorization:
RBAC + case/document permissions

Database:
PostgreSQL

Object Storage:
MinIO

Document processing:
PyMuPDF + OCR

Search:
PostgreSQL FTS

Vector:
pgvector

AI:
LLM + embeddings + RAG

Integrity:
SHA-256

Blockchain:
Hardhat + Solidity + local Ethereum

Audit:
PostgreSQL audit logs

Deployment:
Docker

---

# 41. Final End-to-End Flow

User
↓
Login
↓
JWT authentication
↓
RBAC authorization
↓
Case selection
↓
Document/evidence management
↓
Secure file storage
↓
Metadata storage
↓
SHA-256 hash
↓
Audit event
↓
Blockchain hash anchor
↓
Version history
↓
Search/OCR
↓
Permission-aware RAG
↓
AI answer + sources
↓
Integrity verification
↓
Audit/history

---

# 42. End Goal

The final system should provide a trusted digital lifecycle for legal/investigation documents and case-related evidence.

It should allow an authorized stakeholder to answer:

* What is this document?
* Which case does it belong to?
* Who uploaded it?
* Who accessed it?
* Which version is current?
* What versions existed before?
* Has the document been modified?
* Who is allowed to access it?
* Where can it be found?
* What evidence/documents are associated with this case?
* What happened to the evidence/document over time?
* What information is present in the case?
* Can AI summarize it?
* What are the sources for the AI answer?

The core goal is:

"Secure, searchable, traceable, version-controlled and integrity-verifiable management of legal, investigation and evidence-related digital assets."

---

# 43. Important Instruction for This AI Coding Agent

You are implementing this as an SIH prototype.

Do not optimize for theoretical enterprise complexity.

Optimize for:

* correctness
* security
* understandable architecture
* reliable local execution
* demonstrability
* maintainability
* realistic SIH scope

Always preserve the core flow:

Case
→ Document/Evidence
→ Secure Storage
→ Access Control
→ Version
→ Hash
→ Audit
→ Blockchain
→ Search
→ AI/RAG
→ Integrity Verification

Do not skip security checks to make implementation easier.

Do not claim a feature works unless it has been tested.

When adding a complex technology such as blockchain or RAG, first implement the smallest working version and verify it end-to-end before adding enhancements.
