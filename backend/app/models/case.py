"""Case model — a case-centric record tying together documents and evidence."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    crime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    police_station: Mapped[str] = mapped_column(String(150), nullable=False)

    # One of the documented statuses (validated in the Pydantic schemas):
    # OPEN, UNDER_INVESTIGATION, UNDER_REVIEW, CHARGESHEET_FILED,
    # COURT_STAGE, CLOSED, ARCHIVED
    status: Mapped[str] = mapped_column(
        String(30), default="OPEN", nullable=False, index=True
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    assigned_io_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creator: Mapped["User"] = relationship(  # noqa: F821
        foreign_keys=[created_by]
    )
    assigned_io: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[assigned_io_id]
    )
    members: Mapped[list["CaseMember"]] = relationship(  # noqa: F821
        back_populates="case", cascade="all, delete-orphan"
    )
