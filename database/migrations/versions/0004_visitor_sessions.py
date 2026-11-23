"""SA-25 visitor sessions

Revision ID: 0004_visitor_sessions
Revises: 0003_documents_sync
Create Date: 2026-11-23
"""
from migrations.sql_file import drop, run_sql_file

revision = "0004_visitor_sessions"
down_revision = "0003_documents_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("visitor_sessions_schema.sql")


def downgrade() -> None:
    drop(tables=["visitor_session_creation", "visitor_session"], types=[])
