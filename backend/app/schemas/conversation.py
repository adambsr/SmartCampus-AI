from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


VisitorLanguage = Literal["fr", "tn", "arabizi"]
ConversationChannel = Literal["text"]
MessageRole = Literal["user", "assistant", "system"]


class ConversationCreate(BaseModel):
    channel: ConversationChannel
    visitor_session_id: UUID | None = None
    language: VisitorLanguage | None = None


class VisitorTextMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    content_type: Literal["text"]
    language: VisitorLanguage | None = None


class MessageResponse(BaseModel):
    id: UUID
    role: MessageRole
    content: str
    language: VisitorLanguage | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: UUID
    visitor_session_id: UUID
    channel: ConversationChannel
    status: Literal["active", "closed"]
    created_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)
