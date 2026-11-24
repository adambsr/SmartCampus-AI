from fastapi import APIRouter, Depends
from psycopg import Connection

from app.api.v1.dependencies import get_current_account, require_candidate
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.account import CandidateApplicationsResponse, CandidateProfileResponse
from app.schemas.error import ErrorResponse
from app.services import accounts

router = APIRouter(prefix="/candidates", responses=ERROR_RESPONSES)
PRIVATE_ERRORS = {
    401: {"model": ErrorResponse, "description": "Account authentication required"},
    403: {"model": ErrorResponse, "description": "Role or resource scope denied"},
}


@router.get("/me", response_model=CandidateProfileResponse, responses=PRIVATE_ERRORS,
            summary="Read the signed-in candidate profile")
def my_profile(
    account: dict = Depends(require_candidate), db: Connection = Depends(get_db),
) -> dict:
    return accounts.get_candidate_profile(db, candidate_id=account["id"], actor=account)


@router.get("/me/applications", response_model=CandidateApplicationsResponse,
            responses=PRIVATE_ERRORS, summary="Read the signed-in candidate application statuses")
def my_applications(
    account: dict = Depends(require_candidate), db: Connection = Depends(get_db),
) -> dict:
    return accounts.get_candidate_applications(db, user_id=account["id"])


@router.get("/{candidate_id}", response_model=CandidateProfileResponse,
            responses=PRIVATE_ERRORS, summary="Read an authorized candidate dossier")
def candidate_profile(
    candidate_id: int, account: dict = Depends(get_current_account),
    db: Connection = Depends(get_db),
) -> dict:
    return accounts.get_candidate_profile(db, candidate_id=candidate_id, actor=account)
