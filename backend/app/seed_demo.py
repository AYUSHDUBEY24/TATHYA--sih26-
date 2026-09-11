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
    CYBERSTALKING_COMM_ANALYSIS,
    CYBERSTALKING_COMPLAINT_FIR,
    CYBERSTALKING_DEVICE_EXAM,
    CYBERSTALKING_SOCIAL_EVIDENCE,
    CYBERSTALKING_SUMMARY,
    EMBEZZLEMENT_AUDIT_FINDINGS,
    EMBEZZLEMENT_COMPLAINT,
    EMBEZZLEMENT_FIR,
    EMBEZZLEMENT_INVESTIGATION_REPORT,
    EMBEZZLEMENT_PRELIM_CHARGE,
    EMBEZZLEMENT_STATEMENT_REVIEW,
    EMBEZZLEMENT_TRANSACTION_ANALYSIS,
    FORGERY_AUTH_REPORT,
    FORGERY_FINDINGS,
    FORGERY_FIR,
    FORGERY_HANDWRITING_REPORT,
    FORGERY_SUSPECTED_DEED,
    FRAUD_CHARGE_SHEET,
    FRAUD_FIR,
    FRAUD_FORENSIC_REPORT,
    FRAUD_INVESTIGATION_REPORT,
    FRAUD_PHISHING_BANK_ANALYSIS,
    FRAUD_PHISHING_DEVICE_EXAM,
    FRAUD_PHISHING_EMAIL_EVIDENCE,
    FRAUD_PHISHING_FIR,
    FRAUD_PHISHING_PRELIM_REPORT,
    FRAUD_WITNESS_STATEMENT_01,
    MISSING_CCTV_ANALYSIS,
    MISSING_FIR,
    MISSING_INITIAL_INVESTIGATION,
    MISSING_INVESTIGATION_REPORT,
    MISSING_MOBILE_LOCATION,
    MISSING_PERSON_REPORT,
    MISSING_WITNESS_STATEMENTS_DOC,
    NARCOTICS_EVIDENCE_RECORD,
    NARCOTICS_FIR,
    NARCOTICS_FORENSIC_REPORT,
    NARCOTICS_INVESTIGATION_REPORT,
    NARCOTICS_WITNESS_STATEMENT_01,
    PROPERTY_FIR,
    PROPERTY_INVESTIGATION_REPORT,
    PROPERTY_WITNESS_STATEMENT_01,
    VEHICLE_CCTV_ROUTE,
    VEHICLE_PROGRESS_REPORT,
    VEHICLE_RECOVERY_MEMO,
    VEHICLE_REG_VERIFICATION,
    VEHICLE_THEFT_FIR,
)
from app.core.hashing import sha256_hex
from app.core.security import hash_password
from app.db.database import Base, SessionLocal
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.department import Department
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.evidence import AssetTransfer, EvidenceAsset
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
    # Showcase-case officers (Operation series, CASE-2026-0101..0106).
    {"email": "io.malhotra@demo.sih", "username": "io_malhotra", "full_name": "Insp. Arjun Malhotra (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.mehta@demo.sih", "username": "supervisor_mehta", "full_name": "ACP Raghav Mehta (Demo)", "role": "SUPERVISOR"},
    {"email": "io.kapoor@demo.sih", "username": "io_kapoor", "full_name": "Insp. Meera Kapoor (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.sethi@demo.sih", "username": "supervisor_sethi", "full_name": "ACP Vikram Sethi (Demo)", "role": "SUPERVISOR"},
    {"email": "io.nair@demo.sih", "username": "io_nair", "full_name": "Insp. Kavya Nair (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.bhatia@demo.sih", "username": "supervisor_bhatia", "full_name": "ACP Sameer Bhatia (Demo)", "role": "SUPERVISOR"},
    {"email": "io.verma@demo.sih", "username": "io_verma", "full_name": "Insp. Rohit Verma (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.arora@demo.sih", "username": "supervisor_arora", "full_name": "ACP Nitin Arora (Demo)", "role": "SUPERVISOR"},
    {"email": "io.rao@demo.sih", "username": "io_rao", "full_name": "Insp. Aditya Rao (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.bansal@demo.sih", "username": "supervisor_bansal", "full_name": "ACP Neha Bansal (Demo)", "role": "SUPERVISOR"},
    {"email": "io.sharma@demo.sih", "username": "io_sharma", "full_name": "Insp. Ananya Sharma (Demo)", "role": "INVESTIGATING_OFFICER"},
    {"email": "supervisor.khanna@demo.sih", "username": "supervisor_khanna", "full_name": "ACP Karan Khanna (Demo)", "role": "SUPERVISOR"},
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
        "evidence": [
            {
                "asset_tag": "CASE-2026-001-EV-01",
                "name": "Seized phishing workstation laptop",
                "asset_type": "LAPTOP",
                "description": "Dell laptop recovered from accused's residence; used to send bulk phishing SMS with fake bank links.",
                "status": "REGISTERED",
                "current_holder": "Insp. Kavita Reddy",
                "registered_by": "io_reddy",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accused residence, Visakhapatnam (seizure memo 14/2026)", "to_party": "Insp. Kavita Reddy", "actor": "io_reddy", "status": "IN_CUSTODY", "holder": "Insp. Kavita Reddy"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Kavita Reddy", "to_party": "FSL Hyderabad - Digital Division", "purpose": "Disk imaging and artefact examination", "actor": "io_reddy", "status": "UNDER_EXAMINATION", "holder": "FSL Hyderabad - Digital Division"},
                ],
            },
            {
                "asset_tag": "CASE-2026-001-EV-02",
                "name": "Mobile phone used for OTP interception",
                "asset_type": "MOBILE_PHONE",
                "description": "Dual-SIM handset with 3 banking apps logged in under victim identities.",
                "status": "REGISTERED",
                "current_holder": "Insp. Kavita Reddy",
                "registered_by": "io_reddy",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accused residence, Visakhapatnam (seizure memo 14/2026)", "to_party": "Insp. Kavita Reddy", "actor": "io_reddy", "status": "IN_CUSTODY", "holder": "Insp. Kavita Reddy"},
                ],
            },
            {
                "asset_tag": "CASE-2026-001-EV-03",
                "name": "USB drive containing phishing kit",
                "asset_type": "USB_DRIVE",
                "description": "16 GB pen drive with SMS-gateway scripts and 2,100 harvested credential records.",
                "status": "REGISTERED",
                "current_holder": "FSL Hyderabad - Digital Division",
                "registered_by": "forensic_kumar",
                "transfers": [
                    {"action": "EXAMINED", "from_party": "Insp. Kavita Reddy", "to_party": "Dr. Suresh Kumar (FSL)", "purpose": "Malware and credential-dump analysis", "actor": "forensic_kumar", "status": "UNDER_EXAMINATION", "holder": "FSL Hyderabad - Digital Division"},
                ],
            },
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
        "evidence": [
            {
                "asset_tag": "CASE-2026-002-EV-01",
                "name": "Suspected forged sale deed (original)",
                "asset_type": "DOCUMENT",
                "description": "Registered sale deed dated 02/03/2026 bearing suspect signature and proxy-Aadhaar biometric stamp.",
                "status": "REGISTERED",
                "current_holder": "Insp. Rajesh Patil",
                "registered_by": "supervisor_patil",
                "transfers": [
                    {"action": "TRANSFERRED", "from_party": "Insp. Rajesh Patil", "to_party": "Handwriting & Document Examination Division, FSL Pune", "purpose": "Ink ageing, signature and stamp examination", "actor": "supervisor_patil", "status": "UNDER_EXAMINATION", "holder": "FSL Pune - Document Division"},
                    {"action": "STORED", "from_party": "FSL Pune - Document Division", "to_party": "Civil Lines PS malkhana", "purpose": "Safe custody after examination report", "actor": "supervisor_patil", "status": "STORED", "holder": "Civil Lines PS malkhana"},
                ],
            },
            {
                "asset_tag": "CASE-2026-002-EV-02",
                "name": "Seized desktop used for proxy-Aadhaar attempt",
                "asset_type": "LAPTOP",
                "description": "Desktop from a private document-writing bureau; browser history shows six Aadhaar authentication attempts.",
                "status": "REGISTERED",
                "current_holder": "Insp. Rajesh Patil",
                "registered_by": "supervisor_patil",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Sai Document Bureau, Pune (panchnama 09/2026)", "to_party": "Insp. Rajesh Patil", "actor": "supervisor_patil", "status": "IN_CUSTODY", "holder": "Insp. Rajesh Patil"},
                ],
            },
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
        "evidence": [
            {
                "asset_tag": "CASE-2026-003-EV-01",
                "name": "Seized heroin packages (12.5 kg)",
                "asset_type": "OTHER",
                "description": "24 vacuum-sealed packets recovered from truck cabin at NH-16 checkpoint; forwarded for FSL qualitative analysis.",
                "status": "REGISTERED",
                "current_holder": "NCB Malkhana, Hyderabad",
                "registered_by": "io_reddy",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "NH-16 checkpoint seizure site", "to_party": "Insp. Kavita Reddy", "actor": "io_reddy", "status": "IN_CUSTODY", "holder": "Insp. Kavita Reddy"},
                    {"action": "EXAMINED", "from_party": "Insp. Kavita Reddy", "to_party": "Dr. Suresh Kumar (FSL)", "purpose": "Qualitative and quantitative narcotic analysis", "actor": "forensic_kumar", "status": "UNDER_EXAMINATION", "holder": "FSL Hyderabad"},
                    {"action": "STORED", "from_party": "FSL Hyderabad", "to_party": "NCB Malkhana, Hyderabad", "purpose": "Court-directed safe custody pending trial", "actor": "forensic_kumar", "status": "STORED", "holder": "NCB Malkhana, Hyderabad"},
                ],
            },
            {
                "asset_tag": "CASE-2026-003-EV-02",
                "name": "Mobile phone with trafficking communication",
                "asset_type": "MOBILE_PHONE",
                "description": "Handset of the truck driver containing encrypted chat coordination for the consignment.",
                "status": "REGISTERED",
                "current_holder": "Insp. Kavita Reddy",
                "registered_by": "io_reddy",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Truck driver at NH-16 checkpoint", "to_party": "Insp. Kavita Reddy", "actor": "io_reddy", "status": "IN_CUSTODY", "holder": "Insp. Kavita Reddy"},
                ],
            },
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
        "evidence": [
            {
                "asset_tag": "CASE-2026-004-EV-01",
                "name": "Core-banking backup drive (mirror copy)",
                "asset_type": "STORAGE_DEVICE",
                "description": "Forensic mirror of the cooperative bank's transaction database covering FY2022-FY2026.",
                "status": "REGISTERED",
                "current_holder": "EOW Evidence Store, Delhi",
                "registered_by": "supervisor_patil",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Cooperative bank head office IT cell", "to_party": "Insp. Rajesh Patil", "purpose": "Imaged on-site under seizure memo 206/2026", "actor": "supervisor_patil", "status": "IN_CUSTODY", "holder": "Insp. Rajesh Patil"},
                    {"action": "STORED", "from_party": "Insp. Rajesh Patil", "to_party": "EOW Evidence Store, Delhi", "purpose": "Custody after charge-sheet filing", "actor": "supervisor_patil", "status": "STORED", "holder": "EOW Evidence Store, Delhi"},
                ],
            },
            {
                "asset_tag": "CASE-2026-004-EV-02",
                "name": "Fabricated ledger notebooks (3 volumes)",
                "asset_type": "DOCUMENT",
                "description": "Hand-maintained ledgers showing inflated interest accruals fed into the banking software.",
                "status": "REGISTERED",
                "current_holder": "EOW Evidence Store, Delhi",
                "registered_by": "supervisor_patil",
                "transfers": [
                    {"action": "STORED", "from_party": "Insp. Rajesh Patil", "to_party": "EOW Evidence Store, Delhi", "purpose": "Permanent custody post-conviction", "actor": "supervisor_patil", "status": "STORED", "holder": "EOW Evidence Store, Delhi"},
                ],
            },
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
    {
        "case_number": "CASE-2026-0101",
        "title": "Operation Digital Shield",
        "description": "Organised phishing operation targeting financial institution customers via fake banking portals and OTP interception",
        "crime_type": "CYBER_FRAUD",
        "police_station": "Cyber Crime Cell - North District",
        "status": "UNDER_INVESTIGATION",
        "assigned_io_username": "io_malhotra",
        "members": [
            {"username": "io_malhotra", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_mehta", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0101-EV-01",
                "name": "Seized mobile phone (OTP interception)",
                "asset_type": "MOBILE_PHONE",
                "description": "Dual-SIM handset with fake banking apps used to intercept OTPs",
                "status": "REGISTERED",
                "current_holder": "Insp. Arjun Malhotra",
                "registered_by": "io_malhotra",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accused residence", "to_party": "Insp. Arjun Malhotra", "actor": "io_malhotra", "status": "IN_CUSTODY", "holder": "Insp. Arjun Malhotra"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Arjun Malhotra", "to_party": "Cyber Lab", "purpose": "Digital forensic examination", "actor": "io_malhotra", "status": "UNDER_EXAMINATION", "holder": "Cyber Lab"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0101-EV-02",
                "name": "Seized laptop (phishing workstation)",
                "asset_type": "LAPTOP",
                "description": "Dell laptop used to operate fake banking portals",
                "status": "REGISTERED",
                "current_holder": "Cyber Lab",
                "registered_by": "io_malhotra",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accused residence", "to_party": "Insp. Arjun Malhotra", "actor": "io_malhotra", "status": "IN_CUSTODY", "holder": "Insp. Arjun Malhotra"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Arjun Malhotra", "to_party": "Cyber Lab", "purpose": "Disk imaging", "actor": "io_malhotra", "status": "UNDER_EXAMINATION", "holder": "Cyber Lab"},
                    {"action": "RETURNED", "from_party": "Cyber Lab", "to_party": "Insp. Arjun Malhotra", "purpose": "Examination complete", "actor": "forensic_kumar", "status": "IN_CUSTODY", "holder": "Insp. Arjun Malhotra"},
                ],
            },
        ],
        "documents": [
            {"filename": "FIR_Operation_Digital_Shield.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": FRAUD_PHISHING_FIR, "uploader": "io_malhotra"},
            {"filename": "Bank_Transaction_Analysis.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": FRAUD_PHISHING_BANK_ANALYSIS, "uploader": "io_malhotra"},
            {"filename": "Phishing_Email_Evidence.txt", "doc_type": "EVIDENCE_RECORD", "classification": "RESTRICTED", "content": FRAUD_PHISHING_EMAIL_EVIDENCE, "uploader": "io_malhotra"},
            {"filename": "Device_Examination_Report.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": FRAUD_PHISHING_DEVICE_EXAM, "uploader": "forensic_kumar"},
            {"filename": "Preliminary_Investigation_Report.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": FRAUD_PHISHING_PRELIM_REPORT, "uploader": "io_malhotra", "has_v2": True},
        ],
    },
    {
        "case_number": "CASE-2026-0102",
        "title": "Operation Paper Trail",
        "description": "Document forgery involving fraudulent sale deed for property in Central District",
        "crime_type": "FORGERY",
        "police_station": "Economic Offences Unit - Central District",
        "status": "UNDER_REVIEW",
        "assigned_io_username": "io_kapoor",
        "members": [
            {"username": "io_kapoor", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_sethi", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0102-EV-01",
                "name": "Suspected forged sale deed",
                "asset_type": "DOCUMENT",
                "description": "Alleged forged sale deed for property SG-214/2024",
                "status": "REGISTERED",
                "current_holder": "Insp. Meera Kapoor",
                "registered_by": "io_kapoor",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Complainant", "to_party": "Insp. Meera Kapoor", "actor": "io_kapoor", "status": "IN_CUSTODY", "holder": "Insp. Meera Kapoor"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Meera Kapoor", "to_party": "Document Examiner", "purpose": "Handwriting analysis", "actor": "io_kapoor", "status": "UNDER_EXAMINATION", "holder": "Document Examiner"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0102-EV-02",
                "name": "Original reference document",
                "asset_type": "DOCUMENT",
                "description": "Genuine sale deed for comparison",
                "status": "REGISTERED",
                "current_holder": "Document Examiner",
                "registered_by": "io_kapoor",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Registry Office", "to_party": "Insp. Meera Kapoor", "actor": "io_kapoor", "status": "IN_CUSTODY", "holder": "Insp. Meera Kapoor"},
                ],
            },
        ],
        "documents": [
            {"filename": "Complaint_and_FIR.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": FORGERY_FIR, "uploader": "io_kapoor"},
            {"filename": "Suspected_Forged_Agreement.txt", "doc_type": "EVIDENCE_RECORD", "classification": "CONFIDENTIAL", "content": FORGERY_SUSPECTED_DEED, "uploader": "io_kapoor"},
            {"filename": "Handwriting_Examination_Report.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": FORGERY_HANDWRITING_REPORT, "uploader": "forensic_kumar"},
            {"filename": "Document_Authentication_Report.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": FORGERY_AUTH_REPORT, "uploader": "forensic_kumar"},
            {"filename": "Investigation_Findings.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": FORGERY_FINDINGS, "uploader": "io_kapoor", "has_v2": True},
        ],
    },
    {
        "case_number": "CASE-2026-0103",
        "title": "Operation Safe Return",
        "description": "Missing person investigation for a young woman last seen near Riverside area",
        "crime_type": "MISSING_PERSON",
        "police_station": "Riverside Police Station",
        "status": "ACTIVE",
        "assigned_io_username": "io_nair",
        "members": [
            {"username": "io_nair", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_bhatia", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0103-EV-01",
                "name": "Mobile phone of missing person",
                "asset_type": "MOBILE_PHONE",
                "description": "Last known device of the missing person",
                "status": "REGISTERED",
                "current_holder": "Insp. Kavya Nair",
                "registered_by": "io_nair",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Family", "to_party": "Insp. Kavya Nair", "actor": "io_nair", "status": "IN_CUSTODY", "holder": "Insp. Kavya Nair"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Kavya Nair", "to_party": "Digital Forensics Officer", "purpose": "CDR and location analysis", "actor": "io_nair", "status": "UNDER_EXAMINATION", "holder": "Digital Forensics Officer"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0103-EV-02",
                "name": "CCTV footage metadata",
                "asset_type": "DIGITAL_EVIDENCE",
                "description": "Footage from cameras near last-seen location",
                "status": "REGISTERED",
                "current_holder": "Insp. Kavya Nair",
                "registered_by": "io_nair",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Local businesses", "to_party": "Insp. Kavya Nair", "actor": "io_nair", "status": "IN_CUSTODY", "holder": "Insp. Kavya Nair"},
                ],
            },
        ],
        "documents": [
            {"filename": "Missing_Person_Report.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": MISSING_PERSON_REPORT, "uploader": "io_nair"},
            {"filename": "Initial_Investigation_Report.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": MISSING_INITIAL_INVESTIGATION, "uploader": "io_nair"},
            {"filename": "CCTV_Analysis_Report.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": MISSING_CCTV_ANALYSIS, "uploader": "io_nair"},
            {"filename": "Mobile_Location_Analysis.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": MISSING_MOBILE_LOCATION, "uploader": "forensic_kumar"},
            {"filename": "Witness_Statements.txt", "doc_type": "WITNESS_STATEMENT", "classification": "RESTRICTED", "content": MISSING_WITNESS_STATEMENTS_DOC, "uploader": "io_nair", "has_v2": True},
        ],
    },
    {
        "case_number": "CASE-2026-0104",
        "title": "Operation Road Trace",
        "description": "Stolen vehicle investigation involving a commercial truck",
        "crime_type": "VEHICLE_THEFT",
        "police_station": "Industrial Area Police Station",
        "status": "INVESTIGATION_ONGOING",
        "assigned_io_username": "io_verma",
        "members": [
            {"username": "io_verma", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_arora", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0104-EV-01",
                "name": "Recovered vehicle",
                "asset_type": "VEHICLE",
                "description": "Commercial truck recovered from abandoned warehouse",
                "status": "REGISTERED",
                "current_holder": "Insp. Rohit Verma",
                "registered_by": "io_verma",
                "transfers": [
                    {"action": "RECOVERED", "from_party": "Abandoned warehouse", "to_party": "Insp. Rohit Verma", "actor": "io_verma", "status": "IN_CUSTODY", "holder": "Insp. Rohit Verma"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Rohit Verma", "to_party": "Vehicle Examination Unit", "purpose": "Fingerprint and DNA sampling", "actor": "io_verma", "status": "UNDER_EXAMINATION", "holder": "Vehicle Examination Unit"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0104-EV-02",
                "name": "CCTV footage report",
                "asset_type": "DIGITAL_EVIDENCE",
                "description": "Route analysis from highway cameras",
                "status": "REGISTERED",
                "current_holder": "Insp. Rohit Verma",
                "registered_by": "io_verma",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Highway authority", "to_party": "Insp. Rohit Verma", "actor": "io_verma", "status": "IN_CUSTODY", "holder": "Insp. Rohit Verma"},
                ],
            },
        ],
        "documents": [
            {"filename": "Vehicle_Theft_FIR.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": VEHICLE_THEFT_FIR, "uploader": "io_verma"},
            {"filename": "Vehicle_Registration_Verification.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": VEHICLE_REG_VERIFICATION, "uploader": "io_verma"},
            {"filename": "CCTV_Route_Analysis.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": VEHICLE_CCTV_ROUTE, "uploader": "io_verma"},
            {"filename": "Recovery_Memo.txt", "doc_type": "EVIDENCE_RECORD", "classification": "RESTRICTED", "content": VEHICLE_RECOVERY_MEMO, "uploader": "io_verma"},
            {"filename": "Investigation_Progress_Report.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": VEHICLE_PROGRESS_REPORT, "uploader": "io_verma", "has_v2": True},
        ],
    },
    {
        "case_number": "CASE-2026-0105",
        "title": "Operation Ledger Watch",
        "description": "Financial fraud and embezzlement investigation involving fictitious vendor payments",
        "crime_type": "FINANCIAL_FRAUD",
        "police_station": "Economic Offences Wing - East District",
        "status": "UNDER_INVESTIGATION",
        "assigned_io_username": "io_rao",
        "members": [
            {"username": "io_rao", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_bansal", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0105-EV-01",
                "name": "Financial records",
                "asset_type": "DOCUMENT",
                "description": "Bank statements and fictitious invoices",
                "status": "REGISTERED",
                "current_holder": "Insp. Aditya Rao",
                "registered_by": "io_rao",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accounts department", "to_party": "Insp. Aditya Rao", "actor": "io_rao", "status": "IN_CUSTODY", "holder": "Insp. Aditya Rao"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Aditya Rao", "to_party": "Financial Analysis Unit", "purpose": "Transaction pattern analysis", "actor": "io_rao", "status": "UNDER_EXAMINATION", "holder": "Financial Analysis Unit"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0105-EV-02",
                "name": "Transaction dataset",
                "asset_type": "DIGITAL_EVIDENCE",
                "description": "Digital records of suspicious transactions",
                "status": "REGISTERED",
                "current_holder": "Financial Analysis Unit",
                "registered_by": "io_rao",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Bank", "to_party": "Insp. Aditya Rao", "actor": "io_rao", "status": "IN_CUSTODY", "holder": "Insp. Aditya Rao"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Aditya Rao", "to_party": "Financial Analysis Unit", "purpose": "Forensic accounting", "actor": "io_rao", "status": "UNDER_EXAMINATION", "holder": "Financial Analysis Unit"},
                ],
            },
        ],
        "documents": [
            {"filename": "Complaint_Report.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": EMBEZZLEMENT_COMPLAINT, "uploader": "io_rao"},
            {"filename": "Financial_Transaction_Analysis.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": EMBEZZLEMENT_TRANSACTION_ANALYSIS, "uploader": "io_rao"},
            {"filename": "Account_Statement_Review.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": EMBEZZLEMENT_STATEMENT_REVIEW, "uploader": "io_rao"},
            {"filename": "Audit_Findings.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": EMBEZZLEMENT_AUDIT_FINDINGS, "uploader": "forensic_kumar"},
            {"filename": "Preliminary_Charge_Report.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": EMBEZZLEMENT_PRELIM_CHARGE, "uploader": "io_rao", "has_v2": True},
        ],
    },
    {
        "case_number": "CASE-2026-0106",
        "title": "Operation Silent Shield",
        "description": "Cyberstalking and digital harassment investigation",
        "crime_type": "CYBERSTALKING",
        "police_station": "Cyber Crime Unit - South District",
        "status": "UNDER_INVESTIGATION",
        "assigned_io_username": "io_sharma",
        "members": [
            {"username": "io_sharma", "role_in_case": "INVESTIGATING_OFFICER"},
            {"username": "forensic_kumar", "role_in_case": "FORENSIC_EXAMINER"},
            {"username": "supervisor_khanna", "role_in_case": "SUPERVISOR"},
        ],
        "evidence": [
            {
                "asset_tag": "CASE-2026-0106-EV-01",
                "name": "Mobile phone",
                "asset_type": "MOBILE_PHONE",
                "description": "Device used for harassment",
                "status": "REGISTERED",
                "current_holder": "Insp. Ananya Sharma",
                "registered_by": "io_sharma",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Victim", "to_party": "Insp. Ananya Sharma", "actor": "io_sharma", "status": "IN_CUSTODY", "holder": "Insp. Ananya Sharma"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Ananya Sharma", "to_party": "Digital Forensics Officer", "purpose": "Message extraction", "actor": "io_sharma", "status": "UNDER_EXAMINATION", "holder": "Digital Forensics Officer"},
                ],
            },
            {
                "asset_tag": "CASE-2026-0106-EV-02",
                "name": "Computer",
                "asset_type": "COMPUTER",
                "description": "Desktop used for stalking activities",
                "status": "REGISTERED",
                "current_holder": "Cyber Lab",
                "registered_by": "io_sharma",
                "transfers": [
                    {"action": "COLLECTED", "from_party": "Accused residence", "to_party": "Insp. Ananya Sharma", "actor": "io_sharma", "status": "IN_CUSTODY", "holder": "Insp. Ananya Sharma"},
                    {"action": "TRANSFERRED", "from_party": "Insp. Ananya Sharma", "to_party": "Cyber Lab", "purpose": "Browser history analysis", "actor": "io_sharma", "status": "UNDER_EXAMINATION", "holder": "Cyber Lab"},
                    {"action": "RETURNED", "from_party": "Cyber Lab", "to_party": "Evidence Store", "purpose": "Secure storage", "actor": "forensic_kumar", "status": "IN_CUSTODY", "holder": "Evidence Store"},
                ],
            },
        ],
        "documents": [
            {"filename": "Complaint_and_FIR.txt", "doc_type": "FIR", "classification": "RESTRICTED", "content": CYBERSTALKING_COMPLAINT_FIR, "uploader": "io_sharma"},
            {"filename": "Digital_Communication_Analysis.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "CONFIDENTIAL", "content": CYBERSTALKING_COMM_ANALYSIS, "uploader": "io_sharma"},
            {"filename": "Social_Media_Evidence_Report.txt", "doc_type": "EVIDENCE_RECORD", "classification": "CONFIDENTIAL", "content": CYBERSTALKING_SOCIAL_EVIDENCE, "uploader": "io_sharma"},
            {"filename": "Device_Forensic_Examination.txt", "doc_type": "FORENSIC_REPORT", "classification": "CONFIDENTIAL", "content": CYBERSTALKING_DEVICE_EXAM, "uploader": "forensic_kumar"},
            {"filename": "Investigation_Summary.txt", "doc_type": "INVESTIGATION_REPORT", "classification": "RESTRICTED", "content": CYBERSTALKING_SUMMARY, "uploader": "io_sharma", "has_v2": True},
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


def _register_evidence_asset(
    db: Session, case: Case, ev_spec: dict, registrar: User
) -> EvidenceAsset:
    """Register an evidence asset from spec (idempotent by case+asset_tag)."""
    existing = db.scalar(
        select(EvidenceAsset).where(
            EvidenceAsset.case_id == case.id, EvidenceAsset.asset_tag == ev_spec["asset_tag"]
        )
    )
    if existing is not None:
        return existing
    asset = EvidenceAsset(
        case_id=case.id,
        asset_tag=ev_spec["asset_tag"],
        name=ev_spec["name"],
        asset_type=ev_spec["asset_type"],
        description=ev_spec.get("description"),
        status=ev_spec.get("status", "REGISTERED"),
        current_holder=ev_spec["current_holder"],
        registered_by=registrar.id,
    )
    db.add(asset)
    log_audit(
        db,
        AuditAction.EVIDENCE_REGISTERED,
        actor=registrar,
        entity_type="EVIDENCE",
        entity_id=asset.id,
        case_id=case.id,
        data={"asset_tag": asset.asset_tag, "name": asset.name, "asset_type": asset.asset_type},
    )
    db.commit()
    db.refresh(asset)
    return asset


def _transfer_evidence(
    db: Session, asset: EvidenceAsset, t_spec: dict, actor: User
) -> None:
    """Append a custody transfer event (idempotent by asset+action+parties)."""
    existing = db.scalar(
        select(AssetTransfer).where(
            AssetTransfer.asset_id == asset.id,
            AssetTransfer.action == t_spec["action"],
            AssetTransfer.from_party == t_spec.get("from_party"),
            AssetTransfer.to_party == t_spec.get("to_party"),
        )
    )
    if existing is not None:
        return
    transfer = AssetTransfer(
        asset_id=asset.id,
        action=t_spec["action"],
        from_party=t_spec.get("from_party"),
        to_party=t_spec.get("to_party"),
        purpose=t_spec.get("purpose"),
        actor_id=actor.id,
    )
    db.add(transfer)
    if t_spec.get("status"):
        asset.status = t_spec["status"]
    if t_spec.get("holder"):
        asset.current_holder = t_spec["holder"]
    log_audit(
        db,
        AuditAction.EVIDENCE_TRANSFERRED,
        actor=actor,
        entity_type="EVIDENCE",
        entity_id=asset.id,
        case_id=asset.case_id,
        data={
            "asset_tag": asset.asset_tag,
            "action": t_spec["action"],
            "from_party": t_spec.get("from_party"),
            "to_party": t_spec.get("to_party"),
        },
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

            for ev_spec in case_spec.get("evidence", []):
                registrar = users.get(ev_spec.get("registered_by", "admin_demo"))
                if registrar is None:
                    registrar = admin_user
                asset = _register_evidence_asset(db, case, ev_spec, registrar)
                for t_spec in ev_spec.get("transfers", []):
                    actor = users.get(t_spec.get("actor", "admin_demo"))
                    if actor is None:
                        actor = admin_user
                    _transfer_evidence(db, asset, t_spec, actor)

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
