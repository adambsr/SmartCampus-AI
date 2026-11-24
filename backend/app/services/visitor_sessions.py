"""Visitor session lifecycle and credentials (SA-25)."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from psycopg import Connection

from app.core.config import Settings, get_settings
from app.core.errors import AppError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _secret(settings: Settings) -> bytes:
    configured = settings.visitor_session_secret
    value = configured.get_secret_value() if configured is not None else ""
    secret = value.encode("utf-8")
    if len(secret) < 32:
        raise AppError(
            code="VISITOR_SESSION_NOT_CONFIGURED",
            message="Visitor sessions require VISITOR_SESSION_SECRET with at least 32 bytes.",
            status_code=503,
        )
    return secret


def _issue_access_token(session_id: UUID, now: datetime, settings: Settings) -> str:
    expiry = now + timedelta(minutes=settings.visitor_session_access_token_minutes)
    payload = {
        "sid": str(session_id),
        "sub": str(session_id),
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
        "jti": secrets.token_urlsafe(12),
    }
    return jwt.encode(payload, _secret(settings), algorithm="HS256", headers={"typ": "JWT"})


def _new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def _refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _ip_hmac(client_ip: str, settings: Settings) -> str:
    key = hmac.new(
        _secret(settings), b"smartcampus:visitor-session:ip-hmac:v1", hashlib.sha256
    ).digest()
    return hmac.new(key, client_ip.encode("utf-8"), hashlib.sha256).hexdigest()


def _session_expired(row: dict[str, Any], now: datetime) -> bool:
    return (
        row["status"] != "active"
        or now >= row["idle_expires_at"]
        or now >= row["absolute_expires_at"]
    )


def _expiry_update(conn: Connection, session_id: UUID) -> None:
    conn.execute(
        "UPDATE visitor_session SET status = 'expired' WHERE id = %s AND status = 'active'",
        (session_id,),
    )


def create_visitor_session(
    conn: Connection,
    *,
    client_ip: str,
    language: str | None,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    now = now or _now()
    absolute_expires_at = now + timedelta(hours=settings.visitor_session_max_hours)
    idle_expires_at = min(
        now + timedelta(minutes=settings.visitor_session_idle_minutes), absolute_expires_at
    )
    ip_hash = _ip_hmac(client_ip, settings)
    session_id = uuid4()
    refresh_token = _new_refresh_token()

    rate_limited = False
    with conn.transaction():
        # Serialize creations from the same address so concurrent requests cannot
        # race past the hourly quota. Only an HMAC, never the address, is stored.
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (ip_hash,))
        window_start = now - timedelta(hours=1)
        conn.execute(
            "DELETE FROM visitor_session_creation WHERE created_at <= %s", (window_start,)
        )
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM visitor_session_creation "
            "WHERE ip_hmac = %s AND created_at > %s",
            (ip_hash, window_start),
        ).fetchone()["count"]
        if count >= settings.visitor_session_creations_per_hour:
            rate_limited = True
        else:
            conn.execute(
                """INSERT INTO visitor_session
                   (id, status, language, created_at, last_activity_at, idle_expires_at,
                    absolute_expires_at, refresh_token_hash)
                   VALUES (%s, 'active', %s, %s, %s, %s, %s, %s)""",
                (
                    session_id,
                    language,
                    now,
                    now,
                    idle_expires_at,
                    absolute_expires_at,
                    _refresh_hash(refresh_token),
                ),
            )
            conn.execute(
                "INSERT INTO visitor_session_creation (ip_hmac, created_at) VALUES (%s, %s)",
                (ip_hash, now),
            )

    if rate_limited:
        raise AppError(
            code="VISITOR_SESSION_RATE_LIMITED",
            message="The visitor session creation limit has been reached.",
            status_code=429,
        )

    return {
        "id": session_id,
        "status": "active",
        "language": language,
        "created_at": now,
        "expires_at": absolute_expires_at,
        "access_token": _issue_access_token(session_id, now, settings),
        "refresh_token": refresh_token,
    }


def _decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            _secret(settings),
            algorithms=["HS256"],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "require": ["sid", "sub", "iat", "exp"],
            },
        )
        for name in ("sid", "sub"):
            value = claims.get(name)
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError(f"{name} must be a canonical UUID string")
        for name in ("iat", "exp"):
            value = claims.get(name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer NumericDate")
        if claims["exp"] <= claims["iat"]:
            raise ValueError("exp must be later than iat")
        return claims
    except (InvalidTokenError, ValueError, TypeError, KeyError) as exc:
        raise AppError(
            code="INVALID_VISITOR_SESSION_TOKEN",
            message="The visitor session token is invalid.",
            status_code=401,
        ) from exc


def get_visitor_session(
    conn: Connection,
    *,
    session_id: UUID,
    token: str,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    now = now or _now()
    claims = _decode_access_token(token, settings)
    if claims.get("sid") != str(session_id) or claims.get("sub") != str(session_id):
        raise AppError(
            code="VISITOR_SESSION_OWNERSHIP_MISMATCH",
            message="The token does not belong to this visitor session.",
            status_code=403,
        )
    if claims["iat"] > int(now.timestamp()):
        raise AppError(
            code="INVALID_VISITOR_SESSION_TOKEN",
            message="The visitor session token is invalid.",
            status_code=401,
        )

    with conn.transaction():
        row = conn.execute(
            "SELECT * FROM visitor_session WHERE id = %s FOR UPDATE", (session_id,)
        ).fetchone()
        if row is None:
            raise AppError(
                code="VISITOR_SESSION_NOT_FOUND",
                message="The visitor session was not found.",
                status_code=404,
            )
        if _session_expired(row, now):
            if row["status"] == "active":
                _expiry_update(conn, session_id)
            expired = True
        elif claims["exp"] <= int(now.timestamp()):
            raise AppError(
                code="VISITOR_SESSION_TOKEN_EXPIRED",
                message="The visitor access token has expired; refresh the session token.",
                status_code=401,
            )
        else:
            idle_expires_at = min(
                now + timedelta(minutes=settings.visitor_session_idle_minutes),
                row["absolute_expires_at"],
            )
            conn.execute(
                """UPDATE visitor_session
                   SET last_activity_at = %s, idle_expires_at = %s
                   WHERE id = %s""",
                (now, idle_expires_at, session_id),
            )
            result = {
                "id": row["id"],
                "status": "active",
                "language": row["language"],
                "created_at": row["created_at"],
                "expires_at": row["absolute_expires_at"],
                "access_token": _issue_access_token(session_id, now, settings),
            }
            expired = False

    if expired:
        raise AppError(
            code="VISITOR_SESSION_EXPIRED",
            message="The visitor session has expired.",
            status_code=410,
        )
    return result


def get_visitor_session_from_token(
    conn: Connection,
    *,
    token: str,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Validate a visitor JWT and load its session without trusting a caller-supplied ID."""
    settings = settings or get_settings()
    claims = _decode_access_token(token, settings)
    return get_visitor_session(
        conn,
        session_id=UUID(claims["sid"]),
        token=token,
        now=now,
        settings=settings,
    )


