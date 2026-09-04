"""
Demo environment seeding (Phase 10A).

Creates a realistic, fully fictional demo environment for SIH demonstration.
Safe to run repeatedly (idempotent). Use reset_demo() to clear first.
Run manually: python -m app.seed_demo
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.demo_docs import (
    ARMS_INVESTIGATION_REPORT,
    ASSAULT_COURT_FILING,
    ASSAULT_INVESTIGATION_REPORT,
    EMBEZZLEMENT_FIR,
    EMBEZZLEMENT_INVESTIGATION_REPORT,
    FRAUD_CHARGE_SHEET,
    FRAUD_FIR,
    FRAUD_FORENSIC_REPORT,
    FRAUD_INVESTIGATION_REPORT,
    FRAUD_WITNESS_STATEMENT_01,
    MISSING_FIR,
    MISSING_INVESTIGATION_REPORT,
    NARCOTICS_FIR,
    NARCOTICS_FORENSIC_REPORT,
    NARCOTICS_INVESTIGATION_REPORT,
    NARCOTICS_WITNESS_STATEMENT_01,
    NARCOTICS_EVIDENCE_RECORD,
    PROPERTY_FIR,
    PROPERTY_INVESTIGATION_REPORT,
    PROPERTY_WITNESS_STATEMENT_01,
)
from app.core.hashing import sha256_hex
from app.core.security import hash_password
from app.db.database import Base, SessionLocal
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.department import Department
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.role import Role
from app.models.user import User
from app.seed import seed_default_data
from app.services.audit_service import AuditAction, log_audit
from app.services.document_processing import process_document_version
from app.storage import StorageService, get_storage

logger = logging.getLogger("sih26190.seed_demo")


class _SeedStorage:
    """
    Wraps the storage backend so a down/unreachable MinIO degrades gracefully.

    The first failed save marks storage unavailable: remaining saves are
    skipped (metadata seeding continues) and reads fail fast, instead of
    paying the MinIO connection timeout for every single document.
    """

    def __init__(self, storage: StorageService) -> None:
        self._storage = storage
        self._available = True

    def save(self, object_key: str, content: bytes, content_type: str) -> None:
        if not self._available:
            return
        try:
            self._storage.save(object_key, content, content_type)
        except Exception as exc:  # noqa: BLE001 — demo seeding must survive MinIO being down
            self._available = False
            logger.warning(
                "Object storage is unavailable (%s). Document metadata will be "
                "seeded, but stored files will be missing until the storage "
                "backend is reachable. Skipping further storage attempts.",
                exc,
            )

    def get(self, object_key: str) -> bytes:
        if not self._available:
            raise RuntimeError("Object storage unavailable during demo seeding")
        return self._storage.get(object_key)

DEMO_PASSWORD = "Demo@2026!"

DEMO_USERS = [
    {"email": "admin@demo.sih", "username": "admin_demo", "full_name": "System Administrator (Demo)", "role": "ADMIN"},
    {"email": "io.reddy@demo.sih", "username": "io_reddy", "full_name": "Insp. Kavita Reddy (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.patil@demo.sih", "username": "supervisor_patil", "full_name": "Insp. Rajesh Patil (Demo)", "role": "SUPERVISOR"},
    {"email": "forensic.kumar@demo.sih", "username": "forensic_kumar", "full_name": "Dr. Suresh Kumar (Demo)", "role": "FORENSIC_OFFICER"},
    {"email": "prosecutor.sharma@demo.sih", "username": "prosecutor_sharma", "full_name": "Adv. Meera Sharma (Demo)", "role": "PROSECUTOR"},
]

DEMO_CASES = [
    {
        "case_number": "CASE-2026-001",
        "title": "Cyber Fraud - Phishing Campaign",
        "description": "Organised phishing operation targeting financial institution customers",
        "crime_type": "CYBER_FRAUD",
        "police_station": "Cyber Crime Division, Bengaluru",
        "status": "CHARGESHEET_FILED",
        "assigned_io_username": "io_reddy",
        "members": [
            {"username": "io_reddy", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "prosecutor_sharma", "role_in_case": "LEGAL_ADVISOR"},
        ],
        "documents": [
            {"filename": "FIR_26_2026.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": FRAUD_FIR, "uploader": "io_reddy"},
            {"filename": "Witness_Statement_Priya_Sharma.txt", "doc_type": "WITNESS_STATEMENT", "classification": "CONFIDENTIAL", "content": FRAUD_WITNESS_STATEMENT_01, "uploader": "io_reddy"},
            {"filename": "Investigation_Report_v1.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": FRAUD_INVESTIGATION_REPORT, "uploader": "io_reddy", "has_v2": True},
            {"filename": "Forensic_Report_FSL.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": FRAUD_FORENSIC_REPORT, "uploader": "forensic_kumar"},
            {"filename": "Charge_Sheet_CC112.txt", "doc_type": "CHARGE_SHEET", "classification": "RESTRICTED", "content": FRAUD_CHARGE_SHEET, "uploader": "prosecutor_sharma"},
        ],
    },
    {
        "case_number": "CASE-2026-002",
        "title": "Property Forgery - Fraudulent Sale Deed",
        "description": "Forged sale deed registered using proxy Aadhaar authentication",
        "crime_type": "FORGERY",
        "police_station": "Civil Lines, Pune",
        "status": "UNDER_REVIEW",
        "assigned_io_username": "supervisor_patil",
        "members": [
            {"username": "supervisor_patil", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "io_reddy", "role_in_case": "ASSISTING_OFFICER"},
        ],
        "documents": [
            {"filename": "FIR_142_2026.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": PROPERTY_FIR, "uploader": "supervisor_patil"},
            {"filename": "Witness_Statement_Kulkarni.txt", "doc_type": "WITNESS_STATEMENT", "classification": "INTERNAL", "content": PROPERTY_WITNESS_STATEMENT_01, "uploader": "supervisor_patil"},
            {"filename": "Investigation_Report_Property.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": PROPERTY_INVESTIGATION_REPORT, "uploader": "supervisor_patil"},
        ],
    },
    {
        "case_number": "CASE-2026-003",
        "title": "Narcotics Trafficking - Heroin Seizure",
        "description": "12.5 kg heroin intercepted at NH-16 checkpoint",
        "crime_type": "NARCOTICS",
        "police_station": "NCB Hyderabad",
        "status": "UNDER_INVESTIGATION",
        "assigned_io_username": "io_reddy",
        "members": [
            {"username": "io_reddy", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
        ],
        "documents": [
            {"filename": "FIR_NCB_08_2026.txt", "doc_type": "FIR", "classification": "CONFIDENTIAL", "content": NARCOTICS_FIR, "uploader": "io_reddy"},
            {"filename": "Witness_Statement_Reddy.txt", "doc_type": "WITNESS_STATEMENT", "classification": "INTERNAL", "content": NARCOTICS_WITNESS_STATEMENT_01, "uploader": "io_reddy"},
            {"filename": "FSL_Narcotics_Report.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": NARCOTICS_FORENSIC_REPORT, "uploader": "forensic_kumar"},
            {"filename": "Investigation_Report_Narcotics.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": NARCOTICS_INVESTIGATION_REPORT, "uploader": "io_reddy"},
            {"filename": "Evidence_Record_Seizure.txt", "doc_type": "EVIDENCE_RECORD", "classification": "CONFIDENTIAL", "content": NARCOTICS_EVIDENCE_RECORD, "uploader": "forensic_kumar"},
        ],
    },
    {
        "case_number": "CASE-2026-004",
        "title": "Financial Embezzlement - Bank Fraud (CLOSED)",
        "description": "Rs. 12.7 crore embezzled from cooperative bank over 4 years",
        "crime_type": "FINANCIAL_FRAUD",
        "police_station": "EOW Delhi",
        "status": "CLOSED",
        "assigned_io_username": "supervisor_patil",
        "members": [
            {"username": "supervisor_patil", "role_in_case": "INVESTIGATING_OFFICER"},
        ],
        "documents": [
            {"filename": "FIR_EOW_206_2026.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": EMBEZZLEMENT_FIR, "uploader": "supervisor_patil"},
            {"filename": "Investigation_Report_Embezzlement.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": EMBEZZLEMENT_INVESTIGATION_REPORT, "uploader": "supervisor_patil"},
        ],
    },
    {
        "case_number": "CASE-2026-005",
        "title": "Assault - Hauz Khas Village (COURT STAGE)",
        "description": "Grievous assault outside restaurant, trial ongoing",
        "crime_type": "ASSAULT",
        "police_station": "Hauz Khas, Delhi",
        "status": "COURT_STAGE",
        "assigned_io_username": "io_reddy",
        "members": [
            {"username": "io_reddy", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "prosecutor_sharma", "role_in_case": "PROSECUTOR"},
        ],
        "documents": [
            {"filename": "Investigation_Report_Assault.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "INTERNAL", "content": ASSAULT_INVESTIGATION_REPORT, "uploader": "io_reddy"},
            {"filename": "Court_Filing_CC112.txt", "doc_type": "COURT_FILING", "classification": "RESTRICTED", "content": ASSAULT_COURT_FILING, "uploader": "prosecutor_sharma"},
        ],
    },
    {
        "case_number": "CASE-2026-006",
        "title": "Missing Person - Harleen Kaur (UNDER INVESTIGATION)",
        "description": "19-year-old student missing, likely elopement",
        "crime_type": "MISSING_PERSON",
        "police_station": "Sultanpur Lodhi, Kapurthala",
        "status": "OPEN",
        "assigned_io_username": "io_reddy",
        "members": [
            {"username": "io_reddy", "role_in_case": "INVESTIGATING_OFFICER"},
        ],
        "documents": [
            {"filename": "FIR_09_2026_Missing.txt", "doc_type": "FIR", "classification": "INTERNAL", "content": MISSING_FIR, "uploader": "io_reddy"},
            {"filename": "Investigation_Report_Missing.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "INTERNAL", "content": MISSING_INVESTIGATION_REPORT, "uploader": "io_reddy"},
        ],
    },
    {
        "case_number": "CASE-2026-007",
        "title": "Arms Trafficking - Country-Made Pistols (ARCHIVED)",
        "description": "Illegal arms manufacturing and distribution network, convicted",
        "crime_type": "ARMS_TRAFFICKING",
        "police_station": "ATS Mumbai",
        "status": "ARCHIVED",
        "assigned_io_username": "supervisor_patil",
        "members": [
            {"username": "supervisor_patil", "role_in_case": "INVESTIGATING_OFFICER"},
        ],
        "documents": [
            {"filename": "Investigation_Report_Arms.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": ARMS_INVESTIGATION_REPORT, "uploader": "supervisor_patil"},
        ],
    },
]


def _get_role(db: Session, role_name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        raise RuntimeError(f"Role {role_name} not found - run seed_default_data first")
    return role


def _get_department(db: Session) -> Department:
    dept = db.scalar(select(Department).limit(1))
    if dept is None:
        dept = Department(name="DEMO_DEPT", description="Demo department")
        db.add(dept)
        db.commit()
        db.refresh(dept)
    return dept


def seed_demo_users(db: Session) -> dict[str, User]:
    """Create demo users. Returns {username: User}."""
    users = {}
    dept = _get_department(db)
    for spec in DEMO_USERS:
        existing = db.scalar(select(User).where(User.username == spec["username"]))
        if existing is not None:
            users[spec["username"]] = existing
            continue
        role = _get_role(db, spec["role"])
        user = User(
            email=spec["email"],
            username=spec["username"],
            full_name=spec["full_name"],
            password_hash=hash_password(DEMO_PASSWORD),
            role_id=role.id,
            department_id=dept.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        users[spec["username"]] = user
        logger.info("Created demo user: %s (%s)", spec["username"], spec["role"])
    return users


def _create_case(db: Session, spec: dict, creator: User, users: dict[str, User]) -> Case:
    """Create a case from spec. Returns the Case."""
    existing = db.scalar(select(Case).where(Case.case_number == spec["case_number"]))
    if existing is not None:
        return existing
    assigned_io = users.get(spec["assigned_io_username"])
    case = Case(
        case_number=spec["case_number"],
        title=spec["title"],
        description=spec["description"],
        crime_type=spec["crime_type"],
        police_station=spec["police_station"],
        status=spec["status"],
        created_by=creator.id,
        assigned_io_id=assigned_io.id if assigned_io else None,
    )
    db.add(case)
    log_audit(
        db,
        AuditAction.CASE_CREATED,
        actor=creator,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        data={"case_number": spec["case_number"], "title": spec["title"]},
    )
    db.commit()
    db.refresh(case)
    return case


def _add_case_members(db: Session, case: Case, spec: dict, users: dict[str, User]) -> None:
    """Add case members from spec."""
    for member_spec in spec.get("members", []):
        user = users.get(member_spec["username"])
        if user is None:
            continue
        existing = db.scalar(
            select(CaseMember).where(CaseMember.case_id == case.id, CaseMember.user_id == user.id)
        )
        if existing is not None:
            continue
        membership = CaseMember(case_id=case.id, user_id=user.id, role_in_case=member_spec["role_in_case"])
        db.add(membership)
        log_audit(
            db,
            AuditAction.CASE_MEMBER_ADDED,
            actor=user,
            entity_type="CASE",
            entity_id=case.id,
            case_id=case.id,
            data={"member_username": user.username, "role_in_case": member_spec["role_in_case"]},
        )
    db.commit()


def _upload_document(
    db: Session, case: Case, doc_spec: dict, uploader: User, storage: StorageService
) -> Document:
    """Upload a document with content, create version, process text."""
    content_bytes = doc_spec["content"].encode("utf-8")
    file_name = doc_spec["filename"]
    doc_type = doc_spec["doc_type"]
    classification = doc_spec["classification"]

    existing = db.scalar(select(Document).where(Document.case_id == case.id, Document.file_name == file_name))
    if existing is not None:
        return existing

    doc = Document(
        case_id=case.id,
        file_name=file_name,
        document_type=doc_type,
        classification=classification,
        description=f"Demo document: {file_name}",
        uploaded_by=uploader.id,
        object_key="",
        content_type="text/plain",
        size_bytes=len(content_bytes),
        status="ACTIVE",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        file_name=file_name,
        object_key="",
        hash=sha256_hex(content_bytes),
        file_size=len(content_bytes),
        mime_type="text/plain",
        uploaded_by=uploader.id,
        change_note="Initial version",
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    version.object_key = f"case/{case.id}/doc-{doc.id}/v1/{file_name}"
    doc.object_key = f"case/{case.id}/doc-{doc.id}/{file_name}"
    db.commit()

    try:
        storage.save(version.object_key, content_bytes, "text/plain")
    except Exception:  # noqa: BLE001 — _SeedStorage already logged the cause
        pass

    doc.current_version_id = version.id
    doc.current_version_number = 1
    doc.current_hash = version.hash
    db.commit()

    # Phase 7: best-effort blockchain anchoring via the existing upload flow.
    from app.api.documents import _anchor_version

    _anchor_version(db, doc, version, actor=uploader)

    log_audit(
        db,
        AuditAction.DOCUMENT_UPLOADED,
        actor=uploader,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        case_id=case.id,
        data={"file_name": file_name, "document_type": doc_type, "version": 1, "size_bytes": len(content_bytes)},
    )
    db.commit()

    process_document_version(db, doc, version, content_bytes, actor=uploader)
    return doc


def _create_v2_version(
    db: Session,
    doc: Document,
    case: Case,
    uploader: User,
    storage: StorageService,
    v1_content: bytes,
) -> None:
    """Create a v2 version of a document with modified content."""
    v1 = db.scalar(
        select(DocumentVersion).where(DocumentVersion.document_id == doc.id, DocumentVersion.version_number == 1)
    )
    if v1 is None:
        return False

    existing_v2 = db.scalar(
        select(DocumentVersion).where(
            DocumentVersion.document_id == doc.id, DocumentVersion.version_number == 2
        )
    )
    if existing_v2 is not None:
        return False  # already seeded - keep idempotent

    # Built from the in-memory demo content, NOT from storage, so versioning
    # works even when the object storage backend is unavailable.
    v2_text = v1_content.decode("utf-8") + "\n\n[UPDATED VERSION - Additional findings appended]\nThis document has been updated with supplementary investigation findings."
    v2_bytes = v2_text.encode("utf-8")

    v2 = DocumentVersion(
        document_id=doc.id,
        version_number=2,
        file_name=doc.file_name,
        object_key=f"case/{case.id}/doc-{doc.id}/v2/{doc.file_name}",
        hash=sha256_hex(v2_bytes),
        file_size=len(v2_bytes),
        mime_type="text/plain",
        uploaded_by=uploader.id,
        change_note="Updated with additional findings",
    )
    db.add(v2)
    db.commit()
    db.refresh(v2)

    storage.save(v2.object_key, v2_bytes, "text/plain")

    doc.current_version_id = v2.id
    doc.current_version_number = 2
    doc.current_hash = v2.hash
    db.commit()

    # Phase 7: best-effort blockchain anchoring via the existing version flow.
    from app.api.documents import _anchor_version

    _anchor_version(db, doc, v2, actor=uploader)

    log_audit(
        db,
        AuditAction.DOCUMENT_VERSION_CREATED,
        actor=uploader,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        case_id=case.id,
        data={"version": 2, "previous_version": 1},
    )
    db.commit()

    process_document_version(db, doc, v2, v2_bytes, actor=uploader)

    return True


def seed_demo(
    db: Session | None = None, storage: StorageService | None = None
) -> dict:
    """
    Seed the full demo environment. Idempotent - safe to run repeatedly.

    storage: optional storage backend override (tests inject InMemoryStorage;
    when omitted the configured STORAGE_BACKEND is used).

    Returns a summary dict with counts of created entities.
    """
    owns_session = db is None
    db = db or SessionLocal()
    if storage is None:
        storage = get_storage()
    storage = _SeedStorage(storage)
    try:
        # Ensure the schema exists: a dev DB created by an earlier phase may
        # be missing newer tables (document_texts, document_chunks, ...).
        Base.metadata.create_all(bind=db.get_bind())
        seed_default_data(db)
        summary = {"users": 0, "cases": 0, "documents": 0, "versions": 0}
        users = seed_demo_users(db)
        summary["users"] = len(users)
        admin_user = users.get("admin_demo")
        if admin_user is None:
            raise RuntimeError("Admin user not found")

        for case_spec in DEMO_CASES:
            case = _create_case(db, case_spec, admin_user, users)
            summary["cases"] += 1
            _add_case_members(db, case, case_spec, users)

            for doc_spec in case_spec.get("documents", []):
                uploader = users.get(doc_spec.get("uploader", "admin_demo"))
                if uploader is None:
                    uploader = admin_user
                doc = _upload_document(db, case, doc_spec, uploader, storage)
                summary["documents"] += 1
                if doc_spec.get("has_v2"):
                    created = _create_v2_version(
                        db, doc, case, uploader, storage, doc_spec["content"].encode("utf-8")
                    )
                    if created:
                        summary["versions"] += 1

        logger.info("Demo seed complete: %s", summary)
        return summary
    finally:
        if owns_session:
            db.close()


def reset_demo(db: Session | None = None) -> dict:
    """
    Remove all demo data. Uses email/username prefixes to identify demo entities.
    Returns counts of deleted entities.
    """
    owns_session = db is None
    db = db or SessionLocal()
    try:
        from app.models.audit_log import AuditLog
        from app.models.blockchain_record import BlockchainRecord
        from app.models.document_chunk import DocumentChunk
        from app.models.document_text import DocumentText

        demo_users = db.scalars(select(User).where(User.email.like("%@demo.sih"))).all()
        demo_cases = db.scalars(select(Case).where(Case.case_number.like("CASE-2026-%"))).all()
        demo_case_ids = [c.id for c in demo_cases]

        counts = {"users": 0, "cases": 0, "documents": 0}

        if demo_case_ids:
            demo_docs = db.scalars(select(Document).where(Document.case_id.in_(demo_case_ids))).all()
            for doc in demo_docs:
                chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)).all()
                for chunk in chunks:
                    db.delete(chunk)
                texts = db.scalars(select(DocumentText).where(DocumentText.document_id == doc.id)).all()
                for text in texts:
                    db.delete(text)
                versions = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == doc.id)).all()
                for ver in versions:
                    bc = db.scalar(select(BlockchainRecord).where(BlockchainRecord.document_version_id == ver.id))
                    if bc:
                        db.delete(bc)
                    db.delete(ver)
                db.delete(doc)
                counts["documents"] += 1

            for case_id in demo_case_ids:
                members = db.scalars(select(CaseMember).where(CaseMember.case_id == case_id)).all()
                for member in members:
                    db.delete(member)
            for case in demo_cases:
                db.delete(case)
                counts["cases"] += 1

        for user in demo_users:
            db.delete(user)
            counts["users"] += 1

        db.commit()
        logger.info("Demo reset complete: %s", counts)
        return counts
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        result = reset_demo()
        print(f"Demo data reset: {result}")
    else:
        result = seed_demo()
        print(f"Demo data seeded: {result}")
        print(f"\nDemo password for all users: {DEMO_PASSWORD}")
        print("\nDemo users:")
        for u in DEMO_USERS:
            print(f"  {u['username']:25s} ({u['role']})")
