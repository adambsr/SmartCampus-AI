from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.services import accounts

account_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="accountBearer",
    description="A 15-minute account access JWT; visitor JWTs are not accepted.",
)


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(account_bearer),
    db: Connection = Depends(get_db),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(code="AUTHENTICATION_REQUIRED", message="An account Bearer token is required.", status_code=401)
    return accounts.authenticate_access(db, token=credentials.credentials, settings=get_settings())


def require_candidate(account: dict[str, Any] = Depends(get_current_account)) -> dict[str, Any]:
    if account["role"] != "candidate":
        raise AppError(code="FORBIDDEN", message="Candidate access is required.", status_code=403)
    return account


def require_admin(account: dict[str, Any] = Depends(get_current_account)) -> dict[str, Any]:
    if account["role"] != "admin":
        raise AppError(code="FORBIDDEN", message="Administrator access is required.", status_code=403)
    return account
