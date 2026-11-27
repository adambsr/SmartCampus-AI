"""Account authentication and role management (SA-28)."""

import secrets
from datetime import datetime, timedelta
from typing import Any
from psycopg import Connection
from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from app.core.account_security import (
    ACCESS_MINUTES, account_secret, decode_access_token, hash_matches, hash_password,
    identity_hmac, issue_access_token, needs_rehash, new_opaque_token, now_utc,
    token_hash, token_id, verify_password,
)
from app.core.config import Settings
from app.core.errors import AppError

USER_COLUMNS = "id, email, full_name, role::text AS role, institution_id, is_active, password_hash"
PUBLIC_COLUMNS = ("id", "email", "full_name", "role", "institution_id", "is_active")


def _public(row: dict[str, Any]) -> dict[str, Any]:
    return {name: row[name] for name in PUBLIC_COLUMNS}


def _email(value: str) -> str:
    return value.strip().lower()


def _invalid_credentials() -> AppError:
    return AppError(code="INVALID_CREDENTIALS", message="Invalid email or password.", status_code=401)


def _invalid_refresh() -> AppError:
    return AppError(code="INVALID_ACCOUNT_REFRESH_TOKEN", message="The account session is invalid or expired.", status_code=401)


def _not_found() -> AppError:
    return AppError(code="USER_NOT_FOUND", message="The user was not found.", status_code=404)


def _rate_keys(email: str, ip: str, settings: Settings) -> tuple[str, str]:
    return identity_hmac(email, settings, "email"), identity_hmac(ip, settings, "ip")


def _rate_count(conn: Connection, scope: str, email_key: str, ip_key: str, since: datetime) -> int:
    return conn.execute(
        """SELECT COUNT(*) AS count FROM account_auth_attempt
           WHERE scope = %s AND created_at > %s
             AND (identity_hmac = %s OR ip_hmac = %s)""",
        (scope, since, email_key, ip_key),
    ).fetchone()["count"]


def _rate_record(conn: Connection, scope: str, email_key: str, ip_key: str, at: datetime) -> None:
    conn.execute(
        """INSERT INTO account_auth_attempt (scope, identity_hmac, ip_hmac, created_at)
           VALUES (%s, %s, %s, %s)""",
        (scope, email_key, ip_key, at),
    )


def _rate_lock(conn: Connection, email_key: str, ip_key: str) -> None:
    # The deterministic order also serializes attempts for the same email from different IPs.
    for key in sorted((email_key, ip_key)):
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))


def _create_session(
    conn: Connection, user: dict[str, Any], settings: Settings, at: datetime
) -> tuple[dict[str, Any], str]:
    session_id, refresh_token, hashed = new_opaque_token()
    conn.execute(
        """INSERT INTO account_session
           (id, user_id, refresh_token_hash, created_at, expires_at)
           VALUES (%s, %s, %s, %s, %s)""",
        (session_id, user["id"], hashed, at, at + timedelta(days=settings.account_refresh_days)),
    )
    return {
        "access_token": issue_access_token(user["id"], session_id, settings, at),
        "token_type": "bearer",
        "expires_in": ACCESS_MINUTES * 60,
        "user": _public(user),
    }, refresh_token


