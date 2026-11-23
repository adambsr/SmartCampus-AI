"""SA-26 conversation API tests using an in-memory fake connection."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.db.session import get_db
from app.main import app
from app.services import conversations, visitor_sessions


class Cursor:
    def __init__(self, row: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None):
        self.row = row
        self.rows = rows or []

    def fetchone(self) -> dict[str, Any] | None:
        return self.row

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class FakeConnection:
    def __init__(self, now: datetime):
        self.now = now
        self.sessions: dict[str, dict[str, Any]] = {}
        self.rate_rows: list[tuple[str, datetime]] = []
        self.conversation_rows: dict[str, dict[str, Any]] = {}
        self.message_rows: list[dict[str, Any]] = []

    @contextmanager
    def transaction(self):
        yield

    def execute(self, sql: str, params: tuple = ()) -> Cursor:
        query = " ".join(sql.lower().split())
        if query.startswith("select pg_advisory_xact_lock"):
            return Cursor()
        if query.startswith("delete from visitor_session_creation"):
            cutoff = params[0]
            self.rate_rows = [(ip_hash, at) for ip_hash, at in self.rate_rows if at > cutoff]
            return Cursor()
        if query.startswith("select count(*) as count from visitor_session_creation"):
            ip_hash, cutoff = params
            count = sum(1 for value, at in self.rate_rows if value == ip_hash and at > cutoff)
            return Cursor({"count": count})
        if query.startswith("insert into visitor_session ("):
            (
                session_id,
                language,
                created_at,
                last_activity_at,
                idle_expires_at,
                absolute_expires_at,
                refresh_token_hash,
            ) = params
            row = {
                "id": session_id,
                "status": "active",
                "language": language,
                "created_at": created_at,
                "last_activity_at": last_activity_at,
                "idle_expires_at": idle_expires_at,
                "absolute_expires_at": absolute_expires_at,
                "refresh_token_hash": refresh_token_hash,
            }
            self.sessions[str(session_id)] = row
            return Cursor()
        if query.startswith("insert into visitor_session_creation"):
            self.rate_rows.append((params[0], params[1]))
            return Cursor()
        if query.startswith("select * from visitor_session"):
            return Cursor(self.sessions.get(str(params[0])))
        if query.startswith("update visitor_session set status = 'expired'"):
            row = self.sessions.get(str(params[0]))
            if row is not None:
                row["status"] = "expired"
            return Cursor()
        if query.startswith("update visitor_session set last_activity_at = %s"):
            now, idle_expires_at, session_id = params
            row = self.sessions[str(session_id)]
            row["last_activity_at"] = now
            row["idle_expires_at"] = idle_expires_at
            return Cursor()
        if query.startswith("insert into conversation ("):
            conversation_id, session_id, channel, language, created_at = params
            row = {
                "id": conversation_id,
                "visitor_session_id": session_id,
                "channel": channel,
                "language": language,
                "status": "active",
                "created_at": created_at,
            }
            self.conversation_rows[str(conversation_id)] = row
            return Cursor(row)
        if query.startswith("select status from conversation"):
            conversation_id, session_id = params
            row = self.conversation_rows.get(str(conversation_id))
            if row is None or row["visitor_session_id"] != session_id:
                return Cursor()
            return Cursor({"status": row["status"]})
        if query.startswith("select id, visitor_session_id, channel, status, created_at from conversation"):
            conversation_id, session_id = params
            row = self.conversation_rows.get(str(conversation_id))
            if row is None or row["visitor_session_id"] != session_id:
                return Cursor()
            return Cursor(row)
        if query.startswith("select id, role, content, language, created_at from conversation_message"):
            conversation_id = params[0]
            rows = [
                row for row in self.message_rows if row["conversation_id"] == conversation_id
            ]
            rows.sort(key=lambda row: (row["created_at"], str(row["id"])))
            return Cursor(rows=rows)
        if query.startswith("insert into conversation_message"):
            message_id, conversation_id, content, language, created_at = params
            row = {
                "id": message_id,
                "role": "user",
                "content": content,
                "language": language,
                "created_at": created_at,
                "conversation_id": conversation_id,
            }
            self.message_rows.append(row)
            return Cursor({key: value for key, value in row.items() if key != "conversation_id"})
        raise AssertionError(f"Unexpected SQL in fake connection: {query}")


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    now = [datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)]
    database = FakeConnection(now[0])
    settings = Settings(
        visitor_session_secret=SecretStr("unit-test-secret-value-0123456789abcdef")
    )
    monkeypatch.setattr(visitor_sessions, "get_settings", lambda: settings)
    monkeypatch.setattr(visitor_sessions, "_now", lambda: now[0])
    monkeypatch.setattr(conversations, "_now", lambda: now[0])
    app.dependency_overrides[get_db] = lambda: database
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        yield client, database, now
    app.dependency_overrides.clear()


def _new_session(client: TestClient) -> dict[str, Any]:
    response = client.post("/api/v1/visitor-sessions", json={"language": "fr"})
    assert response.status_code == 201
    return response.json()


def _headers(session: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _new_conversation(client: TestClient, session: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/conversations",
        json={"channel": "text", "language": "tn"},
        headers=_headers(session),
    )
    assert response.status_code == 201
    return response.json()


def test_create_conversation_requires_valid_visitor_token_and_persists_language(api) -> None:
    client, database, _ = api
    missing = client.post("/api/v1/conversations", json={"channel": "text"})
    invalid = client.post(
        "/api/v1/conversations",
        json={"channel": "text"},
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    session = _new_session(client)
    created = client.post(
        "/api/v1/conversations",
        json={"channel": "text", "language": "tn"},
        headers=_headers(session),
    )

    assert missing.status_code == invalid.status_code == 401
    assert created.status_code == 201
    body = created.json()
    assert body["channel"] == "text"
    assert body["status"] == "active"
    assert body["visitor_session_id"] == session["id"]
    assert body["messages"] == []
    assert database.conversation_rows[body["id"]]["visitor_session_id"] == UUID(session["id"])
    assert database.conversation_rows[body["id"]]["language"] == "tn"


def test_create_conversation_rejects_mismatched_session_id(api) -> None:
    client, _, _ = api
    session = _new_session(client)
    response = client.post(
        "/api/v1/conversations",
        json={"channel": "text", "visitor_session_id": "00000000-0000-0000-0000-000000000001"},
        headers=_headers(session),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "VISITOR_SESSION_OWNERSHIP_MISMATCH"


def test_expired_visitor_session_cannot_create_conversation(api) -> None:
    client, _, now = api
    session = _new_session(client)
    now[0] += timedelta(minutes=31)
    response = client.post(
        "/api/v1/conversations", json={"channel": "text"}, headers=_headers(session)
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "VISITOR_SESSION_EXPIRED"


@pytest.mark.parametrize(
    "body",
    [
        {"channel": "audio"},
        {"channel": "video"},
        {"channel": "text", "language": "en"},
    ],
)
def test_conversation_creation_rejects_unsupported_channel_or_language(api, body) -> None:
    client, _, _ = api
    session = _new_session(client)
    response = client.post("/api/v1/conversations", json=body, headers=_headers(session))
    assert response.status_code == 422


def test_owner_can_retrieve_history_and_other_session_gets_not_found(api) -> None:
    client, _, now = api
    owner = _new_session(client)
    other = _new_session(client)
    conversation = _new_conversation(client, owner)
    first = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "first", "content_type": "text", "language": "fr"},
        headers=_headers(owner),
    )
    now[0] += timedelta(seconds=1)
    second = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "second", "content_type": "text"},
        headers=_headers(owner),
    )

    assert first.status_code == second.status_code == 201
    assert first.json()["role"] == second.json()["role"] == "user"
    assert first.json()["language"] == "fr"
    assert "assistant_message" not in second.json()
    retrieved = client.get(
        f"/api/v1/conversations/{conversation['id']}", headers=_headers(owner)
    )
    hidden = client.get(
        f"/api/v1/conversations/{conversation['id']}", headers=_headers(other)
    )
    blocked_message = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "should stay private", "content_type": "text"},
        headers=_headers(other),
    )

    assert retrieved.status_code == 200
    assert [message["content"] for message in retrieved.json()["messages"]] == [
        "first",
        "second",
    ]
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"
    assert blocked_message.status_code == 404


def test_message_creation_requires_token_and_rejects_audio_or_invalid_body(api) -> None:
    client, _, _ = api
    session = _new_session(client)
    conversation = _new_conversation(client, session)
    path = f"/api/v1/conversations/{conversation['id']}/messages"
    missing = client.post(path, json={"content": "hello", "content_type": "text"})
    audio = client.post(
        path,
        json={"content": "", "content_type": "audio_reference", "audio_reference": "00000000-0000-0000-0000-000000000001"},
        headers=_headers(session),
    )
    empty = client.post(
        path,
        json={"content": "", "content_type": "text"},
        headers=_headers(session),
    )

    assert missing.status_code == 401
    assert audio.status_code == empty.status_code == 422


def test_message_creation_rejects_audio_reference_extra_on_text_message(api) -> None:
    client, _, _ = api
    session = _new_session(client)
    conversation = _new_conversation(client, session)
    response = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={
            "content": "hello",
            "content_type": "text",
            "audio_reference": "00000000-0000-0000-0000-000000000001",
        },
        headers=_headers(session),
    )
    assert response.status_code == 422


def test_message_creation_rejects_closed_conversation(api) -> None:
    client, database, _ = api
    session = _new_session(client)
    conversation = _new_conversation(client, session)
    database.conversation_rows[conversation["id"]]["status"] = "closed"
    response = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "hello", "content_type": "text"},
        headers=_headers(session),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONVERSATION_CLOSED"


def test_invalid_or_unowned_conversation_cannot_receive_message(api) -> None:
    client, _, _ = api
    session = _new_session(client)
    absent_id = "00000000-0000-0000-0000-000000000001"
    response = client.post(
        f"/api/v1/conversations/{absent_id}/messages",
        json={"content": "hello", "content_type": "text"},
        headers=_headers(session),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_invalid_conversation_uuid_is_rejected(api) -> None:
    client, _, _ = api
    session = _new_session(client)
    response = client.get("/api/v1/conversations/not-a-uuid", headers=_headers(session))
    assert response.status_code == 422


def test_openapi_describes_text_only_message_response(api) -> None:
    client, _, _ = api
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    create = paths["/api/v1/conversations"]["post"]
    message = paths["/api/v1/conversations/{conversation_id}/messages"]["post"]
    components = schema["components"]["schemas"]
    assert components["ConversationCreate"]["properties"]["channel"]["const"] == "text"
    assert (
        components["VisitorTextMessageCreate"]["properties"]["content_type"]["const"]
        == "text"
    )
    assert create["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ConversationCreate"
    )
    assert message["responses"]["201"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/MessageResponse")


def test_conversation_schema_declares_owner_and_text_only_constraints() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sql = (repo_root / "database" / "schema" / "conversations_schema.sql").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(sql.lower().split())
    assert "references visitor_session(id) on delete restrict" in normalized
    assert "check (channel = 'text')" in normalized
    assert "check (role in ('user', 'assistant', 'system'))" in normalized
    assert "on conversation_message (conversation_id, created_at, id)" in normalized
