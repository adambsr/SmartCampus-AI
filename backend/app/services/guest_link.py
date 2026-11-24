"""Permanent, consented transfer of an entire visitor session (SA-29)."""
import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID, uuid4

from psycopg import Connection

from app.core.errors import AppError
from app.services import visitor_sessions


def link_session(conn: Connection, *, session_id: UUID, visitor_token: str, user_id: int) -> dict:
    now = datetime.now(timezone.utc)
    with conn.transaction():
        # SA-25 validates the token and locks the session. The outer transaction
        # retains that lock through the ownership update and credential revocation.
        try:
            visitor_sessions.get_visitor_session(conn, session_id=session_id, token=visitor_token, now=now)
        except AppError as exc:
            if exc.code == "VISITOR_SESSION_EXPIRED":
                row = conn.execute("SELECT status FROM visitor_session WHERE id = %s FOR UPDATE", (session_id,)).fetchone()
                if row and row["status"] == "linked":
                    raise AppError(code="VISITOR_SESSION_LINK_CONFLICT", message="The session is already linked.", status_code=409) from exc
            raise
        changed = conn.execute(
            """UPDATE visitor_session SET status = 'linked', linked_user_id = %s,
                   link_consent_at = %s, linked_at = %s, refresh_token_hash = %s
               WHERE id = %s AND status = 'active' RETURNING id, linked_at""",
            (user_id, now, now, hashlib.sha256(secrets.token_bytes(32)).hexdigest(), session_id),
        ).fetchone()
        if changed is None:
            raise AppError(code="VISITOR_SESSION_LINK_CONFLICT", message="The session cannot be linked.", status_code=409)
        rows = conn.execute(
            """UPDATE conversation SET user_id = %s
               WHERE visitor_session_id = %s AND user_id IS NULL RETURNING id""",
            (user_id, session_id),
        ).fetchall()
        return {"session_id": changed["id"], "linked_at": changed["linked_at"], "conversation_count": len(rows)}


def list_candidate_conversations(conn: Connection, *, user_id: int) -> dict:
    rows = conn.execute(
        """SELECT id, visitor_session_id, channel, status, created_at
           FROM conversation WHERE user_id = %s ORDER BY created_at DESC, id DESC""",
        (user_id,),
    ).fetchall()
    return {"items": rows}


def get_candidate_conversation(conn: Connection, *, user_id: int, conversation_id: UUID) -> dict:
    row = conn.execute(
        """SELECT id, visitor_session_id, channel, status, created_at
           FROM conversation WHERE id = %s AND user_id = %s""",
        (conversation_id, user_id),
    ).fetchone()
    if row is None:
        raise AppError(code="CONVERSATION_NOT_FOUND", message="The conversation was not found.", status_code=404)
    messages = conn.execute(
        """SELECT id, role, content, language, created_at FROM conversation_message
           WHERE conversation_id = %s ORDER BY created_at ASC, id ASC""",
        (conversation_id,),
    ).fetchall()
    return {**row, "messages": messages}


def add_candidate_message(
    conn: Connection, *, user_id: int, conversation_id: UUID, content: str, language: str | None,
) -> dict:
    with conn.transaction():
        row = conn.execute(
            """SELECT status FROM conversation WHERE id = %s AND user_id = %s FOR UPDATE""",
            (conversation_id, user_id),
        ).fetchone()
        if row is None:
            raise AppError(code="CONVERSATION_NOT_FOUND", message="The conversation was not found.", status_code=404)
        if row["status"] != "active":
            raise AppError(code="CONVERSATION_CLOSED", message="Messages cannot be added to a closed conversation.", status_code=409)
        return conn.execute(
            """INSERT INTO conversation_message (id, conversation_id, role, content, language, created_at)
               VALUES (%s, %s, 'user', %s, %s, %s)
               RETURNING id, role, content, language, created_at""",
            (uuid4(), conversation_id, content, language, datetime.now(timezone.utc)),
        ).fetchone()