def register_candidate(
    conn: Connection, *, email: str, full_name: str, password: str, client_ip: str,
    settings: Settings, at: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    account_secret(settings)
    at = at or now_utc()
    email = _email(email)
    email_key, ip_key = _rate_keys(email, client_ip, settings)
    password_hash = hash_password(password)
    limited = False
    try:
        with conn.transaction():
            _rate_lock(conn, email_key, ip_key)
            conn.execute("DELETE FROM account_auth_attempt WHERE created_at <= %s", (at - timedelta(hours=1),))
            limited = _rate_count(conn, "register", email_key, ip_key, at - timedelta(hours=1)) >= 5
            if not limited:
                user = conn.execute(
                    """INSERT INTO app_user (email, password_hash, full_name, role)
                       VALUES (%s, %s, %s, 'candidate')
                       RETURNING id, email, full_name, role::text AS role,
                                 institution_id, is_active, password_hash""",
                    (email, password_hash, full_name.strip()),
                ).fetchone()
                conn.execute("INSERT INTO candidate_profile (user_id) VALUES (%s)", (user["id"],))
                _rate_record(conn, "register", email_key, ip_key, at)
                result = _create_session(conn, user, settings, at)
    except UniqueViolation as exc:
        raise AppError(code="EMAIL_ALREADY_REGISTERED", message="This email is already registered.", status_code=409) from exc
    if limited:
        raise AppError(code="REGISTRATION_RATE_LIMITED", message="Too many registrations. Try again later.", status_code=429)
    return result


def login(
    conn: Connection, *, email: str, password: str, client_ip: str, settings: Settings,
    at: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    account_secret(settings)
    at = at or now_utc()
    email = _email(email)
    email_key, ip_key = _rate_keys(email, client_ip, settings)
    limited = failed = False
    with conn.transaction():
        _rate_lock(conn, email_key, ip_key)
        conn.execute("DELETE FROM account_auth_attempt WHERE created_at <= %s", (at - timedelta(hours=1),))
        limited = _rate_count(conn, "login", email_key, ip_key, at - timedelta(minutes=15)) >= 5
        if not limited:
            user = conn.execute(
                f"SELECT {USER_COLUMNS} FROM app_user WHERE lower(email) = %s",
                (email,),
            ).fetchone()
            valid = verify_password(password, user["password_hash"] if user else None)
            if not valid or not user or not user["is_active"] or not user["password_hash"]:
                _rate_record(conn, "login", email_key, ip_key, at)
                failed = True
            else:
                new_hash = hash_password(password) if needs_rehash(user["password_hash"]) else user["password_hash"]
                conn.execute(
                    "UPDATE app_user SET last_login_at = %s, password_hash = %s WHERE id = %s",
                    (at, new_hash, user["id"]),
                )
                result = _create_session(conn, user, settings, at)
    if limited:
        raise AppError(code="LOGIN_RATE_LIMITED", message="Too many login attempts. Try again later.", status_code=429)
    if failed:
        raise _invalid_credentials()
    return result


def authenticate_access(
    conn: Connection, *, token: str, settings: Settings, at: datetime | None = None
) -> dict[str, Any]:
    user_id, session_id = decode_access_token(token, settings)
    row = conn.execute(
        f"""SELECT u.{USER_COLUMNS.replace(', ', ', u.')},
                   s.revoked_at, s.expires_at
            FROM account_session s JOIN app_user u ON u.id = s.user_id
            WHERE s.id = %s AND u.id = %s""",
        (session_id, user_id),
    ).fetchone()
    if not row or not row["is_active"] or not row["password_hash"] or row["revoked_at"] is not None or row["expires_at"] <= (at or now_utc()):
        raise AppError(code="ACCOUNT_SESSION_INACTIVE", message="The account session is inactive.", status_code=401)
    return {**_public(row), "session_id": session_id}


def refresh(
    conn: Connection, *, refresh_token: str, settings: Settings, at: datetime | None = None
) -> tuple[dict[str, Any], str]:
    account_secret(settings)
    at = at or now_utc()
    session_id = token_id(refresh_token)
    if session_id is None:
        raise _invalid_refresh()
    with conn.transaction():
        row = conn.execute(
            f"""SELECT u.{USER_COLUMNS.replace(', ', ', u.')},
                       s.refresh_token_hash, s.expires_at, s.revoked_at
                FROM account_session s JOIN app_user u ON u.id = s.user_id
                WHERE s.id = %s FOR UPDATE OF s""",
            (session_id,),
        ).fetchone()
        if (
            not row or not row["is_active"] or not row["password_hash"]
            or row["revoked_at"] is not None or row["expires_at"] <= at
            or not hash_matches(row["refresh_token_hash"], token_hash(refresh_token))
        ):
            raise _invalid_refresh()
        rotated = f"{session_id}.{secrets.token_urlsafe(32)}"
        conn.execute(
            "UPDATE account_session SET refresh_token_hash = %s WHERE id = %s",
            (token_hash(rotated), session_id),
        )
        response = {
            "access_token": issue_access_token(row["id"], session_id, settings, at),
            "token_type": "bearer",
            "expires_in": ACCESS_MINUTES * 60,
            "user": _public(row),
        }
    return response, rotated


def logout(
    conn: Connection, *, refresh_token: str | None, access_token: str | None,
    settings: Settings, at: datetime | None = None,
) -> None:
    at = at or now_utc()
    session_id = token_id(refresh_token) if refresh_token else None
    with conn.transaction():
        if session_id and refresh_token:
            row = conn.execute(
                "SELECT refresh_token_hash FROM account_session WHERE id = %s FOR UPDATE",
                (session_id,),
            ).fetchone()
            if row and hash_matches(row["refresh_token_hash"], token_hash(refresh_token)):
                conn.execute(
                    "UPDATE account_session SET revoked_at = COALESCE(revoked_at, %s) WHERE id = %s",
                    (at, session_id),
                )
                return
        if access_token:
            try:
                user_id, access_sid = decode_access_token(access_token, settings)
            except AppError:
                return
            conn.execute(
                """UPDATE account_session SET revoked_at = COALESCE(revoked_at, %s)
                   WHERE id = %s AND user_id = %s""",
                (at, access_sid, user_id),
            )


def activate(
    conn: Connection, *, invitation_token: str, password: str, settings: Settings,
    at: datetime | None = None,
) -> None:
    account_secret(settings)
    at = at or now_utc()
    invitation_id = token_id(invitation_token)
    if invitation_id is None:
        raise AppError(code="INVALID_INVITATION", message="The invitation is invalid or expired.", status_code=401)
    password_hash = hash_password(password)
    with conn.transaction():
        row = conn.execute(
            """SELECT i.user_id, i.token_hash, i.expires_at, i.used_at, i.revoked_at,
                      u.password_hash
               FROM account_invitation i JOIN app_user u ON u.id = i.user_id
               WHERE i.id = %s FOR UPDATE OF i, u""",
            (invitation_id,),
        ).fetchone()
        if (
            not row or row["used_at"] is not None or row["revoked_at"] is not None
            or row["expires_at"] <= at or row["password_hash"] is not None
            or not hash_matches(row["token_hash"], token_hash(invitation_token))
        ):
            raise AppError(code="INVALID_INVITATION", message="The invitation is invalid or expired.", status_code=401)
        conn.execute(
            "UPDATE app_user SET password_hash = %s, is_active = true, updated_at = %s WHERE id = %s",
            (password_hash, at, row["user_id"]),
        )
        conn.execute("UPDATE account_invitation SET used_at = %s WHERE id = %s", (at, invitation_id))
        conn.execute(
            """UPDATE account_invitation SET revoked_at = %s
               WHERE user_id = %s AND id <> %s AND used_at IS NULL AND revoked_at IS NULL""",
            (at, row["user_id"], invitation_id),
        )


def list_users(conn: Connection, *, limit: int, offset: int) -> dict[str, Any]:
    rows = conn.execute(
        f"SELECT {USER_COLUMNS} FROM app_user ORDER BY id LIMIT %s OFFSET %s",
        (limit, offset),
    ).fetchall()
    return {"items": [_public(row) for row in rows]}


def create_staff(
    conn: Connection, *, email: str, full_name: str, role: str,
    institution_id: int | None,
) -> dict[str, Any]:
    if role not in ("interviewer", "admin"):
        raise AppError(code="INVALID_STAFF_ROLE", message="A supported staff role is required.", status_code=422)
    if institution_id is not None:
        raise AppError(
            code="INVALID_STAFF_INSTITUTION",
            message="Staff accounts do not use institution assignments.",
            status_code=422,
        )
    try:
        with conn.transaction():
            row = conn.execute(
                """INSERT INTO app_user (email, full_name, role, institution_id, is_active)
                   VALUES (%s, %s, %s, %s, false)
                   RETURNING id, email, full_name, role::text AS role,
                             institution_id, is_active, password_hash""",
                (_email(email), full_name.strip(), role, institution_id),
            ).fetchone()
    except UniqueViolation as exc:
        raise AppError(code="EMAIL_ALREADY_REGISTERED", message="This email is already registered.", status_code=409) from exc
    except (ForeignKeyViolation, CheckViolation) as exc:
        raise AppError(code="INVALID_STAFF_INSTITUTION", message="The institution is invalid.", status_code=422) from exc
    return _public(row)


def update_user(
    conn: Connection, *, actor_id: int, target_id: int,
    fields: dict[str, Any], at: datetime | None = None,
) -> dict[str, Any]:
    at = at or now_utc()
    if not fields:
        raise AppError(code="EMPTY_USER_UPDATE", message="No user changes were provided.", status_code=422)
    try:
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("smartcampus:last-admin:v1",))
            row = conn.execute(
                f"SELECT {USER_COLUMNS} FROM app_user WHERE id = %s FOR UPDATE", (target_id,)
            ).fetchone()
            if row is None:
                raise _not_found()
            if row["role"] == "candidate" and ("role" in fields or "institution_id" in fields):
                raise AppError(code="CANDIDATE_ROLE_IMMUTABLE", message="Candidate accounts cannot be converted to staff.", status_code=409)
            if any(value is None for key, value in fields.items() if key in ("role", "is_active")):
                raise AppError(code="INVALID_USER_UPDATE", message="Role and active status cannot be null.", status_code=422)
            role = fields.get("role", row["role"])
            active = fields.get("is_active", row["is_active"])
            institution_id = fields.get("institution_id", row["institution_id"])
            if "role" in fields and role not in ("interviewer", "admin"):
                raise AppError(code="INVALID_STAFF_ROLE", message="A supported staff role is required.", status_code=422)
            if "institution_id" in fields and institution_id is not None:
                raise AppError(code="INVALID_STAFF_INSTITUTION", message="Staff accounts do not use institution assignments.", status_code=422)
            institution_id = None
            changed = (role, institution_id, active) != (row["role"], row["institution_id"], row["is_active"])
            if not changed:
                return _public(row)
            if row["role"] == "admin" and row["is_active"] and row["password_hash"] and (role != "admin" or not active):
                count = conn.execute(
                    """SELECT COUNT(*) AS count FROM app_user
                       WHERE role = 'admin' AND is_active AND password_hash IS NOT NULL"""
                ).fetchone()["count"]
                if count <= 1:
                    raise AppError(code="LAST_ADMIN_REQUIRED", message="The last active administrator cannot be removed.", status_code=409)
            updated = conn.execute(
                """UPDATE app_user SET role = %s, institution_id = %s,
                          is_active = %s, updated_at = %s WHERE id = %s
                   RETURNING id, email, full_name, role::text AS role,
                             institution_id, is_active, password_hash""",
                (role, institution_id, active, at, target_id),
            ).fetchone()
            conn.execute(
                """INSERT INTO account_role_audit
                   (actor_user_id, target_user_id, old_role, new_role,
                    old_institution_id, new_institution_id, old_is_active, new_is_active, changed_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (actor_id, target_id, row["role"], role, row["institution_id"], institution_id,
                 row["is_active"], active, at),
            )
            conn.execute(
                """UPDATE account_session SET revoked_at = %s
                   WHERE user_id = %s AND revoked_at IS NULL""",
                (at, target_id),
            )
            conn.execute(
                """UPDATE account_invitation SET revoked_at = %s
                   WHERE user_id = %s AND used_at IS NULL AND revoked_at IS NULL""",
                (at, target_id),
            )
            return _public(updated)
    except ForeignKeyViolation as exc:
        raise AppError(code="INVALID_STAFF_INSTITUTION", message="The institution is invalid.", status_code=422) from exc


def issue_invitation(
    conn: Connection, *, actor_id: int, target_id: int, settings: Settings,
    at: datetime | None = None,
) -> dict[str, Any]:
    account_secret(settings)
    at = at or now_utc()
    with conn.transaction():
        user = conn.execute(
            f"SELECT {USER_COLUMNS} FROM app_user WHERE id = %s FOR UPDATE", (target_id,)
        ).fetchone()
        if user is None:
            raise _not_found()
        if user["password_hash"] is not None:
            raise AppError(code="ACCOUNT_ALREADY_ACTIVATED", message="This account already has a password.", status_code=409)
        conn.execute(
            """UPDATE account_invitation SET revoked_at = %s
               WHERE user_id = %s AND used_at IS NULL AND revoked_at IS NULL""",
            (at, target_id),
        )
        invitation_id, token, hashed = new_opaque_token()
        expires_at = at + timedelta(hours=settings.account_invite_hours)
        conn.execute(
            """INSERT INTO account_invitation
               (id, user_id, token_hash, created_by, created_at, expires_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (invitation_id, target_id, hashed, actor_id, at, expires_at),
        )
    return {"invitation_token": token, "expires_at": expires_at}


def get_candidate_profile(
    conn: Connection, *, candidate_id: int, actor: dict[str, Any]
) -> dict[str, Any]:
    role = actor["role"]
    if role == "candidate":
        if candidate_id != actor["id"]:
            raise AppError(code="FORBIDDEN", message="This candidate profile is not accessible.", status_code=403)
        scope_sql, params = "", ()
    elif role == "admin":
        scope_sql, params = "", ()
    elif role == "interviewer":
        scope_sql = """AND EXISTS (
            SELECT 1 FROM application a WHERE a.user_id = u.id
            AND a.status = 'interview_scheduled')"""
        params = ()
    else:
        raise AppError(code="FORBIDDEN", message="This role cannot access candidate dossiers.", status_code=403)
    row = conn.execute(
        """SELECT u.id, u.email, u.full_name, u.phone,
                  p.birth_year, p.city, p.nationality, p.current_level,
                  p.bac_section, p.bac_year, p.bac_average::text AS bac_average,
                  p.last_diploma, p.last_diploma_specialty, p.favorite_subjects,
                  p.interests, p.career_goal, p.constraints,
                  p.preferred_language::text AS preferred_language
           FROM app_user u JOIN candidate_profile p ON p.user_id = u.id
           WHERE u.id = %s AND u.role = 'candidate' """ + scope_sql,
        (candidate_id, *params),
    ).fetchone()
    if row is None:
        raise AppError(code="CANDIDATE_NOT_FOUND", message="The candidate was not found.", status_code=404)
    return row


def get_candidate_applications(conn: Connection, *, user_id: int) -> dict[str, Any]:
    rows = conn.execute(
        """SELECT a.id, a.program_id, p.name AS program_name, i.code AS institution_code,
                  a.status::text AS status, a.consent_at, a.submitted_at
           FROM application a JOIN program p ON p.id = a.program_id
           JOIN institution i ON i.id = p.institution_id
           WHERE a.user_id = %s ORDER BY a.created_at DESC, a.id DESC""",
        (user_id,),
    ).fetchall()
    return {"items": rows}
