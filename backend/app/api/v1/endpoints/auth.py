from fastapi import APIRouter, Depends, Request, Response
from psycopg import Connection

from app.api.v1.dependencies import get_current_account
from app.core.account_security import (
    clear_refresh_cookie, cookie_name, peer_ip, set_refresh_cookie, validate_origin,
)
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.openapi import ERROR_RESPONSES
from app.db.session import get_db
from app.schemas.account import (
    AccountPublic, ActivateRequest, AuthResponse, LoginRequest, RegisterRequest,
)
from app.schemas.error import ErrorResponse
from app.services import accounts

router = APIRouter(prefix="/auth", responses=ERROR_RESPONSES)
AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Account credential invalid or expired"},
    403: {"model": ErrorResponse, "description": "Origin or role not allowed"},
    409: {"model": ErrorResponse, "description": "Account state conflict"},
    429: {"model": ErrorResponse, "description": "Authentication rate limit reached"},
    503: {"model": ErrorResponse, "description": "Account signing is not configured"},
}


@router.post("/register", response_model=AuthResponse, status_code=201, responses=AUTH_ERRORS,
             summary="Register a candidate account")
def register(
    body: RegisterRequest, request: Request, response: Response,
    db: Connection = Depends(get_db),
) -> dict:
    settings = get_settings()
    validate_origin(request, settings)
    result, refresh_token = accounts.register_candidate(
        db, email=str(body.email), full_name=body.full_name, password=body.password,
        client_ip=peer_ip(request), settings=settings,
    )
    set_refresh_cookie(response, refresh_token, settings)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/login", response_model=AuthResponse, responses=AUTH_ERRORS,
             summary="Sign in with an account")
def login(
    body: LoginRequest, request: Request, response: Response,
    db: Connection = Depends(get_db),
) -> dict:
    settings = get_settings()
    validate_origin(request, settings)
    result, refresh_token = accounts.login(
        db, email=str(body.email), password=body.password,
        client_ip=peer_ip(request), settings=settings,
    )
    set_refresh_cookie(response, refresh_token, settings)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/refresh", response_model=AuthResponse, responses=AUTH_ERRORS,
             summary="Rotate an account refresh credential")
def refresh(
    request: Request, response: Response, db: Connection = Depends(get_db),
) -> dict:
    settings = get_settings()
    validate_origin(request, settings, required=True)
    token = request.cookies.get(cookie_name(settings))
    if not token:
        raise AppError(code="AUTHENTICATION_REQUIRED", message="An account refresh cookie is required.", status_code=401)
    result, rotated = accounts.refresh(db, refresh_token=token, settings=settings)
    set_refresh_cookie(response, rotated, settings)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/logout", status_code=204, responses=AUTH_ERRORS,
             summary="Revoke the current account session")
def logout(
    request: Request, response: Response, db: Connection = Depends(get_db),
) -> None:
    settings = get_settings()
    token = request.cookies.get(cookie_name(settings))
    validate_origin(request, settings, required=bool(token))
    authorization = request.headers.get("authorization", "")
    access_token = authorization[7:] if authorization.lower().startswith("bearer ") else None
    accounts.logout(db, refresh_token=token, access_token=access_token, settings=settings)
    clear_refresh_cookie(response, settings)
    response.headers["Cache-Control"] = "no-store"


@router.post("/activate", status_code=204, responses=AUTH_ERRORS,
             summary="Set the first password with a one-time invitation")
def activate(
    body: ActivateRequest, request: Request, response: Response,
    db: Connection = Depends(get_db),
) -> None:
    settings = get_settings()
    validate_origin(request, settings)
    accounts.activate(
        db, invitation_token=body.invitation_token,
        password=body.password, settings=settings,
    )
    response.headers["Cache-Control"] = "no-store"


@router.get("/me", response_model=AccountPublic, responses=AUTH_ERRORS,
            summary="Get the current account and effective role")
def me(account: dict = Depends(get_current_account)) -> dict:
    return account
