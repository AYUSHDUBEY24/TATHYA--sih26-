"""Case management endpoints — all access checks are backend-enforced."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_authorized_case,
    get_current_user,
    require_roles,
    user_can_manage_case,
)
from app.db.database import get_db
from app.models.case import Case
from app.models.case_member import CaseMember
from app.models.role import Role
from app.models.user import User
from app.schemas.case import (
    CaseAccessResponse,
    CaseCreate,
    CaseDetailResponse,
    CaseMemberAdd,
    CaseMemberOut,
    CaseResponse,
    CaseStatus,
    CaseUpdate,
)
from app.schemas.auth import MessageResponse
from app.services.audit_service import AuditAction, client_ip, log_audit

router = APIRouter()


def _generate_case_number(db: Session) -> str:
    """Generate the next CASE-<year>-<seq> number for this year.

    Sequence numbers are parsed NUMERICALLY (not via string ordering) so
    pre-existing rows with inconsistent zero-padding (e.g. a mixed
    ``CASE-2026-0008`` alongside ``CASE-2026-007``) can never break sequence
    generation or collide with an existing number.
    """
    year = date.today().year
    prefix = f"CASE-{year}-"
    seqs = db.scalars(
        select(Case.case_number).where(Case.case_number.like(f"{prefix}%"))
    ).all()
    max_seq = 0
    for value in seqs:
        try:
            max_seq = max(max_seq, int(value.rsplit("-", 1)[-1]))
        except ValueError:
            continue
    return f"{prefix}{max_seq + 1:04d}"


def _case_detail(case: Case, current_user: User, db: Session) -> CaseDetailResponse:
    """Build the full case detail payload (members + manage flag)."""
    memberships = db.scalars(
        select(CaseMember)
        .where(CaseMember.case_id == case.id)
        .order_by(CaseMember.joined_at)
    ).all()
    return CaseDetailResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        crime_type=case.crime_type,
        police_station=case.police_station,
        status=case.status,
        created_by=case.created_by,
        assigned_io=case.assigned_io,
        created_at=case.created_at,
        updated_at=case.updated_at,
        members=[
            CaseMemberOut(
                id=m.id,
                user_id=m.user_id,
                username=m.user.username,
                full_name=m.user.full_name,
                role_in_case=m.role_in_case,
                joined_at=m.joined_at,
            )
            for m in memberships
        ],
        can_manage=user_can_manage_case(current_user, case),
    )


@router.get("", response_model=list[CaseResponse], summary="List cases visible to you")
def list_cases(
    case_status: CaseStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Case]:
    """ADMIN sees all cases; everyone else sees only authorized cases."""
    stmt = select(Case).order_by(Case.updated_at.desc())
    if case_status is not None:
        stmt = stmt.where(Case.status == case_status)
    if current_user.role.name != "ADMIN":
        member_case_ids = select(CaseMember.case_id).where(
            CaseMember.user_id == current_user.id
        )
        stmt = stmt.where(
            (Case.assigned_io_id == current_user.id)
            | (Case.id.in_(member_case_ids))
        )
    return list(db.scalars(stmt).all())


@router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a case (ADMIN or INVESTIGATING_OFFICER)",
)
def create_case(
    payload: CaseCreate,
    request: Request,
    current_user: User = Depends(require_roles("ADMIN", "INVESTIGATING_OFFICER")),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    # Resolve optional assigned IO — must be an existing investigating officer.
    assigned_io: User | None = None
    if payload.assigned_io_id is not None:
        assigned_io = db.get(User, payload.assigned_io_id)
        if (
            assigned_io is None
            or assigned_io.role.name != "INVESTIGATING_OFFICER"
        ):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "assigned_io_id must reference an existing investigating officer",
            )

    case_number = payload.case_number or _generate_case_number(db)
    if db.scalar(select(Case).where(Case.case_number == case_number)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Case number already exists")

    case = Case(
        case_number=case_number,
        title=payload.title,
        description=payload.description,
        crime_type=payload.crime_type,
        police_station=payload.police_station,
        status=payload.status,
        created_by=current_user.id,
        assigned_io_id=assigned_io.id if assigned_io else None,
    )
    db.add(case)
    db.flush()  # need case.id before adding members

    # The creator always becomes a member; the assigned IO is synced too.
    memberships: dict[UUID, str] = {current_user.id: current_user.role.name}
    if assigned_io is not None and assigned_io.id != current_user.id:
        memberships[assigned_io.id] = "INVESTIGATING_OFFICER"
    for user_id, role_in_case in memberships.items():
        db.add(CaseMember(case_id=case.id, user_id=user_id, role_in_case=role_in_case))

    log_audit(
        db,
        AuditAction.CASE_CREATED,
        actor=current_user,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"case_number": case.case_number, "title": case.title},
    )

    db.commit()
    db.refresh(case)
    return _case_detail(case, current_user, db)


@router.get("/{case_id}", response_model=CaseDetailResponse, summary="Case details")
def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    case = get_authorized_case(case_id, current_user, db)
    return _case_detail(case, current_user, db)


@router.get(
    "/{case_id}/access",
    response_model=CaseAccessResponse,
    summary="Your effective permissions on this case (mirrors enforced rules)",
)
def get_my_case_access(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseAccessResponse:
    """
    Powers the "Your Access" card. Every flag is computed from the SAME helper
    rules the operative endpoints enforce — nothing is derived from the role
    name alone and nothing is hardcoded client-side.
    """
    case = get_authorized_case(case_id, current_user, db)  # 404 if unauthorized
    member = db.scalar(
        select(CaseMember).where(
            CaseMember.case_id == case.id, CaseMember.user_id == current_user.id
        )
    )
    can_manage = user_can_manage_case(current_user, case)
    # "Case access implies write" is the documented upload rule (upload and
    # version endpoints authorize through the same case-access dependency);
    # integrity verification likewise requires only authorized document access.
    can_access = True
    return CaseAccessResponse(
        role=current_user.role.name,
        case_role=member.role_in_case if member else None,
        can_read=can_access,
        can_upload=can_access,
        can_create_version=can_access,
        can_verify_integrity=can_access,
        can_delete_documents=can_manage,
        can_manage_case=can_manage,
        can_administer=current_user.role.name == "ADMIN",
    )


@router.put(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Update a case (ADMIN, creator, or assigned IO)",
)
def update_case(
    case_id: UUID,
    payload: CaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    case = get_authorized_case(case_id, current_user, db)
    if not user_can_manage_case(current_user, case):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions to modify this case",
        )

    data = payload.model_dump(exclude_unset=True)
    if "assigned_io_id" in data:
        new_io_id = data.pop("assigned_io_id")
        if new_io_id is not None:
            new_io = db.get(User, new_io_id)
            if new_io is None or new_io.role.name != "INVESTIGATING_OFFICER":
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "assigned_io_id must reference an existing investigating officer",
                )
            # Keep membership consistent with the assignment.
            existing = db.scalar(
                select(CaseMember).where(
                    CaseMember.case_id == case.id,
                    CaseMember.user_id == new_io.id,
                )
            )
            if existing is None:
                db.add(
                    CaseMember(
                        case_id=case.id,
                        user_id=new_io.id,
                        role_in_case="INVESTIGATING_OFFICER",
                    )
                )
        case.assigned_io_id = new_io_id

    for field, value in data.items():
        setattr(case, field, value)

    log_audit(
        db,
        AuditAction.CASE_UPDATED,
        actor=current_user,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"updated_fields": sorted(data.keys())},
    )

    db.commit()
    db.refresh(case)
    return _case_detail(case, current_user, db)


@router.delete(
    "/{case_id}",
    response_model=MessageResponse,
    summary="Delete a case (ADMIN only)",
)
def delete_case(
    case_id: UUID,
    request: Request,
    _current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    log_audit(
        db,
        AuditAction.CASE_DELETED,
        actor=_current_user,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"case_number": case.case_number, "title": case.title},
    )
    db.delete(case)  # members removed via cascade
    db.commit()
    return MessageResponse(message=f"Case {case.case_number} deleted")


@router.post(
    "/{case_id}/members",
    response_model=CaseMemberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a case member (ADMIN, creator, or assigned IO)",
)
def add_case_member(
    case_id: UUID,
    payload: CaseMemberAdd,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseMemberOut:
    case = get_authorized_case(case_id, current_user, db)
    if not user_can_manage_case(current_user, case):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions to manage case members",
        )

    if payload.user_id is not None:
        target = db.get(User, payload.user_id)
    elif payload.email is not None:
        target = db.scalar(select(User).where(User.email == payload.email.lower()))
    else:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide either user_id or email"
        )
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    duplicate = db.scalar(
        select(CaseMember).where(
            CaseMember.case_id == case.id, CaseMember.user_id == target.id
        )
    )
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already a case member")

    membership = CaseMember(
        case_id=case.id,
        user_id=target.id,
        role_in_case=payload.role_in_case or target.role.name,
    )
    db.add(membership)
    log_audit(
        db,
        AuditAction.CASE_MEMBER_ADDED,
        actor=current_user,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"added_user_id": str(target.id), "role_in_case": membership.role_in_case},
    )
    db.commit()
    db.refresh(membership)
    return CaseMemberOut(
        id=membership.id,
        user_id=membership.user_id,
        username=target.username,
        full_name=target.full_name,
        role_in_case=membership.role_in_case,
        joined_at=membership.joined_at,
    )


@router.delete(
    "/{case_id}/members/{user_id}",
    response_model=MessageResponse,
    summary="Remove a case member (ADMIN, creator, or assigned IO)",
)
def remove_case_member(
    case_id: UUID,
    user_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    case = get_authorized_case(case_id, current_user, db)
    if not user_can_manage_case(current_user, case):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Insufficient permissions to manage case members",
        )

    membership = db.scalar(
        select(CaseMember).where(
            CaseMember.case_id == case.id, CaseMember.user_id == user_id
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membership not found")
    db.delete(membership)
    log_audit(
        db,
        AuditAction.CASE_MEMBER_REMOVED,
        actor=current_user,
        entity_type="CASE",
        entity_id=case.id,
        case_id=case.id,
        ip_address=client_ip(request),
        data={"removed_user_id": str(user_id)},
    )
    db.commit()
    return MessageResponse(message="Member removed from case")
