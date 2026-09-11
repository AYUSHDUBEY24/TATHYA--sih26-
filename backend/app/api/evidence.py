"""Evidence / chain-of-custody endpoints (final feature pass).

Assets are case-scoped; every route re-uses the shared case authorization
helpers (``get_authorized_case``) so RBAC/404 semantics match documents.
Transfers are append-only custody events — never rewritten.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_authorized_case, get_current_user
from app.db.database import get_db
from app.models import AssetTransfer, Case, EvidenceAsset, User
from app.schemas.evidence import (
    ALLOWED_ASSET_STATUSES,
    ALLOWED_ASSET_TYPES,
    ALLOWED_TRANSFER_ACTIONS,
    AssetTransferCreate,
    AssetTransferOut,
    ChainOfCustodyResponse,
    EvidenceAssetCreate,
    EvidenceAssetDetail,
    EvidenceAssetOut,
)
from app.services.audit_service import AuditAction, client_ip, log_audit

router = APIRouter()


def _validate_choice(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{label} must be one of: {', '.join(allowed)}",
        )
    return value


def _transfer_out(transfer: AssetTransfer) -> AssetTransferOut:
    return AssetTransferOut(
        id=transfer.id,
        action=transfer.action,
        from_party=transfer.from_party,
        to_party=transfer.to_party,
        purpose=transfer.purpose,
        occurred_at=transfer.occurred_at,
        actor_id=transfer.actor_id,
        actor_name=(
            transfer.actor.full_name or transfer.actor.username
            if transfer.actor is not None
            else "Unknown"
        ),
    )


def _asset_detail(asset: EvidenceAsset) -> EvidenceAssetDetail:
    return EvidenceAssetDetail(
        **EvidenceAssetOut.model_validate(asset).model_dump(),
        transfers=[_transfer_out(t) for t in asset.transfers],
    )


def _next_asset_tag(db: Session, case_id: uuid.UUID) -> str:
    """EV-0001 style per-case tag (case-scoped sequence)."""
    count = db.scalar(
        select(func.count(EvidenceAsset.id)).where(
            EvidenceAsset.case_id == case_id
        )
    )
    return f"EV-{(count or 0) + 1:04d}"


def _get_authorized_asset(
    asset_id: uuid.UUID, current_user: User, db: Session
) -> EvidenceAsset:
    asset = db.scalar(
        select(EvidenceAsset)
        .options(selectinload(EvidenceAsset.transfers))
        .where(EvidenceAsset.id == asset_id)
    )
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evidence asset not found")
    # Case-level authorization (404 semantics shared with documents).
    get_authorized_case(asset.case_id, current_user, db)
    return asset


@router.get("", response_model=list[EvidenceAssetOut])
def list_evidence(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EvidenceAssetOut]:
    """List evidence assets for an authorized case (404 if no access)."""
    case = get_authorized_case(case_id, current_user, db)
    assets = db.scalars(
        select(EvidenceAsset)
        .where(EvidenceAsset.case_id == case.id)
        .order_by(EvidenceAsset.created_at)
    ).all()
    return [EvidenceAssetOut.model_validate(a) for a in assets]


@router.post("", response_model=EvidenceAssetDetail, status_code=201)
def register_evidence(
    payload_case_id: uuid.UUID,
    payload: EvidenceAssetCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceAssetDetail:
    """Register a new evidence asset; the registration is the first custody event."""
    asset_type = _validate_choice(payload.asset_type, ALLOWED_ASSET_TYPES, "asset_type")
    asset_status = _validate_choice(payload.status, ALLOWED_ASSET_STATUSES, "status")
    case = get_authorized_case(payload_case_id, current_user, db)

    asset = EvidenceAsset(
        case_id=case.id,
        asset_tag=_next_asset_tag(db, case.id),
        name=payload.name,
        asset_type=asset_type,
        description=payload.description,
        status=asset_status,
        current_holder=payload.current_holder,
        registered_by=current_user.id,
    )
    db.add(asset)
    db.flush()

    db.add(
        AssetTransfer(
            asset_id=asset.id,
            action="REGISTERED",
            from_party=None,
            to_party=payload.current_holder,
            purpose="Evidence registered into case custody",
            actor_id=current_user.id,
        )
    )
    log_audit(
        db,
        AuditAction.EVIDENCE_REGISTERED,
        actor=current_user,
        entity_type="EVIDENCE_ASSET",
        entity_id=asset.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"asset_tag": asset.asset_tag, "asset_type": asset.asset_type},
    )
    db.commit()
    db.refresh(asset)
    return _asset_detail(asset)


@router.get("/{asset_id}/chain", response_model=ChainOfCustodyResponse)
def chain_of_custody(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChainOfCustodyResponse:
    """Full chain-of-custody timeline for one evidence asset."""
    asset = _get_authorized_asset(asset_id, current_user, db)
    case = db.get(Case, asset.case_id)
    return ChainOfCustodyResponse(
        asset=EvidenceAssetOut.model_validate(asset),
        case_number=case.case_number,
        case_title=case.title,
        transfers=[_transfer_out(t) for t in asset.transfers],
    )


@router.post("/{asset_id}/transfers", response_model=EvidenceAssetDetail)
def add_custody_event(
    asset_id: uuid.UUID,
    payload: AssetTransferCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceAssetDetail:
    """Record a custody event (collect / transfer / examine / store / release)."""
    action = _validate_choice(payload.action, ALLOWED_TRANSFER_ACTIONS, "action")
    asset = _get_authorized_asset(asset_id, current_user, db)

    # Keep the asset's live state consistent with the latest custody event.
    status_map = {
        "REGISTERED": "REGISTERED",
        "COLLECTED": "IN_CUSTODY",
        "TRANSFERRED": "IN_CUSTODY",
        "EXAMINED": "UNDER_EXAMINATION",
        "STORED": "STORED",
        "RELEASED": "RELEASED",
    }
    db.add(
        AssetTransfer(
            asset_id=asset.id,
            action=action,
            from_party=payload.from_party,
            to_party=payload.to_party,
            purpose=payload.purpose,
            actor_id=current_user.id,
            occurred_at=payload.occurred_at or func.now(),
        )
    )
    if payload.to_party:
        asset.current_holder = payload.to_party
    asset.status = status_map.get(action, asset.status)
    log_audit(
        db,
        AuditAction.EVIDENCE_TRANSFERRED,
        actor=current_user,
        entity_type="EVIDENCE_ASSET",
        entity_id=asset.id,
        case_id=asset.case_id,
        ip_address=client_ip(request),
        data={
            "asset_tag": asset.asset_tag,
            "action": action,
            "from_party": payload.from_party,
            "to_party": payload.to_party,
        },
    )
    db.commit()
    db.refresh(asset)
    return _asset_detail(asset)
