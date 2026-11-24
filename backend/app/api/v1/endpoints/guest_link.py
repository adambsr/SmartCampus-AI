from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from psycopg import Connection
from pydantic import BaseModel, Field

from app.api.v1.dependencies import require_candidate
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.conversation import ConversationResponse, MessageResponse, VisitorTextMessageCreate
from app.services import guest_link

router = APIRouter(responses=ERROR_RESPONSES)


class LinkConsent(BaseModel):
    consent: Literal[True] = Field(description="Transfer all conversations and end visitor access")


class LinkResult(BaseModel):
    session_id: UUID
    linked_at: datetime
    conversation_count: int


class ConversationSummary(BaseModel):
    id: UUID
    visitor_session_id: UUID
    channel: str
    status: str
    created_at: datetime


class ConversationList(BaseModel):
    items: list[ConversationSummary]


@router.post("/visitor-sessions/{session_id}/link", response_model=LinkResult)
def link_visitor_session(
    session_id: UUID, body: LinkConsent,
    visitor_token: str = Header(alias="X-Visitor-Session-Token"),
    account: dict = Depends(require_candidate), db: Connection = Depends(get_db),
) -> dict:
    if body.consent is not True:
        from app.core.errors import AppError
        raise AppError(code="CONSENT_REQUIRED", message="Explicit consent is required.", status_code=422)
    return guest_link.link_session(db, session_id=session_id, visitor_token=visitor_token, user_id=account["id"])


@router.get("/candidates/me/conversations", response_model=ConversationList)
def list_conversations(account: dict = Depends(require_candidate), db: Connection = Depends(get_db)) -> dict:
    return guest_link.list_candidate_conversations(db, user_id=account["id"])


@router.get("/candidates/me/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: UUID, account: dict = Depends(require_candidate), db: Connection = Depends(get_db),
) -> dict:
    return guest_link.get_candidate_conversation(db, user_id=account["id"], conversation_id=conversation_id)


@router.post("/candidates/me/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
def add_message(
    conversation_id: UUID, body: VisitorTextMessageCreate,
    account: dict = Depends(require_candidate), db: Connection = Depends(get_db),
) -> dict:
    return guest_link.add_candidate_message(
        db, user_id=account["id"], conversation_id=conversation_id,
        content=body.content, language=body.language,
    )
