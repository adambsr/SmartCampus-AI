from fastapi import APIRouter, Depends, Query, Response
from psycopg import Connection

from app.api.v1.dependencies import require_admin
from app.core.config import get_settings
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.account import (
    AccountListResponse, AccountPublic, AccountUpdateRequest, InvitationResponse,
    StaffCreateRequest,
)
from app.schemas.error import ErrorResponse
from app.services import accounts

router = APIRouter(prefix="/admin/users", responses=ERROR_RESPONSES)
ADMIN_ERRORS = {
    401: {"model": ErrorResponse, "description": "Account authentication required"},
    403: {"model": ErrorResponse, "description": "Administrator role required"},
    409: {"model": ErrorResponse, "description": "Account state conflict"},
}


@router.get("", response_model=AccountListResponse, responses=ADMIN_ERRORS,
            summary="List user accounts for administration")
def list_users(
    limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin), db: Connection = Depends(get_db),
) -> dict:
    return accounts.list_users(db, limit=limit, offset=offset)


@router.post("", response_model=AccountPublic, status_code=201, responses=ADMIN_ERRORS,
             summary="Create a pending staff account")
def create_staff(
    body: StaffCreateRequest, _: dict = Depends(require_admin),
    db: Connection = Depends(get_db),
) -> dict:
    return accounts.create_staff(
        db, email=str(body.email), full_name=body.full_name,
        role=body.role, institution_id=body.institution_id,
    )


@router.patch("/{user_id}", response_model=AccountPublic, responses=ADMIN_ERRORS,
              summary="Change a staff role, institution, or account status")
def update_user(
    user_id: int, body: AccountUpdateRequest,
    admin: dict = Depends(require_admin), db: Connection = Depends(get_db),
) -> dict:
    return accounts.update_user(
        db, actor_id=admin["id"], target_id=user_id,
        fields=body.model_dump(exclude_unset=True),
    )


@router.post("/{user_id}/invitations", response_model=InvitationResponse,
             status_code=201, responses=ADMIN_ERRORS,
             summary="Issue a one-time first-password invitation")
def invite_user(
    user_id: int, response: Response, admin: dict = Depends(require_admin),
    db: Connection = Depends(get_db),
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return accounts.issue_invitation(
        db, actor_id=admin["id"], target_id=user_id, settings=get_settings()
    )
