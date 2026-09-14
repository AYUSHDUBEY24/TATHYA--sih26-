# TATHYA — DEEP CODEBASE ANALYSIS FOR VIVA / INTERVIEW

You have access to the complete TATHYA project repository.

Project:
TATHYA — Where Facts Find Forever

SIH Problem Statement:
SIH26190

IMPORTANT:
This project is ALREADY WORKING.

============================================================
ABSOLUTE RULE — READ ONLY
============================================================

DO NOT MODIFY THIS PROJECT.

Treat the entire repository as READ-ONLY.

DO NOT:
- edit any code
- create files
- delete files
- rename files
- refactor code
- fix bugs
- optimize code
- change UI
- change configuration
- change environment variables
- change database schema
- change database data
- install packages
- update packages
- change Docker configuration
- change blockchain configuration
- change AI configuration

Even if you discover an error, incomplete feature, mock implementation,
failed blockchain transaction, security weakness, or bad practice:

DO NOT FIX IT.

Only explain:
- what the current implementation does
- where it is implemented
- why it behaves that way
- whether it is fully implemented, partially implemented, mocked,
  or currently failing

The purpose is ONLY:

READ → TRACE → UNDERSTAND → EXPLAIN → PREPARE FOR VIVA

============================================================
MY ACTUAL GOAL
============================================================

I am a 3rd-year Computer Science student preparing for:

- SIH project demo
- SIH technical presentation
- project viva
- internship interviews
- placement interviews
- technical cross-questioning

I do NOT want a superficial project overview.

I want to deeply understand how the ENTIRE PROJECT WORKS BEHIND THE UI.

If an interviewer points at ANY button, page, technology, database,
API, blockchain component, AI component, or piece of data, I should
be able to explain:

1. What it is
2. Why we use it
3. How it works
4. What happens internally
5. Where it is implemented in our code
6. What data enters it
7. What data comes out
8. Where the data is stored
9. Which component communicates with it
10. What happens if it fails
11. What security is involved
12. Why we chose this technology instead of alternatives

============================================================
VERY IMPORTANT — ACTUAL IMPLEMENTATION ONLY
============================================================

DO NOT explain what "a typical system" would do.

Explain what THIS repository actually does.

For every technology/feature:

FIRST inspect the code.

THEN explain it.

Never assume something exists because:
- there is a UI button
- there is a folder
- there is a dependency
- the technology is mentioned in README
- the architecture diagram says it exists

Verify how it is actually connected.

If something is:

FULLY IMPLEMENTED
say so.

PARTIALLY IMPLEMENTED
say so.

MOCK/DEMO
say so.

CONFIGURED BUT NOT CONNECTED
say so.

CURRENTLY FAILING
say so.

Do not hide limitations.

============================================================
TEACH ME LIKE A TEACHER
============================================================

I want explanations in SIMPLE language first.

For every difficult concept use this structure:

1. SIMPLE MEANING
2. REAL-WORLD ANALOGY
3. WHY TATHYA NEEDS IT
4. HOW IT WORKS IN TATHYA
5. ACTUAL CODE IMPLEMENTATION
6. DATA FLOW
7. WHAT HAPPENS IF IT FAILS
8. VIVA QUESTIONS
9. SHORT INTERVIEW ANSWER

Do NOT start with complicated terminology.

For example, for hashing:

First:
"Hash is like a digital fingerprint of a file."

Then explain:
- SHA-256
- input
- output
- deterministic nature
- modification detection
- actual implementation
- database storage
- verification

Then give the viva answer.

Use Hinglish where useful, but keep technical terms in English.

============================================================
PART 1 — UNDERSTAND THE COMPLETE SYSTEM FIRST
============================================================

Before explaining individual technologies, inspect the repository and
understand how everything is connected.

Create a mental model of:

USER
 ↓
FRONTEND
 ↓
API
 ↓
BACKEND
 ↓
AUTHENTICATION
 ↓
AUTHORIZATION / RBAC
 ↓
