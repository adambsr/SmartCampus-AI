"""SA-29 ownership and credential revocation without a real database."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.dependencies import require_candidate
from app.db.session import get_db
from app.core.config import Settings
from app.core.errors import AppError
from app.services import conversations, guest_link, visitor_sessions


class Cursor:
    def __init__(self, one=None, rows=None):
        self.one, self.rows = one, rows or []

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.rows


class MemoryDb:
    def __init__(self, now, refresh_token):
        self.lock = RLock()
        self.session_id = uuid4()
        self.conversation_id = uuid4()
        self.session = dict(id=self.session_id, status="active", language="fr", created_at=now,
            last_activity_at=now, idle_expires_at=now + timedelta(minutes=30),
            absolute_expires_at=now + timedelta(hours=24),
            refresh_token_hash=visitor_sessions._refresh_hash(refresh_token), linked_user_id=None)
        self.conversation = dict(id=self.conversation_id, visitor_session_id=self.session_id,
            channel="text", status="active", created_at=now, user_id=None)
        self.messages = [dict(id=uuid4(), role="user", content="Previous message", language="fr", created_at=now)]

    @contextmanager
    def transaction(self):
        with self.lock:
            yield

    def execute(self, sql, params=()):
        q = " ".join(sql.lower().split())
        if q.startswith("select * from visitor_session"):
            return Cursor(self.session.copy() if params[0] == self.session_id else None)
        if q.startswith("select status from visitor_session"):
            return Cursor({"status": self.session["status"]} if params[0] == self.session_id else None)
        if q.startswith("update visitor_session set last_activity_at"):
            self.session.update(last_activity_at=params[0], idle_expires_at=params[1]); return Cursor()
        if q.startswith("update visitor_session set status = 'expired'"):
            self.session["status"] = "expired"; return Cursor()
        if q.startswith("update visitor_session set status = 'linked'"):
            if self.session["status"] != "active": return Cursor()
            self.session.update(linked_user_id=params[0], link_consent_at=params[1], linked_at=params[2],
                                refresh_token_hash=params[3], status="linked")
            return Cursor({"id": self.session_id, "linked_at": params[2]})
        if q.startswith("update conversation set user_id"):
            if self.conversation["user_id"] is None:
                self.conversation["user_id"] = params[0]
                return Cursor(rows=[{"id": self.conversation_id}])
            return Cursor(rows=[])
        if q.startswith("select id, visitor_session_id, channel, status, created_at from conversation"):
            if "where user_id =" in q:
                return Cursor(rows=[self.conversation.copy()] if self.conversation["user_id"] == params[0] else [])
            expected = (params[1] if "where id =" in q else None)
            allowed = self.conversation["id"] == params[0] and self.conversation["user_id"] == expected
            return Cursor(self.conversation.copy() if allowed else None)
        if q.startswith("select id, role, content, language, created_at from conversation_message"):
            return Cursor(rows=list(self.messages))
        if q.startswith("select status from conversation"):
            owner = params[1]
            allowed = params[0] == self.conversation_id and (
                self.conversation["user_id"] == owner if "user_id = %s" in q and "visitor_session_id" not in q
                else self.conversation["visitor_session_id"] == owner and self.conversation["user_id"] is None)
            return Cursor({"status": self.conversation["status"]} if allowed else None)
        if q.startswith("insert into conversation_message"):
            _, _, content, language, created_at = params
            row = dict(id=params[0], role="user", content=content, language=language, created_at=created_at)
            self.messages.append(row)
            return Cursor(row)
        raise AssertionError(q)


@pytest.fixture
def setup(monkeypatch):
    now = datetime.now(timezone.utc)
    refresh = "private-visitor-refresh-token-0123456789"
    db = MemoryDb(now, refresh)
    settings = Settings(_env_file=None, visitor_session_secret=SecretStr("visitor-test-secret-0123456789abcdef"))
    monkeypatch.setattr(visitor_sessions, "get_settings", lambda: settings)
    token = visitor_sessions._issue_access_token(db.session_id, now, settings)
    return db, token, refresh, now, settings


def test_transfer_preserves_history_and_revokes_both_visitor_credentials(setup):
    db, token, refresh, now, settings = setup
    old_message_id = db.messages[0]["id"]
    result = guest_link.link_session(db, session_id=db.session_id, visitor_token=token, user_id=7)
    assert result["conversation_count"] == 1
    assert db.conversation["id"] == db.conversation_id
    assert db.conversation["user_id"] == 7
    assert db.session["link_consent_at"] is not None
    assert db.messages[0]["id"] == old_message_id
    history = guest_link.get_candidate_conversation(db, user_id=7, conversation_id=db.conversation_id)
    assert history["messages"][0]["content"] == "Previous message"
    guest_link.add_candidate_message(db, user_id=7, conversation_id=db.conversation_id, content="Continue", language="fr")
    assert len(db.messages) == 2
    with pytest.raises(AppError) as other:
        guest_link.get_candidate_conversation(db, user_id=8, conversation_id=db.conversation_id)
    assert other.value.status_code == 404
    with pytest.raises(AppError) as other_write:
        guest_link.add_candidate_message(db, user_id=8, conversation_id=db.conversation_id, content="No", language="fr")
    assert other_write.value.status_code == 404
    with pytest.raises(AppError) as old_access:
        visitor_sessions.get_visitor_session(db, session_id=db.session_id, token=token, now=now, settings=settings)
    assert old_access.value.status_code == 410
    with pytest.raises(AppError) as old_refresh:
        visitor_sessions.refresh_visitor_session(db, session_id=db.session_id, refresh_token=refresh, now=now, settings=settings)
    assert old_refresh.value.status_code == 410


def test_competing_claims_only_transfer_once(setup):
    db, token, _, _, _ = setup
    def claim(user_id):
        try: return guest_link.link_session(db, session_id=db.session_id, visitor_token=token, user_id=user_id)
        except AppError as error: return error
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, [7, 8]))
    assert sum(isinstance(value, dict) for value in results) == 1
    assert db.conversation["user_id"] in (7, 8)
    assert sum(isinstance(value, AppError) for value in results) == 1


def test_expired_session_cannot_be_claimed(setup):
    db, token, _, now, _ = setup
    db.session["idle_expires_at"] = now - timedelta(seconds=1)
    with pytest.raises(AppError) as expired:
        guest_link.link_session(db, session_id=db.session_id, visitor_token=token, user_id=7)
    assert expired.value.status_code == 410
    assert db.conversation["user_id"] is None


def test_guest_message_and_transfer_serialize_without_losing_message(setup):
    db, token, _, now, settings = setup
    def guest_write():
        try:
            with db.transaction():
                visitor_sessions.get_visitor_session(db, session_id=db.session_id, token=token, now=now, settings=settings)
                conversations.create_message(db, conversation_id=db.conversation_id,
                    visitor_session_id=db.session_id, content="Racing message", language="fr")
            return True
        except AppError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        write = pool.submit(guest_write)
        linked = pool.submit(guest_link.link_session, db, session_id=db.session_id, visitor_token=token, user_id=7)
        wrote = write.result()
        linked.result()
    assert db.conversation["user_id"] == 7
    assert (len(db.messages) == 2) == wrote


def test_link_api_requires_explicit_consent_and_visitor_proof(setup):
    db, token, _, _, _ = setup
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            path = f"/api/v1/visitor-sessions/{db.session_id}/link"
            headers = {"X-Visitor-Session-Token": token}
            assert client.post(path, json={"consent": True}, headers=headers).status_code == 401
            assert client.get("/api/v1/candidates/me/conversations").status_code == 401
            app.dependency_overrides[require_candidate] = lambda: {"id": 7, "role": "candidate"}
            assert client.post(path, json={"consent": False}, headers=headers).status_code == 422
            assert client.post(path, json={"consent": True}, headers={"X-Visitor-Session-Token": "bad"}).status_code == 401
            linked = client.post(path, json={"consent": True}, headers=headers)
            assert linked.status_code == 200
            assert linked.json()["conversation_count"] == 1
            assert client.post(path, json={"consent": True}, headers=headers).status_code == 409
            assert len(client.get("/api/v1/candidates/me/conversations").json()["items"]) == 1
            candidate_path = f"/api/v1/candidates/me/conversations/{db.conversation_id}"
            assert client.get(candidate_path).json()["messages"][0]["content"] == "Previous message"
            assert client.post(f"{candidate_path}/messages", json={"content": "New", "content_type": "text"}).status_code == 201
            visitor_headers = {"Authorization": f"Bearer {token}"}
            assert client.post("/api/v1/conversations", json={"channel": "text"}, headers=visitor_headers).status_code == 410
            assert client.get(f"/api/v1/conversations/{db.conversation_id}", headers=visitor_headers).status_code == 410
            assert client.post(f"/api/v1/conversations/{db.conversation_id}/messages",
                json={"content": "Old visitor", "content_type": "text"}, headers=visitor_headers).status_code == 410
    finally:
        app.dependency_overrides.clear()