def refresh_visitor_session(
    conn: Connection,
    *,
    session_id: UUID,
    refresh_token: str,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    now = now or _now()
    new_refresh_token = _new_refresh_token()

    with conn.transaction():
        row = conn.execute(
            "SELECT * FROM visitor_session WHERE id = %s FOR UPDATE", (session_id,)
        ).fetchone()
        if row is None:
            raise AppError(
                code="VISITOR_SESSION_NOT_FOUND",
                message="The visitor session was not found.",
                status_code=404,
            )
        if _session_expired(row, now):
            if row["status"] == "active":
                _expiry_update(conn, session_id)
            expired = True
        elif not hmac.compare_digest(row["refresh_token_hash"], _refresh_hash(refresh_token)):
            raise AppError(
                code="INVALID_VISITOR_REFRESH_TOKEN",
                message="The visitor refresh token is invalid or has already been rotated.",
                status_code=401,
            )
        else:
            idle_expires_at = min(
                now + timedelta(minutes=settings.visitor_session_idle_minutes),
                row["absolute_expires_at"],
            )
            conn.execute(
                """UPDATE visitor_session
                   SET refresh_token_hash = %s, last_activity_at = %s, idle_expires_at = %s
                   WHERE id = %s""",
                (_refresh_hash(new_refresh_token), now, idle_expires_at, session_id),
            )
            result = {
                "id": row["id"],
                "status": "active",
                "language": row["language"],
                "created_at": row["created_at"],
                "expires_at": row["absolute_expires_at"],
                "access_token": _issue_access_token(session_id, now, settings),
                "refresh_token": new_refresh_token,
            }
            expired = False

    if expired:
        raise AppError(
            code="VISITOR_SESSION_EXPIRED",
            message="The visitor session has expired.",
            status_code=410,
        )
    return result
