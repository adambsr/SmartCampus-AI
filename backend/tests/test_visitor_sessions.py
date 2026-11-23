"""SA-25 visitor session unit and API tests; no database is required."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
import jwt
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.db.session import get_db
from app.main import app
from app.services import visitor_sessions as service


class Cursor:
    def __init__(self, row: dict[str, Any] | None = None):
        self.row = row

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


class FakeConnection:
    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.rate_rows: list[tuple[str, datetime]] = []

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
            self.sessions[str(session_id)] = {
                "id": session_id,
                "status": "active",
                "language": language,
                "created_at": created_at,
                "last_activity_at": last_activity_at,
                "idle_expires_at": idle_expires_at,
                "absolute_expires_at": absolute_expires_at,
                "refresh_token_hash": refresh_token_hash,
            }
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
        if query.startswith("update visitor_session set last_activity_at = %s, idle_expires_at = %s"):
            now, idle_expires_at, session_id = params
            row = self.sessions[str(session_id)]
            row["last_activity_at"] = now
            row["idle_expires_at"] = idle_expires_at
            return Cursor()
        if query.startswith("update visitor_session set refresh_token_hash = %s"):
            token_hash, now, idle_expires_at, session_id = params
            row = self.sessions[str(session_id)]
            row["refresh_token_hash"] = token_hash
            row["last_activity_at"] = now
            row["idle_expires_at"] = idle_expires_at
            return Cursor()
        raise AssertionError(f"Unexpected SQL in fake connection: {query}")


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    database = FakeConnection()
    settings = Settings(visitor_session_secret=SecretStr("unit-test-secret-value-0123456789abcdef"))
    current_time = [datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)]
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(service, "_now", lambda: current_time[0])
    app.dependency_overrides[get_db] = lambda: database
    with TestClient(app, client=("203.0.113.10", 12345)) as client:
        yield client, database, current_time, settings
    app.dependency_overrides.clear()


def test_creation_returns_unique_uuid_and_does_not_store_client_context(api) -> None:
    client, database, _, _ = api
    first = client.post(
        "/api/v1/visitor-sessions",
        json={"language": "fr", "client_context": {"source": "homepage"}},
    )
    second = client.post("/api/v1/visitor-sessions", json={"language": "tn"})

    assert first.status_code == second.status_code == 201
    first_body, second_body = first.json(), second.json()
    assert first_body["id"] != second_body["id"]
    assert first_body["status"] == "active"
    assert first_body["language"] == "fr"
    assert first_body["access_token"] and first_body["refresh_token"]
    assert "client_context" not in database.sessions[first_body["id"]]
    assert set(database.sessions[first_body["id"]]) == {
        "id",
        "status",
        "language",
        "created_at",
        "last_activity_at",
        "idle_expires_at",
        "absolute_expires_at",
        "refresh_token_hash",
    }


def test_session_routes_fail_closed_without_signing_secret(api, monkeypatch) -> None:
    client, _, _, _ = api
    monkeypatch.setattr(service, "get_settings", lambda: Settings())
    response = client.post("/api/v1/visitor-sessions")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "VISITOR_SESSION_NOT_CONFIGURED"


def test_status_requires_matching_valid_session_token_and_refreshes_access_token(api) -> None:
    client, _, _, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    response = client.get(
        f"/api/v1/visitor-sessions/{created['id']}",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["access_token"] != created["access_token"]
    assert "refresh_token" not in response.json()


def test_missing_invalid_and_mismatched_tokens_use_common_errors(api) -> None:
    client, _, _, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    missing = client.get(f"/api/v1/visitor-sessions/{created['id']}")
    invalid = client.get(
        f"/api/v1/visitor-sessions/{created['id']}",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    other_id = str(uuid4())
    mismatch = client.get(
        f"/api/v1/visitor-sessions/{other_id}",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )

    assert missing.status_code == invalid.status_code == 401
    assert mismatch.status_code == 403
    for response in (missing, invalid, mismatch):
        body = response.json()
        assert set(body) == {"error"}
        assert body["error"]["request_id"] == response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "token_factory",
    [
        lambda session_id, now, key: jwt.encode(
            {"sid": str(session_id), "sub": str(session_id), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=15)).timestamp())},
            key,
            algorithm="HS256",
        ) + "x",
        lambda session_id, now, key: "not-a-jwt",
        lambda session_id, now, key: jwt.encode(
            {"sid": str(session_id), "sub": str(session_id), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=15)).timestamp())},
            "unsupported-algorithm-test-key-at-least-48-bytes-long",
            algorithm="HS384",
        ),
        lambda session_id, now, key: jwt.encode(
            {"sid": str(session_id), "sub": str(session_id), "iat": int(now.timestamp())},
            key,
            algorithm="HS256",
        ),
        lambda session_id, now, key: jwt.encode(
            {"sid": str(session_id), "sub": 42, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=15)).timestamp())},
            key,
            algorithm="HS256",
        ),
        lambda session_id, now, key: jwt.encode(
            {"sid": "not-a-uuid", "sub": str(session_id), "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=15)).timestamp())},
            key,
            algorithm="HS256",
        ),
    ],
    ids=["invalid-signature", "malformed", "unsupported-algorithm", "missing-claim", "wrong-type", "invalid-uuid"],
)
def test_invalid_jwt_variants_are_rejected(api, token_factory) -> None:
    client, _, current_time, settings = api
    created = client.post("/api/v1/visitor-sessions").json()
    token = token_factory(UUID(created["id"]), current_time[0], settings.visitor_session_secret.get_secret_value())
    response = client.get(
        f"/api/v1/visitor-sessions/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_VISITOR_SESSION_TOKEN"


def test_unknown_session_returns_404(api) -> None:
    client, _, current_time, settings = api
    absent_id = uuid4()
    token = service._issue_access_token(absent_id, current_time[0], settings)
    response = client.get(
        f"/api/v1/visitor-sessions/{absent_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VISITOR_SESSION_NOT_FOUND"


def test_expiry_marks_and_preserves_minimal_session_record(api) -> None:
    client, database, current_time, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    session_id = created["id"]
    current_time[0] += timedelta(minutes=31)
    response = client.get(
        f"/api/v1/visitor-sessions/{session_id}",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )

    assert response.status_code == 410
    assert database.sessions[session_id]["status"] == "expired"
    assert session_id in database.sessions


def test_absolute_expiry_is_enforced(api) -> None:
    client, database, current_time, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    session_id = created["id"]
    row = database.sessions[session_id]
    # Simulate ongoing activity up to the absolute lifetime.
    row["idle_expires_at"] = row["absolute_expires_at"]
    current_time[0] = row["absolute_expires_at"]
    response = client.post(
        f"/api/v1/visitor-sessions/{session_id}/refresh",
        json={"refresh_token": created["refresh_token"]},
    )

    assert response.status_code == 410
    assert row["status"] == "expired"
    assert session_id in database.sessions


def test_refresh_rotates_token_and_rejects_reuse(api) -> None:
    client, database, _, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    url = f"/api/v1/visitor-sessions/{created['id']}/refresh"
    rotated = client.post(url, json={"refresh_token": created["refresh_token"]})
    reused = client.post(url, json={"refresh_token": created["refresh_token"]})

    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != created["refresh_token"]
    assert rotated.json()["access_token"] != created["access_token"]
    assert reused.status_code == 401
    assert database.sessions[created["id"]]["refresh_token_hash"] != created["refresh_token"]


def test_creation_quota_uses_peer_ip_and_ignores_forwarded_headers(api) -> None:
    client, database, _, _ = api
    for index in range(5):
        response = client.post(
            "/api/v1/visitor-sessions",
            headers={"X-Forwarded-For": f"198.51.100.{index + 1}"},
        )
        assert response.status_code == 201
    limited = client.post(
        "/api/v1/visitor-sessions", headers={"X-Forwarded-For": "203.0.113.77"}
    )

    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "VISITOR_SESSION_RATE_LIMITED"
    assert len(database.rate_rows) == 5
    assert len({ip_hash for ip_hash, _ in database.rate_rows}) == 1


def test_creation_limit_is_per_ip_and_old_rate_records_are_pruned(api) -> None:
    client, database, current_time, _ = api
    for _ in range(5):
        assert client.post("/api/v1/visitor-sessions").status_code == 201
    current_time[0] += timedelta(hours=1, seconds=1)
    assert client.post("/api/v1/visitor-sessions").status_code == 201
    assert len(database.rate_rows) == 1


def test_peer_ip_has_an_independent_creation_quota(api) -> None:
    _, database, _, _ = api
    with TestClient(app, client=("203.0.113.11", 12345)) as other_peer:
        response = other_peer.post("/api/v1/visitor-sessions")
    assert response.status_code == 201
    assert len(database.rate_rows) == 1


def test_openapi_marks_refresh_as_proposed_contract_extension(api) -> None:
    client, _, _, _ = api
    schema = client.get("/openapi.json").json()
    refresh = schema["paths"]["/api/v1/visitor-sessions/{session_id}/refresh"]["post"]
    assert "proposed sa-5 contract extension" in refresh["description"].lower()
    assert "refresh_token" in schema["components"]["schemas"]["VisitorSessionWithRefreshResponse"]["required"]


def test_expired_access_token_is_rejected_while_session_is_still_active(api) -> None:
    client, _, current_time, _ = api
    created = client.post("/api/v1/visitor-sessions").json()
    current_time[0] += timedelta(minutes=16)
    response = client.get(
        f"/api/v1/visitor-sessions/{created['id']}",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "VISITOR_SESSION_TOKEN_EXPIRED"
