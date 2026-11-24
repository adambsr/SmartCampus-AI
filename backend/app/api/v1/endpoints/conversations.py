from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.core.errors import AppError
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    VisitorTextMessageCreate,
)
from app.schemas.error import ErrorResponse
from app.services import conversations as service
from app.services import visitor_sessions


router = APIRouter(responses=ERROR_RESPONSES)
bearer = HTTPBearer(
    auto_error=False,
    scheme_name="visitorBearer",
    description="A visitor-session JWT; account JWTs are not accepted.",
)
AUTH_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Visitor Bearer token required or invalid"},
    403: {"model": ErrorResponse, "description": "Visitor session ownership mismatch"},
    410: {"model": ErrorResponse, "description": "Visitor session expired"},
}


def _authenticated_session(
    credentials: HTTPAuthorizationCredentials | None,
    db: Connection,
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="AUTHENTICATION_REQUIRED",
            message="A visitor session Bearer token is required.",
            status_code=401,
        )
    return visitor_sessions.get_visitor_session_from_token(
        db, token=credentials.credentials
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201,
    summary="Create a text conversation for the authenticated visitor",
    responses={**AUTH_RESPONSES, 422: ERROR_RESPONSES[422]},
)
def create_conversation(
    body: ConversationCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Connection = Depends(get_db),
) -> dict:
    session = _authenticated_session(credentials, db)
    session_id = session["id"]
    if body.visitor_session_id is not None and body.visitor_session_id != session_id:
        raise AppError(
            code="VISITOR_SESSION_OWNERSHIP_MISMATCH",
            message="The request session ID does not match the Bearer token.",
            status_code=403,
        )
    return service.create_conversation(
        db,
        visitor_session_id=session_id,
        channel=body.channel,
        language=body.language,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Retrieve an owned conversation and its messages",
    responses={**AUTH_RESPONSES, 404: ERROR_RESPONSES[404]},
)
def get_conversation(
    conversation_id: UUID,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Connection = Depends(get_db),
) -> dict:
    session = _authenticated_session(credentials, db)
    return service.get_conversation(
        db, conversation_id=conversation_id, visitor_session_id=session["id"]
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=201,
    summary="Persist a visitor text message",
    description=(
        "Stores the visitor message and returns it. Assistant response generation is not "
        "configured; audio content is not supported."
    ),
    responses={
        **AUTH_RESPONSES,
        404: ERROR_RESPONSES[404],
        409: {"model": ErrorResponse, "description": "Conversation is closed"},
        422: ERROR_RESPONSES[422],
    },
)
def create_message(
    conversation_id: UUID,
    body: VisitorTextMessageCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Connection = Depends(get_db),
) -> dict:
    session = _authenticated_session(credentials, db)
    return service.create_message(
        db,
        conversation_id=conversation_id,
        visitor_session_id=session["id"],
        content=body.content,
        language=body.language,
    )