DATABASE
 ↓
FILE STORAGE
 ↓
OCR / AI
 ↓
SEARCH
 ↓
HASHING
 ↓
BLOCKCHAIN
 ↓
AUDIT LOGS

But DO NOT assume every arrow exists.

Replace this with the ACTUAL architecture discovered from code.

Then explain the architecture deeply.

============================================================
PART 2 — FRONTEND DEEP UNDERSTANDING
============================================================

Analyze the actual frontend.

Identify every page.

For example, if present:

- Login
- Dashboard
- Cases
- Case Details
- Documents
- Upload Document
- Search
- AI Assistant
- Audit Logs
- Integrity Verification
- Version History
- Profile
- Admin pages

For EVERY page explain:

A. What the page does
B. Which React component renders it
C. Important child components
D. State management
E. API calls
F. User actions
G. Loading states
H. Error states
I. Response handling
J. How the UI updates

Then trace important actions.

Example:

User clicks Upload
 ↓
React event handler
 ↓
FormData
 ↓
API request
 ↓
Backend endpoint
 ↓
Response
 ↓
React state update
 ↓
UI

Use actual filenames and function names.

============================================================
PART 3 — BACKEND FROM ZERO
============================================================

I especially want to understand the backend.

Explain:

What is a backend?

Why do we need it?

Why shouldn't the React frontend directly access the database?

Then inspect the actual backend.

Explain:

- Framework
- Entry point
- Server startup
- Routes
- Controllers
- Services
- Middleware
- Utilities
- Models
- Database connection
- Authentication
- Authorization
- File handling
- AI services
- Blockchain services
- Audit services

Explain the relationship:

Route
 ↓
Controller
 ↓
Service
 ↓
Database / Storage / External Service
 ↓
Response

But only if this is how the actual project is structured.

============================================================
PART 4 — API DEEP DIVE
============================================================

List the important APIs actually implemented.

For each API explain:

HTTP METHOD:
GET / POST / PUT / PATCH / DELETE

ENDPOINT:

PURPOSE:

REQUEST:

BODY:

PARAMETERS:

AUTHENTICATION:

AUTHORIZATION:

BACKEND FLOW:

DATABASE/STORAGE:

RESPONSE:

ERROR CASES:

FRONTEND USAGE:

ACTUAL FILE:

ACTUAL FUNCTION:

Then explain REST APIs from beginner level.

Explain:

GET
POST
PUT
PATCH
DELETE

using TATHYA examples.

============================================================
PART 5 — AUTHENTICATION
============================================================

Explain authentication from absolute zero.

What is authentication?

What is authorization?

What is the difference?

Then trace actual login.

Example:

User enters email/password
 ↓
React
 ↓
Login API
 ↓
Backend
 ↓
Database lookup
 ↓
Password verification
 ↓
Token/session
 ↓
Frontend
 ↓
Future API requests

But use actual implementation.

Explain:

- Password hashing
- JWT or sessions
- Cookies/localStorage/etc.
- Middleware
- Token validation
- User identity
- Logout
- Expiration
- Unauthorized requests

Find the exact code.

============================================================
PART 6 — RBAC / AUTHORIZATION
============================================================

Explain RBAC from zero.

Why is RBAC needed in TATHYA?

Find actual roles.

Find actual permissions.

Explain:

User
 ↓
Role
 ↓
Permission
 ↓
Resource
 ↓
Allow / Deny

Give real examples.

Example:

Viewer
tries to delete document
 ↓
backend permission check
 ↓
DENIED

Explain where the check happens.

VERY IMPORTANT:

Explain why hiding a button in React is NOT enough security.

Explain backend authorization.

Give likely interviewer questions:

- Why RBAC?
- Authentication vs authorization?
- What happens if user manipulates frontend?
- Can a Viewer call the delete API manually?
- How does backend prevent this?

Answer according to actual code.

============================================================
PART 7 — DATABASE DEEP DIVE
============================================================

Identify the actual database.

Explain:

What database are we using?

