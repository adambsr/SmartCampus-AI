"""SA-28 account authentication and role audit.

Revision ID: 0006_account_auth
Revises: 0005_conversations
Create Date: 2026-11-24
"""
from migrations.sql_file import drop, run_sql_file

revision = "0006_account_auth"
down_revision = "0005_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("account_auth_schema.sql")


def downgrade() -> None:
    drop(
        tables=["account_auth_attempt", "account_role_audit", "account_invitation", "account_session"],
        types=[],
    )
