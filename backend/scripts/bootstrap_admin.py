"""One-time, interactive first-admin password setup. Never run without DB-write approval.

From backend/: uv run python -m scripts.bootstrap_admin [admin@example.com]
Uses DATABASE_URL only. It never prints the password or connection string.
"""

import argparse
import getpass

import psycopg
from psycopg.rows import dict_row

from app.core.account_security import hash_password
from app.core.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Set the first existing administrator password once.")
    parser.add_argument("email", nargs="?", help="Existing active admin email; omit if exactly one eligible admin exists")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.database_url:
        parser.error("DATABASE_URL is required")
    password = getpass.getpass("New admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")
    if password != confirmation or not 12 <= len(password) <= 128:
        parser.error("Passwords must match and contain 12 to 128 characters")
    hashed = hash_password(password)
    del password, confirmation

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        with conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                ("smartcampus:last-admin:v1",),
            )
            existing = conn.execute(
                """SELECT COUNT(*) AS count FROM app_user
                   WHERE role = 'admin' AND is_active AND password_hash IS NOT NULL"""
            ).fetchone()["count"]
            if existing:
                parser.error("An active administrator already has a password; bootstrap is closed")
            if args.email:
                row = conn.execute(
                    """SELECT id, is_active, password_hash FROM app_user
                       WHERE lower(email) = lower(%s) AND role = 'admin' FOR UPDATE""",
                    (args.email,),
                ).fetchone()
            else:
                eligible = conn.execute(
                    """SELECT id, is_active, password_hash FROM app_user
                       WHERE role = 'admin' AND is_active AND password_hash IS NULL
                       ORDER BY id LIMIT 2 FOR UPDATE"""
                ).fetchall()
                if len(eligible) != 1:
                    parser.error("Specify an admin email when there is not exactly one eligible account")
                row = eligible[0]
            if row is None or not row["is_active"] or row["password_hash"] is not None:
                parser.error("The requested account is not an active, passwordless admin")
            conn.execute(
                "UPDATE app_user SET password_hash = %s, updated_at = now() WHERE id = %s",
                (hashed, row["id"]),
            )
    print("Initial administrator password set. No other account was changed.")


if __name__ == "__main__":
    main()