Why?

Why not MongoDB?

Why PostgreSQL?

What type of data belongs in PostgreSQL?

Then inspect the actual schema.

Find:

- tables
- models
- columns
- primary keys
- foreign keys
- relationships
- indexes
- constraints
- enums
- timestamps

Explain each important table.

Especially:

Users
Roles
Permissions
Cases
Documents
Document Versions
Audit Logs
AI Queries
Integrity Records
Blockchain Records
etc.

ONLY mention tables that actually exist.

Create a simple conceptual ER diagram.

============================================================
PART 8 — HOW DATA IS ACTUALLY STORED
============================================================

This is extremely important for my interview.

Take a real document and explain exactly what happens.

Example:

FIR.pdf

Explain:

1. Where the actual PDF is stored
2. What metadata is stored
3. Which database table stores metadata
4. How file path/object key is stored
5. How case ID is associated
6. How uploader is associated
7. How version is stored
8. How hash is stored
9. How audit record is stored
10. How integrity information is stored

Clearly distinguish:

ACTUAL FILE

vs

METADATA

vs

HASH

vs

AUDIT RECORD

============================================================
PART 9 — MINIO / OBJECT STORAGE
============================================================

If MinIO is actually used:

Explain MinIO from zero.

What is object storage?

Why do we need object storage?

Why not store PDF directly inside PostgreSQL?

Then explain:

Frontend
 ↓
Backend
 ↓
MinIO
 ↓
Object/Bucket

Explain:

- bucket
- object
- object key
- upload
- download
- delete
- metadata
- access

Find actual MinIO code.

Explain exact flow for uploading a document.

============================================================
PART 10 — DOCUMENT UPLOAD DEEP TRACE
============================================================

This is one of the most important things I need to understand.

Trace ONE document upload completely.

Start from:

User clicks "Upload Document"

Then:

React
 ↓
event handler
 ↓
FormData
 ↓
API
 ↓
Backend route
 ↓
authentication
 ↓
authorization
 ↓
validation
 ↓
file processing
 ↓
storage
 ↓
database
 ↓
hash
 ↓
version
 ↓
audit
 ↓
blockchain if applicable
 ↓
response
 ↓
frontend
 ↓
UI

For every step:

Give actual filename
Give actual function
Explain what happens

============================================================
PART 11 — DOCUMENT VERSIONING
============================================================

Explain versioning from zero.

Why do we need document versions?

Suppose:

FIR v1
 ↓
FIR v2
 ↓
FIR v3

Explain actual implementation.

Tell me:

- How version number is generated
- Where it is stored
- How current version is identified
- How old versions are preserved
- How file storage works for versions
- How hashes differ between versions
- How audit logs track versions
- How the UI displays versions

Trace actual code.

============================================================
PART 12 — SHA-256 HASHING
============================================================

Explain cryptographic hashing from zero.

Then SHA-256.

Explain:

Input
 ↓
SHA-256 algorithm
 ↓
Fixed-length hash
 ↓
Digital fingerprint

Then explain actual TATHYA implementation.

Find:

- hashing library
- hashing function
- file
- input to hash
- output
- storage location
- verification function

Explain whether the hash is generated:

- during upload
- during version creation
- during verification
- elsewhere

Explain:

Original file
 ↓
Hash A

Modified file
 ↓
Hash B

Hash A != Hash B

Explain exactly how this detects modification.

============================================================
PART 13 — WHAT HAPPENS WHEN A FILE IS TAMPERED?
============================================================

I specifically want to understand the COMPLETE tampering flow.

Assume:

Original document:
FIR_v1.pdf

Original hash:
HASH_A

Then someone modifies the file.

Explain:

1. Where could modification occur?
2. What happens to the actual file?
3. When is verification triggered?
4. How is current hash calculated?
5. Where does expected hash come from?
6. How are hashes compared?
7. What happens if they match?
8. What happens if they don't match?
9. What does the backend return?
10. What does the UI show?
11. Is an audit log generated?
12. Is an alert generated?
13. Is blockchain involved?
14. What happens to the modified file?
15. Is it replaced, quarantined, rejected, or simply flagged?

