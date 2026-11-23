"""Visitor-owned conversations and text messages (SA-26)."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from psycopg import Connection

from app.core.errors import AppError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _not_found() -> AppError:
    return AppError(
        code="CONVERSATION_NOT_FOUND",
        message="The conversation was not found.",
        status_code=404,
    )


def create_conversation(
    conn: Connection,
    *,
    visitor_session_id: UUID,
    channel: str,
    language: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    conversation_id = uuid4()
    row = conn.execute(
        """INSERT INTO conversation
           (id, visitor_session_id, channel, language, created_at)
           VALUES (%s, %s, %s, %s, %s)
           RETURNING id, visitor_session_id, channel, status, created_at""",
        (conversation_id, visitor_session_id, channel, language, now or _now()),
    ).fetchone()
    return {**row, "messages": []}


def get_conversation(
    conn: Connection, *, conversation_id: UUID, visitor_session_id: UUID
) -> dict[str, Any]:
    row = conn.execute(
        """SELECT id, visitor_session_id, channel, status, created_at
           FROM conversation
           WHERE id = %s AND visitor_session_id = %s""",
        (conversation_id, visitor_session_id),
    ).fetchone()
    if row is None:
        raise _not_found()

    messages = conn.execute(
        """SELECT id, role, content, language, created_at
           FROM conversation_message
           WHERE conversation_id = %s
           ORDER BY created_at ASC, id ASC""",
        (conversation_id,),
    ).fetchall()
    return {**row, "messages": messages}


def create_message(
    conn: Connection,
    *,
    conversation_id: UUID,
    visitor_session_id: UUID,
    content: str,
    language: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    created_at = now or _now()
    with conn.transaction():
        conversation = conn.execute(
            """SELECT status FROM conversation
               WHERE id = %s AND visitor_session_id = %s
               FOR UPDATE""",
            (conversation_id, visitor_session_id),
        ).fetchone()
        if conversation is None:
            raise _not_found()
        if conversation["status"] != "active":
            raise AppError(
                code="CONVERSATION_CLOSED",
                message="Messages cannot be added to a closed conversation.",
                status_code=409,
            )

        return conn.execute(
            """INSERT INTO conversation_message
               (id, conversation_id, role, content, language, created_at)
               VALUES (%s, %s, 'user', %s, %s, %s)
               RETURNING id, role, content, language, created_at""",
            (uuid4(), conversation_id, content, language, created_at),
        ).fetchone()
