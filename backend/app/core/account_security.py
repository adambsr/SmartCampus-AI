"""Account credential primitives. Visitor tokens deliberately use another secret/profile."""

import hashlib
import hmac
import ipaddress
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request, Response
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings
from app.core.errors import AppError

COOKIE_SECURE_NAME = "__Host-smartcampus-refresh"
COOKIE_DEV_NAME = "smartcampus_refresh"
ISSUER = "smartcampus-account"
AUDIENCE = "smartcampus-api-account"
TOKEN_KIND = "account_access"
ACCESS_MINUTES = 15
HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, salt_len=16)
_DUMMY_HASH = HASHER.hash("dummy-password-that-is-not-an-account")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def account_secret(settings: Settings) -> bytes:
    configured = settings.account_jwt_secret
    value = configured.get_secret_value() if configured else ""
    secret = value.encode("utf-8")
    if len(secret) < 32 or value.startswith("replace-with"):
        raise AppError(
            code="ACCOUNT_AUTH_NOT_CONFIGURED",
            message="Account authentication requires a distinct ACCOUNT_JWT_SECRET of at least 32 bytes.",
            status_code=503,
        )
    visitor = settings.visitor_session_secret
    if visitor and value == visitor.get_secret_value():
        raise AppError(
            code="ACCOUNT_AUTH_NOT_CONFIGURED",
            message="Account and visitor signing secrets must differ.",
            status_code=503,
        )
    return secret


def hash_password(password: str) -> str:
    return HASHER.hash(password)


def verify_password(password: str, stored_hash: str | None) -> bool:
    if stored_hash is None:
        # Spend comparable work for an unknown or passwordless account.
        stored_hash = _DUMMY_HASH
        dummy = True
    else:
        dummy = False
    try:
        return HASHER.verify(stored_hash, password) and not dummy
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    return HASHER.check_needs_rehash(stored_hash)


def issue_access_token(user_id: int, session_id: UUID, settings: Settings, at: datetime) -> str:
    payload = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "token_type": TOKEN_KIND,
        "sub": str(user_id),
        "sid": str(session_id),
        "iat": int(at.timestamp()),
        "nbf": int(at.timestamp()),
        "exp": int((at + timedelta(minutes=ACCESS_MINUTES)).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, account_secret(settings), algorithm="HS256", headers={"typ": "JWT"})


def decode_access_token(token: str, settings: Settings) -> tuple[int, UUID]:
    try:
        claims = jwt.decode(
            token,
            account_secret(settings),
            algorithms=["HS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"require": ["iss", "aud", "token_type", "sub", "sid", "iat", "nbf", "exp", "jti"]},
        )
        if claims["token_type"] != TOKEN_KIND or not isinstance(claims["sub"], str):
            raise ValueError("Wrong token kind or subject")
        if not claims["sub"].isdigit() or int(claims["sub"]) <= 0:
            raise ValueError("Invalid account subject")
        sid = UUID(claims["sid"])
        if str(sid) != claims["sid"]:
            raise ValueError("Noncanonical session ID")
        for key in ("iat", "nbf", "exp"):
            if isinstance(claims[key], bool) or not isinstance(claims[key], int):
                raise ValueError("Invalid NumericDate")
        if claims["exp"] <= claims["iat"]:
            raise ValueError("Invalid token lifetime")
        if not isinstance(claims["jti"], str) or not claims["jti"]:
            raise ValueError("Invalid token ID")
        return int(claims["sub"]), sid
    except (InvalidTokenError, ValueError, TypeError, KeyError) as exc:
        raise AppError(
            code="INVALID_ACCOUNT_TOKEN", message="The account access token is invalid.", status_code=401
        ) from exc


def new_opaque_token() -> tuple[UUID, str, str]:
    token_id = uuid4()
    token = f"{token_id}.{secrets.token_urlsafe(32)}"
    return token_id, token, token_hash(token)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_id(token: str) -> UUID | None:
    try:
        identifier, secret = token.split(".", 1)
        result = UUID(identifier)
        if str(result) != identifier or len(secret) < 32:
            return None
        return result
    except (ValueError, AttributeError):
        return None


def hash_matches(expected: str, actual: str) -> bool:
    return hmac.compare_digest(expected, actual)


def identity_hmac(value: str, settings: Settings, purpose: str) -> str:
    key = hmac.new(account_secret(settings), f"smartcampus:auth:{purpose}:v1".encode(), hashlib.sha256).digest()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def peer_ip(request: Request) -> str:
    client = request.client
    try:
        if client is None:
            raise ValueError("missing peer")
        return str(ipaddress.ip_address(client.host))
    except ValueError as exc:
        raise AppError(
            code="CLIENT_ADDRESS_UNAVAILABLE",
            message="A trusted connection peer IP address is required.",
            status_code=400,
        ) from exc


def validate_origin(request: Request, settings: Settings, *, required: bool = False) -> None:
    origin = request.headers.get("origin")
    if not origin:
        if required:
            raise AppError(code="ORIGIN_REQUIRED", message="An Origin header is required.", status_code=403)
        return
    own_origin = f"{request.url.scheme}://{request.headers.get('host', '')}"
    if origin not in {*settings.cors_origins, own_origin}:
        raise AppError(code="ORIGIN_NOT_ALLOWED", message="This origin is not allowed.", status_code=403)


def cookie_name(settings: Settings) -> str:
    if not settings.auth_cookie_secure and settings.environment != "development":
        raise AppError(code="ACCOUNT_AUTH_NOT_CONFIGURED", message="Insecure cookies are only allowed in development.", status_code=503)
    return COOKIE_SECURE_NAME if settings.auth_cookie_secure else COOKIE_DEV_NAME


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        cookie_name(settings), token, max_age=settings.account_refresh_days * 86400,
        secure=settings.auth_cookie_secure, httponly=True, samesite="strict", path="/",
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        cookie_name(settings), secure=settings.auth_cookie_secure, httponly=True,
        samesite="strict", path="/",
    )