DO NOT ASSUME.

Find the actual behavior in the code.

This section is VERY important for viva.

============================================================
PART 14 — INTEGRITY VERIFICATION
============================================================

Trace the "Verify Integrity" button.

Explain:

UI
 ↓
Frontend handler
 ↓
API
 ↓
Backend
 ↓
Document retrieval
 ↓
Hash calculation
 ↓
Expected hash retrieval
 ↓
Comparison
 ↓
Result
 ↓
Audit
 ↓
UI

Explain actual success and failure responses.

============================================================
PART 15 — BLOCKCHAIN FROM ZERO
============================================================

Explain blockchain as if I have never used it.

First:

What is blockchain?

Why is it useful for document integrity?

Why not simply store everything in PostgreSQL?

Then explain TATHYA's actual blockchain architecture.

Identify:

- Blockchain network
- Hardhat
- Solidity
- Smart contract
- Contract address
- ABI
- Web3 library
- Provider
- Wallet/signer
- Transaction
- Gas
- Block
- Event
- Transaction hash

Only explain components that ACTUALLY exist.

============================================================
PART 16 — SOLIDITY SMART CONTRACT
============================================================

This is VERY important.

Find the actual Solidity contract.

Explain the contract line-by-line conceptually.

I need to know:

1. What is Solidity?
2. Why is Solidity used?
3. What is a smart contract?
4. What does OUR contract store?
5. What functions exist?
6. What parameters do they accept?
7. What do they return?
8. What state variables exist?
9. Are there mappings?
10. Are there events?
11. Who can call the functions?
12. What transaction is created?
13. What gets stored permanently?

Show the important contract code snippets but DO NOT modify them.

Explain in simple language.

For example:

document hash
 ↓
Solidity function
 ↓
transaction
 ↓
blockchain
 ↓
stored integrity record

But verify the actual implementation.

============================================================
PART 17 — HOW BLOCKCHAIN APPEARS IN THE UI
============================================================

This is VERY important.

I want to understand how the blockchain backend becomes visible in the frontend.

Trace:

User uploads document
 ↓
Backend generates hash
 ↓
Blockchain service
 ↓
Smart contract
 ↓
Blockchain transaction
 ↓
Transaction result
 ↓
Database/audit
 ↓
Frontend API
 ↓
UI

Explain exactly where the UI gets:

- anchored status
- transaction hash
- blockchain status
- verification status
- failure status

If the UI says:

"Not anchored"

explain WHY.

If audit logs show:

"BLOCKCHAIN_REGISTRATION_FAILED"

explain the actual failure path.

Do not pretend blockchain works if it currently doesn't.

============================================================
PART 18 — BLOCKCHAIN FAILURE
============================================================

Analyze failure handling.

What happens if:

- Hardhat isn't running?
- RPC connection fails?
- Contract address is wrong?
- Transaction fails?
- Wallet/signing fails?
- Gas fails?
- Blockchain service throws an error?

Explain actual implementation.

Does the document upload fail completely?

Or does the document still get stored while blockchain anchoring fails?

This distinction is extremely important.

============================================================
PART 19 — OCR
============================================================

Explain OCR from zero.

What is OCR?

Why do legal/investigation documents need OCR?

Then inspect actual implementation.

Explain:

Image/PDF
 ↓
OCR
 ↓
Text
 ↓
Storage
 ↓
Search / AI

Find:

- OCR library/service
- function
- file
- trigger
- output
- storage

Explain what happens if OCR fails.

============================================================
PART 20 — SEARCH
============================================================

Explain Search from zero.

Difference between:

Keyword search
vs
Semantic search

Then analyze actual TATHYA search.

Trace:

User query
 ↓
Frontend
 ↓
API
 ↓
Backend
 ↓
Database/search engine
 ↓
Results
 ↓
Frontend

Explain:

