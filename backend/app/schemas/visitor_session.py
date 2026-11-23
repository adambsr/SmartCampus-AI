from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


VisitorLanguage = Literal["fr", "tn", "arabizi"]


class VisitorSessionCreate(BaseModel):
    language: VisitorLanguage | None = None
    # Accepted for compatibility with SA-5. Anonymous context is not persisted.
    client_context: dict[str, Any] | None = None


class VisitorSessionRefresh(BaseModel):
    refresh_token: str = Field(min_length=32)


class VisitorSessionResponse(BaseModel):
    id: UUID
    status: Literal["active", "expired"]
    language: VisitorLanguage | None = None
    created_at: datetime
    expires_at: datetime
    access_token: str


class VisitorSessionWithRefreshResponse(VisitorSessionResponse):
    # Proposed SA-5 contract extension; issued only on create/refresh.
    refresh_token: str
