"""SA-29 transfer visitor conversations to candidate accounts.

Revision ID: 0007_guest_account_link
Revises: 0006_account_auth
"""
from migrations.sql_file import run_sql_file

revision = "0007_guest_account_link"
down_revision = "0006_account_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("guest_account_link_schema.sql")


def downgrade() -> None:
    raise RuntimeError("SA-29 ownership transfers are permanent; downgrade is intentionally unsupported")