- filtering
- sorting
- permissions
- ranking
- pagination if present

Use actual code.

============================================================
PART 21 — EMBEDDINGS
============================================================

If embeddings are actually implemented:

Explain from zero.

What is an embedding?

Why convert text into vectors?

What does a vector represent?

Example:

"car"
and
"automobile"

Then explain actual TATHYA implementation.

Find:

- embedding model
- library/API
- vector dimensions
- where generated
- where stored
- when generated

============================================================
PART 22 — PGVECTOR
============================================================

Explain pgvector from zero.

Why use it?

How does PostgreSQL store vectors?

How is similarity calculated?

Which table/column stores vectors?

What similarity method is used?

Trace actual query:

User query
 ↓
query embedding
 ↓
vector similarity
 ↓
relevant chunks
 ↓
results

Only if actually implemented.

============================================================
PART 23 — RAG
============================================================

Explain RAG from absolute beginner level.

What is an LLM?

What problem does RAG solve?

Why not simply send the question to an LLM?

Explain:

Retrieval
+
Generation

Then inspect actual TATHYA implementation.

Trace:

User question
 ↓
Authentication
 ↓
Permission filtering
 ↓
Document retrieval
 ↓
Chunk retrieval
 ↓
Embedding/vector search
 ↓
Relevant context
 ↓
Prompt
 ↓
LLM
 ↓
Answer
 ↓
Sources/citations
 ↓
Audit log

Do NOT assume every step exists.

Verify every step.

============================================================
PART 24 — AI ASSISTANT COMPLETE TRACE
============================================================

Take ONE real AI question from the UI.

For example:

"List all forensic findings across my authorized cases."

Trace it completely.

I want:

1. React component
2. User input
3. Frontend function
4. API endpoint
5. Request body
6. Backend route
7. Authentication
8. Authorization
9. Search/retrieval
10. Embedding
11. Vector database
12. Retrieved chunks
13. Prompt
14. LLM
15. Response
16. Sources
17. Audit log
18. Frontend rendering

Use actual code locations.

============================================================
PART 25 — AI SECURITY
============================================================

This is a likely interviewer question.

Explain:

How does TATHYA prevent an AI user from getting unauthorized documents?

Trace:

User
 ↓
Role
 ↓
Authorized cases
 ↓
Authorized documents
 ↓
Retrieval
 ↓
AI

Find actual permission filtering.

Also explain:

What happens if someone tries to ask:

"Show me confidential documents from another user's case."

If the protection is incomplete, say so.

============================================================
PART 26 — AI HALLUCINATION
============================================================

Explain:

What is hallucination?

Can our AI hallucinate?

How does RAG reduce hallucination?

What limitations remain?

Does our system provide sources/citations?

Does the system restrict answers to retrieved context?

Use actual implementation.

============================================================
PART 27 — AUDIT LOGS
============================================================

Explain audit logging from zero.

What is an audit log?

Why do legal/investigation systems need it?

Then inspect actual implementation.

Find all real audit event types.

For each important event explain:

- trigger
- actor
- action
- resource
- case
- timestamp
- result
- metadata
- database table

Trace:

User Action
 ↓
Backend
 ↓
Audit Service
 ↓
Database
 ↓
Audit Logs UI

============================================================
PART 28 — SECURITY ARCHITECTURE
============================================================

Explain all security mechanisms actually implemented.

Cover:

- Authentication
- Authorization
- RBAC
- Password handling
- API security
- File validation
- Storage
- Hashing
- Versioning
- Audit logging
- Blockchain
- AI permission filtering

Then explain:

"What can an attacker/user try to do?"

and

"How does current TATHYA handle it?"

Be honest about limitations.

============================================================
PART 29 — ERROR HANDLING
============================================================

Analyze actual error handling.

Explain what happens when:

- login fails
- unauthorized API is called
- file upload fails
- database fails
- MinIO fails
- OCR fails
- AI fails
- vector search fails
- hash verification fails
- blockchain fails

Trace frontend + backend behavior.

