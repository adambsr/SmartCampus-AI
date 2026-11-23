import ipaddress
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.core.errors import AppError
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.error import ErrorResponse
from app.schemas.visitor_session import (
    VisitorSessionCreate,
    VisitorSessionRefresh,
    VisitorSessionResponse,
    VisitorSessionWithRefreshResponse,
)
from app.services import visitor_sessions as service

router = APIRouter(responses=ERROR_RESPONSES)
bearer = HTTPBearer(auto_error=False)
SESSION_ERRORS = {
    401: {"model": ErrorResponse, "description": "Invalid or expired session credential"},
    403: {"model": ErrorResponse, "description": "Session ownership mismatch"},
    410: {"model": ErrorResponse, "description": "Visitor session expired"},
    429: {"model": ErrorResponse, "description": "Usage limit reached"},
    503: {"model": ErrorResponse, "description": "Visitor session signing is not configured"},
}


@router.post(
    "/visitor-sessions",
    response_model=VisitorSessionWithRefreshResponse,
    status_code=201,
    summary="Create an anonymous visitor session",
    description=(
        "Creates a temporary visitor session. The refresh token in this response is a "
        "proposed SA-5 contract extension. Proposed defaults: 30 minutes idle, 24 hours "
        "absolute lifetime, and five creations per client IP per hour."
    ),
    responses={**SESSION_ERRORS},
)
def create_visitor_session(
    request: Request,
    body: VisitorSessionCreate | None = None,
    db: Connection = Depends(get_db),
) -> dict:
    client = request.client
    if client is None or not client.host:
        raise AppError(
            code="CLIENT_ADDRESS_UNAVAILABLE",
            message="A trusted connection peer address is required to create a visitor session.",
            status_code=400,
        )
    try:
        client_ip = str(ipaddress.ip_address(client.host))
    except ValueError as exc:
        raise AppError(
            code="CLIENT_ADDRESS_UNAVAILABLE",
            message="A trusted connection peer IP address is required to create a visitor session.",
            status_code=400,
        ) from exc
    return service.create_visitor_session(
        db,
        client_ip=client_ip,
        language=body.language if body else None,
    )


@router.get(
    "/visitor-sessions/{session_id}",
    response_model=VisitorSessionResponse,
    summary="Get the status of an owned visitor session",
    description="Requires a Bearer JWT whose session claim matches the requested session ID.",
    responses={404: ERROR_RESPONSES[404], **SESSION_ERRORS},
)
def get_visitor_session(
    session_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Connection = Depends(get_db),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="AUTHENTICATION_REQUIRED",
            message="A visitor session Bearer token is required.",
            status_code=401,
        )
    return service.get_visitor_session(db, session_id=session_id, token=credentials.credentials)


@router.post(
    "/visitor-sessions/{session_id}/refresh",
    response_model=VisitorSessionWithRefreshResponse,
    summary="Refresh visitor session credentials (proposed SA-5 extension)",
    description=(
        "Proposed SA-5 contract extension: submit the current refresh token to rotate it "
        "and receive a new 15-minute access JWT and refresh token."
    ),
    responses={404: ERROR_RESPONSES[404], **SESSION_ERRORS},
)
def refresh_visitor_session(
    session_id: UUID,
    body: VisitorSessionRefresh,
    db: Connection = Depends(get_db),
) -> dict:
    return service.refresh_visitor_session(
        db, session_id=session_id, refresh_token=body.refresh_token
    )
