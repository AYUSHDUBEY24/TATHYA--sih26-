"""
Idempotent baseline seeding: the five prototype roles and demo departments.

Runs automatically at application startup (if the database is reachable) and
can be run manually with: ``python -m app.seed`` (from the backend directory).

All data is synthetic/fictional — never real police or criminal data.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.department import Department
from app.models.role import Role

ROLES: list[tuple[str, str]] = [
    (
        "ADMIN",
        "System administrator: users, roles, departments, audit, configuration",
    ),
    (
        "INVESTIGATING_OFFICER",
        "Assigned cases, document upload/versioning, authorized search and AI",
    ),
    (
        "SUPERVISOR",
        "Department case review, activity/audit review, reports, approvals",
    ),
    (
        "FORENSIC_OFFICER",
        "Authorized evidence/forensic cases, forensic report uploads",
    ),
    (
        "PROSECUTOR",
        "Authorized legal/court documents, charge sheets, filings, AI over authorized data",
    ),
]

DEPARTMENTS: list[tuple[str, str]] = [
    ("NCRB", "National Crime Records Bureau (synthetic demo)"),
    ("STATE_CRIME_BRANCH", "State Crime Branch (synthetic demo)"),
    ("FORENSIC_SCIENCE_LAB", "Forensic Science Laboratory (synthetic demo)"),
]


def seed_default_data(db: Session | None = None) -> None:
    """Insert any missing roles/departments. Safe to run repeatedly."""
    owns_session = db is None
    db = db or SessionLocal()
    try:
        for name, description in ROLES:
            if db.scalar(select(Role).where(Role.name == name)) is None:
                db.add(Role(name=name, description=description))
        for name, description in DEPARTMENTS:
            if db.scalar(select(Department).where(Department.name == name)) is None:
                db.add(Department(name=name, description=description))
        db.commit()
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    seed_default_data()
    print("Baseline roles and departments seeded (idempotent).")