============================================================
PART 30 — DOCKER
============================================================

Explain Docker from zero.

What is a container?

Why do we use Docker?

Then inspect:

- Dockerfiles
- docker-compose
- services
- ports
- volumes
- networks
- environment variables

Explain exactly how TATHYA starts.

For every service:

Service
 ↓
Container
 ↓
Port
 ↓
Purpose
 ↓
Dependencies

============================================================
PART 31 — COMPLETE DATA FLOW
============================================================

Give me the complete system data flow.

Start with:

User Login



Case creation/opening
 ↓
Document upload
 ↓
Storage
 ↓
Metadata
 ↓
Hash
 ↓
Version
 ↓
OCR
 ↓
Search/indexing
 ↓
AI/RAG
 ↓
Integrity verification
 ↓
Blockchain
 ↓
Audit log

For every step explain:

Frontend
Backend
Database
Storage
External service
Response

============================================================
PART 32 — TECHNOLOGY-BY-TECHNOLOGY EXPLANATION
============================================================

For EVERY major technology actually used in the repository, create:

Technology:
What is it?
Why do we use it?
What problem does it solve?
How does it work?
How is it used in TATHYA?
Where is it in the code?
What data does it handle?
What happens without it?
Why choose it over an alternative?
Likely interviewer question:
Short answer:

Include actual technologies such as:

React
Backend framework
REST API
PostgreSQL
MinIO
pgvector
OCR
LLM
RAG
Embeddings
SHA-256
Solidity
Smart Contracts
Hardhat
Blockchain
Docker
JWT/session
RBAC

But ONLY if actually present.

============================================================
PART 33 — WHY THIS TECHNOLOGY AND NOT ANOTHER?
============================================================

Prepare comparison questions.

For example:

Why PostgreSQL instead of MongoDB?

Why MinIO instead of storing files in PostgreSQL?

Why pgvector instead of a separate vector database?

Why RAG instead of directly using an LLM?

Why SHA-256?

Why blockchain?

Why Solidity?

Why Hardhat?

Why React?

Why Docker?

For each answer:

Simple reason
Technical reason
TATHYA-specific reason
Interview-ready answer

Do not invent reasons unrelated to actual implementation.

============================================================
PART 34 — SCALABILITY
============================================================

Explain how this architecture could scale.

But first explain the CURRENT architecture.

Then discuss theoretically:

- more users
- more documents
- more cases
- larger files
- more AI queries
- more audit logs
- multiple departments
- multiple servers

Clearly separate:

CURRENT IMPLEMENTATION

from

FUTURE SCALABILITY

============================================================
PART 35 — CURRENT LIMITATIONS
============================================================

Create a brutally honest section:

CURRENT IMPLEMENTATION LIMITATIONS

Find things such as:

- mock data
- demo users
- hardcoded values
- incomplete blockchain
- AI limitations
- OCR limitations
- local-only services
- missing production security
- error handling limitations
- scalability limitations

ONLY mention things actually found.

DO NOT FIX THEM.

Explain how I should answer if an interviewer asks about them.

============================================================
PART 36 — COMPLETE INTERVIEW QUESTION BANK
============================================================

After understanding the codebase, create a question bank.

Categories:

1. Project Basics
2. Problem Statement
3. Architecture
4. Frontend
5. React
6. Backend
7. APIs
8. Database
9. PostgreSQL
10. MinIO
11. Authentication
12. JWT/session
13. RBAC
14. Documents
15. Version Control
16. Hashing
17. SHA-256
18. Integrity Verification
19. Blockchain
20. Solidity
21. Smart Contracts
22. Hardhat
23. OCR
24. Search
25. Embeddings
26. pgvector
27. RAG
28. LLM
29. AI Security
30. Audit Logs
31. Docker
32. Security
33. Scalability
34. Limitations

For each category create:

Question:
Short answer:
Detailed answer:
Actual code/file:
Likely follow-up:
Best interview response:

============================================================
PART 37 — JUDGE CROSS-QUESTIONING
============================================================

