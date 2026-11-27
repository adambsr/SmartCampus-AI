"""Simplify active roles without promoting legacy staff accounts.

Revision ID: 0008_simplify_roles
Revises: 0007_guest_account_link
"""
from migrations.sql_file import run_sql_file

revision = "0008_simplify_roles"
down_revision = "0007_guest_account_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("role_simplification_schema.sql")


def downgrade() -> None:
    raise RuntimeError("Role assignments require human review; automatic downgrade is unsupported")
