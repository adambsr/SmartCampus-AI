"""SA-28 API/security tests; never connect to a database."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.v1 import dependencies
from app.api.v1.endpoints import auth as auth_endpoint
from app.api.v1.endpoints import admin_users as admin_endpoint
from app.core.account_security import (
    decode_access_token, hash_password, issue_access_token, token_hash, verify_password,
)
from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import get_db
from app.main import app
from app.services import accounts, visitor_sessions


class Cursor:
    def __init__(self, row: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.users: dict[int, dict[str, Any]] = {}
        self.profiles: set[int] = set()
        self.sessions: dict[UUID, dict[str, Any]] = {}
        self.invitations: dict[UUID, dict[str, Any]] = {}
        self.attempts: list[dict[str, Any]] = []
        self.audit: list[tuple] = []
        self.next_user_id = 1

    def user(self, email: str, role: str, password: str | None, institution_id: int | None = None):
        user_id = self.next_user_id
        self.next_user_id += 1
        row = {
            "id": user_id, "email": email, "full_name": email.split("@")[0],
            "role": role, "institution_id": institution_id, "is_active": True,
            "password_hash": hash_password(password) if password else None,
        }
        self.users[user_id] = row
        if role == "candidate":
            self.profiles.add(user_id)
        return row

    @contextmanager
    def transaction(self):
        yield

    def execute(self, sql: str, params: tuple = ()) -> Cursor:
        q = " ".join(sql.lower().split())
        if q.startswith("select pg_advisory_xact_lock"):
            return Cursor()
        if q.startswith("delete from account_auth_attempt"):
            self.attempts = [a for a in self.attempts if a["created_at"] > params[0]]
            return Cursor()
        if q.startswith("select count(*) as count from account_auth_attempt"):
            scope, since, email_key, ip_key = params
            count = sum(1 for a in self.attempts if a["scope"] == scope and a["created_at"] > since
                        and (a["identity_hmac"] == email_key or a["ip_hmac"] == ip_key))
            return Cursor({"count": count})
        if q.startswith("insert into account_auth_attempt"):
            scope, email_key, ip_key, at = params
            self.attempts.append({"scope": scope, "identity_hmac": email_key, "ip_hmac": ip_key, "created_at": at})
            return Cursor()
        if q.startswith("insert into app_user"):
            if "'candidate'" in q:
                email, password_hash, name = params
                role, institution_id, active = "candidate", None, True
            else:
                email, name, role, institution_id = params
                password_hash, active = None, False
            user_id = self.next_user_id
            self.next_user_id += 1
            row = {"id": user_id, "email": email, "full_name": name, "role": role,
                   "institution_id": institution_id, "is_active": active, "password_hash": password_hash}
            self.users[user_id] = row
            return Cursor(row)
        if q.startswith("insert into candidate_profile"):
            self.profiles.add(params[0])
            return Cursor()
        if q.startswith("insert into account_session"):
            sid, user_id, hashed, created_at, expires_at = params
            self.sessions[sid] = {"id": sid, "user_id": user_id, "refresh_token_hash": hashed,
                                  "created_at": created_at, "expires_at": expires_at, "revoked_at": None}
            return Cursor()
        if q.startswith("select id, email, full_name") and "from app_user where lower(email)" in q:
            row = next((u for u in self.users.values() if u["email"].lower() == params[0]), None)
            return Cursor(row)
        if q.startswith("update app_user set last_login_at"):
            at, hashed, user_id = params
            self.users[user_id].update(last_login_at=at, password_hash=hashed)
            return Cursor()
        if "from account_session s join app_user u" in q:
            sid = params[0]
            session = self.sessions.get(sid)
            user = self.users.get(session["user_id"]) if session else None
            if len(params) == 2 and user and user["id"] != params[1]:
                user = None
            return Cursor({**user, **{k: session[k] for k in ("refresh_token_hash", "expires_at", "revoked_at")}} if user else None)
        if q.startswith("update account_session set refresh_token_hash"):
            hashed, sid = params
            self.sessions[sid]["refresh_token_hash"] = hashed
            return Cursor()
        if q.startswith("select refresh_token_hash from account_session"):
            return Cursor(self.sessions.get(params[0]))
        if q.startswith("update account_session set revoked_at"):
            if "where user_id" in q:
                at, user_id = params
                for session in self.sessions.values():
                    if session["user_id"] == user_id and session["revoked_at"] is None:
                        session["revoked_at"] = at
            else:
                at, sid, *rest = params
                session = self.sessions.get(sid)
                if session and (not rest or session["user_id"] == rest[0]):
                    session["revoked_at"] = session["revoked_at"] or at
            return Cursor()
        if q.startswith("select id, email, full_name") and "from app_user where id" in q:
            return Cursor(self.users.get(params[0]))
        if q.startswith("select count(*) as count from app_user"):
            return Cursor({"count": sum(1 for u in self.users.values() if u["role"] == "admin"
                                  and u["is_active"] and u["password_hash"] is not None)})
        if q.startswith("update app_user set role"):
            role, institution_id, active, _, user_id = params
            self.users[user_id].update(role=role, institution_id=institution_id, is_active=active)
            return Cursor(self.users[user_id])
        if q.startswith("insert into account_role_audit"):
            self.audit.append(params)
            return Cursor()
        if q.startswith("select id, email, full_name") and "from app_user order by" in q:
            limit, offset = params
            return Cursor(rows=list(self.users.values())[offset:offset + limit])
        if q.startswith("update account_invitation set revoked_at"):
            at, user_id, *excluded = params
            for invitation in self.invitations.values():
                if invitation["user_id"] == user_id and invitation["used_at"] is None and invitation["revoked_at"] is None and (not excluded or invitation["id"] != excluded[0]):
                    invitation["revoked_at"] = at
            return Cursor()
        if q.startswith("insert into account_invitation"):
            invitation_id, user_id, hashed, actor_id, created_at, expires_at = params
            self.invitations[invitation_id] = {"id": invitation_id, "user_id": user_id,
                "token_hash": hashed, "created_by": actor_id, "created_at": created_at,
                "expires_at": expires_at, "used_at": None, "revoked_at": None}
            return Cursor()
        if q.startswith("select i.user_id"):
            invitation = self.invitations.get(params[0])
            user = self.users.get(invitation["user_id"]) if invitation else None
            return Cursor({**invitation, "password_hash": user["password_hash"]} if user else None)
        if q.startswith("update app_user set password_hash"):
            hashed, _, user_id = params
            self.users[user_id].update(password_hash=hashed, is_active=True)
            return Cursor()
        if q.startswith("update account_invitation set used_at"):
            at, invitation_id = params
            self.invitations[invitation_id]["used_at"] = at
            return Cursor()
        if "from app_user u join candidate_profile p" in q:
            candidate_id = params[0]
            user = self.users.get(candidate_id)
            if not user or user["role"] != "candidate" or candidate_id not in self.profiles:
                return Cursor()
            if "from recommendation" in q and params[1:] != (1, 1):
                return Cursor()
            if "interview_scheduled" in q and candidate_id != 20:
                return Cursor()
            return Cursor({**user, **dict.fromkeys(("phone", "birth_year", "city", "nationality",
                "current_level", "bac_section", "bac_year", "bac_average", "last_diploma",
                "last_diploma_specialty", "favorite_subjects", "interests", "career_goal", "constraints")),
                "preferred_language": "fr"})
        if q.startswith("select a.id") and "from application a" in q:
            return Cursor(rows=[])
        raise AssertionError(f"Unexpected SQL: {q}")


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    database = FakeConnection()
    settings = Settings(
        _env_file=None,
        account_jwt_secret=SecretStr("test-account-secret-0123456789abcdef-unique"),
        visitor_session_secret=SecretStr("test-visitor-secret-0123456789abcdef-unique"),
        auth_cookie_secure=False,
        environment="development",
    )
    monkeypatch.setattr(auth_endpoint, "get_settings", lambda: settings)
    monkeypatch.setattr(admin_endpoint, "get_settings", lambda: settings)
    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    app.dependency_overrides[get_db] = lambda: database
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        yield client, database, settings
    app.dependency_overrides.clear()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_password_hashes_and_account_visitor_tokens_are_separate(api) -> None:
    _, _, settings = api
    password = "a long sample password"
    hashed = hash_password(password)
    assert hashed != password and verify_password(password, hashed)
    assert not verify_password("wrong password", hashed)
    assert not verify_password(password, None)
    now = datetime.now(timezone.utc)
    account_token = issue_access_token(1, UUID("00000000-0000-0000-0000-000000000001"), settings, now)
    visitor_token = visitor_sessions._issue_access_token(UUID("00000000-0000-0000-0000-000000000002"), now, settings)
    assert decode_access_token(account_token, settings)[0] == 1
    with pytest.raises(AppError):
        decode_access_token(visitor_token, settings)
    with pytest.raises(AppError):
        visitor_sessions._decode_access_token(account_token, settings)


def test_candidate_registration_login_refresh_and_logout(api) -> None:
    client, database, _ = api
    registration = client.post("/api/v1/auth/register", json={
        "email": "CANDIDATE@Example.com", "full_name": "Candidate One",
        "password": "a long candidate password",
    })
    assert registration.status_code == 201
    body = registration.json()
    assert body["user"]["role"] == "candidate"
    assert body["user"]["email"] == "candidate@example.com"
    assert body["user"]["id"] in database.profiles
    assert "password_hash" not in body["user"]
    assert "httponly" in registration.headers["set-cookie"].lower()
    assert "samesite=strict" in registration.headers["set-cookie"].lower()
    first_session = next(iter(database.sessions.values()))
    assert first_session["refresh_token_hash"] != client.cookies.get("smartcampus_refresh")
    assert first_session["refresh_token_hash"] == token_hash(client.cookies.get("smartcampus_refresh"))
    me = client.get("/api/v1/auth/me", headers=_headers(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["role"] == "candidate"
    old_cookie = client.cookies.get("smartcampus_refresh")
    refreshed = client.post("/api/v1/auth/refresh", headers={"Origin": "http://testserver"})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != body["access_token"]
    with pytest.raises(AppError) as replay:
        accounts.refresh(database, refresh_token=old_cookie, settings=api[2])
    assert replay.value.status_code == 401
    logout = client.post("/api/v1/auth/logout", headers={"Origin": "http://testserver"})
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me", headers=_headers(refreshed.json()["access_token"])).status_code == 401


def test_registration_cannot_choose_staff_role_and_login_failures_are_generic(api) -> None:
    client, database, _ = api
    admin = database.user("admin@example.com", "admin", None)
    attempt = client.post("/api/v1/auth/register", json={
        "email": "attacker@example.com", "full_name": "Attacker",
        "password": "a long candidate password", "role": "admin",
    })
    assert attempt.status_code == 422
    assert len(database.users) == 1
    wrong_admin = client.post("/api/v1/auth/login", json={"email": admin["email"], "password": "wrong"})
    unknown = client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong"})
    assert wrong_admin.status_code == unknown.status_code == 401
    assert wrong_admin.json()["error"]["code"] == unknown.json()["error"]["code"] == "INVALID_CREDENTIALS"
    for _ in range(3):
        client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong"})
    limited = client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong"})
    assert limited.status_code == 429


def test_admin_invitation_activation_and_role_change_revoke_sessions(api) -> None:
    client, database, settings = api
    admin = database.user("admin@example.com", "admin", "a long admin password")
    pending = database.user("staff@example.com", "academic_staff", None, 1)
    pending["is_active"] = False
    admin_login = client.post("/api/v1/auth/login", json={"email": admin["email"], "password": "a long admin password"})
    admin_token = admin_login.json()["access_token"]
    assert client.get("/api/v1/admin/users", headers=_headers(admin_token)).status_code == 200
    invitation = client.post(f"/api/v1/admin/users/{pending['id']}/invitations", headers=_headers(admin_token))
    assert invitation.status_code == 201
    invite_token = invitation.json()["invitation_token"]
    assert token_hash(invite_token) == next(iter(database.invitations.values()))["token_hash"]
    activated = client.post("/api/v1/auth/activate", json={
        "invitation_token": invite_token, "password": "a new staff password",
    })
    assert activated.status_code == 204
    assert database.users[pending["id"]]["is_active"]
    assert client.post("/api/v1/auth/activate", json={
        "invitation_token": invite_token, "password": "another staff password",
    }).status_code == 401
    staff_login = client.post("/api/v1/auth/login", json={"email": pending["email"], "password": "a new staff password"})
    assert staff_login.status_code == 200
    staff_token = staff_login.json()["access_token"]
    assert client.get("/api/v1/admin/users", headers=_headers(staff_token)).status_code == 403
    changed = client.patch(f"/api/v1/admin/users/{pending['id']}", json={"role": "interviewer"}, headers=_headers(admin_token))
    assert changed.status_code == 200
    assert changed.json()["role"] == "interviewer"
    assert database.audit and database.audit[-1][0] == admin["id"]
    assert client.get("/api/v1/auth/me", headers=_headers(staff_token)).status_code == 401
    with pytest.raises(AppError) as exc:
        accounts.update_user(database, actor_id=admin["id"], target_id=admin["id"], fields={"is_active": False})
    assert exc.value.code == "LAST_ADMIN_REQUIRED"
    assert settings.account_invite_hours == 24


def test_candidate_resource_and_origin_guards(api) -> None:
    client, database, settings = api
    candidate = database.user("candidate@example.com", "candidate", "a long candidate password")
    staff = database.user("staff@example.com", "academic_staff", "a long staff password", 1)
    other_staff = database.user("other@example.com", "academic_staff", "a long staff password", 2)
    candidate_login = client.post("/api/v1/auth/login", json={"email": candidate["email"], "password": "a long candidate password"}).json()
    token = candidate_login["access_token"]
    assert client.get("/api/v1/candidates/me", headers=_headers(token)).status_code == 200
    assert client.get("/api/v1/candidates/me/applications", headers=_headers(token)).json() == {"items": []}
    assert client.get("/api/v1/candidates/999", headers=_headers(token)).status_code == 403
    assert client.post("/api/v1/auth/refresh").status_code == 403
    assert client.post("/api/v1/auth/refresh", headers={"Origin": "https://evil.example"}).status_code == 403
    staff_actor = {**staff, "session_id": UUID(int=1)}
    assert accounts.get_candidate_profile(database, candidate_id=candidate["id"], actor=staff_actor)["id"] == candidate["id"]
    with pytest.raises(AppError) as exc:
        accounts.get_candidate_profile(database, candidate_id=candidate["id"], actor=other_staff)
    assert exc.value.status_code == 404
    assert settings.auth_cookie_secure is False


def test_generated_openapi_exposes_account_contract(api) -> None:
    client, _, _ = api
    schema = client.get("/openapi.json").json()
    assert "accountBearer" in schema["components"]["securitySchemes"]
    assert "visitorBearer" in schema["components"]["securitySchemes"]
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/admin/users/{user_id}/invitations" in schema["paths"]
    assert "role" not in schema["components"]["schemas"]["RegisterRequest"]["properties"]