Act as a strict SIH judge.

Ask questions like:

"Explain your project in one minute."

"Show me where the backend starts."

"Which API is called when you upload a document?"

"Where is the document actually stored?"

"What is stored in PostgreSQL?"

"Why are you using MinIO?"

"How do you know the document wasn't modified?"

"Show me where hashing happens."

"What happens if the file is modified?"

"Where is the hash stored?"

"Why blockchain?"

"Why not PostgreSQL?"

"Show me your Solidity contract."

"What does your smart contract actually store?"

"How does blockchain status reach the frontend?"

"What happens if blockchain is down?"

"What happens if OCR fails?"

"What happens if AI gives a wrong answer?"

"How do you prevent unauthorized users from querying confidential documents?"

"How does RBAC work?"

"Can someone bypass frontend permissions?"

"How does backend stop them?"

"How are document versions stored?"

"How do you scale this system?"

"What is the weakest part of your current implementation?"

"What part of this project did you actually implement?"

Answer every question according to the actual repository.

============================================================
PART 38 — CODE WALKTHROUGH
============================================================

For the most important workflows, give me a code walkthrough.

Do not dump entire files.

Show only important snippets.

For each snippet:

1. What file?
2. What function?
3. What does this code do?
4. Why is it needed?
5. What calls it?
6. What does it call next?

Especially do this for:

- login
- RBAC
- document upload
- MinIO storage
- database insert
- hashing
- integrity verification
- version creation
- OCR
- search
- embedding
- RAG
- AI query
- blockchain transaction
- Solidity contract
- audit logging

============================================================
PART 39 — FINAL MENTAL MODEL
============================================================

At the end, give me a "TATHYA Mental Model".

I should be able to remember the project using:

WHO
WHAT
WHERE
HOW
WHY

WHO:
Who uses the system?

WHAT:
What does it manage?

WHERE:
Where is each type of data stored?

HOW:
How does data move through the system?

WHY:
Why is each technology used?

Then give me a final architecture diagram.

============================================================
PART 40 — VIVA CRASH REVISION
============================================================

Finally give me:

TATHYA IN 5 MINUTES

TOP 30 THINGS I MUST REMEMBER

TOP 30 MOST LIKELY VIVA QUESTIONS

TOP 30 ONE-LINE ANSWERS

TOP 15 TECHNICAL QUESTIONS

TOP 15 "WHY DID YOU USE THIS?" QUESTIONS

TOP 15 "WHAT IF THIS FAILS?" QUESTIONS

TOP 10 BLOCKCHAIN QUESTIONS

TOP 10 AI/RAG QUESTIONS

TOP 10 DATABASE QUESTIONS

TOP 10 SECURITY QUESTIONS

============================================================
VERY IMPORTANT OUTPUT STYLE
============================================================

DO NOT give me everything in one giant response.

Teach me sequentially.

First inspect the repository completely.

Then start with:

MODULE 1 — COMPLETE SYSTEM ARCHITECTURE

Explain it deeply enough that I understand:

Frontend
Backend
API
Database
Storage
AI
OCR
Search
Hashing
Blockchain
Audit

Then STOP.

I will ask:

"Next module"

and you continue with the next module.

Do not skip technical details.

Do not modify anything.

Do not fix anything.

Do not assume anything.

Always use actual code.

Always mention actual file paths.

Always distinguish actual implementation from theoretical/future functionality.

============================================================
FINAL OBJECTIVE
============================================================

After completing this analysis, I should be able to answer this question confidently:

"Open any page of TATHYA, point to any feature, and explain exactly what happens behind the UI — from the user's click, through React, API, backend, authentication, authorization, database/storage, AI/blockchain processing, and finally back to the UI."

That is the level of understanding I need.

REMEMBER:

THIS IS A WORKING PROJECT.

DO NOT CHANGE ANYTHING.

READ ONLY.

ANALYZE THE EXISTING CODE.

TEACH ME HOW IT WORKS.
