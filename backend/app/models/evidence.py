"""Evidence asset + chain-of-custody transfer models.

Evidence assets are case-scoped physical/digital items (laptop, mobile,
documents, USB drives...) whose custody history is tracked as an
append-only list of AssetTransfer events. Transfers are NEVER rewritten —
restores/corrections would be new events, keeping the chain auditable.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class EvidenceAsset(Base):
    __tablename__ = "evidence_assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Human-readable chain tag, e.g. "EV-0001" (unique per case).
    asset_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # LAPTOP / MOBILE_PHONE / DOCUMENT / USB_DRIVE / OTHER (validated in schemas).
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # REGISTERED / IN_CUSTODY / UNDER_EXAMINATION / STORED / RELEASED.
    status: Mapped[str] = mapped_column(
        String(30), default="REGISTERED", nullable=False, index=True
    )
    # Display name of the party currently holding the asset (free text so the
    # chain can reference non-user parties like "Central Forensic Lab").
    current_holder: Mapped[str] = mapped_column(String(255), nullable=False)
    registered_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
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

    case: Mapped["Case"] = relationship()  # noqa: F821
    registrar: Mapped["User"] = relationship()  # noqa: F821
    transfers: Mapped[list["AssetTransfer"]] = relationship(  # noqa: F821
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="AssetTransfer.occurred_at",
    )


class AssetTransfer(Base):
    __tablename__ = "asset_transfers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # REGISTERED / COLLECTED / TRANSFERRED / EXAMINED / STORED / RELEASED
    # (validated in schemas).
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    from_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # The user who recorded this custody event (may differ from the parties).
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset: Mapped["EvidenceAsset"] = relationship(back_populates="transfers")
    actor: Mapped["User"] = relationship()  # noqa: F821
