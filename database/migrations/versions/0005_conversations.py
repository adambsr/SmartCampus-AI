"""SA-26 visitor-owned text conversations

Revision ID: 0005_conversations
Revises: 0004_visitor_sessions
Create Date: 2026-11-23
"""
from migrations.sql_file import drop, run_sql_file

revision = "0005_conversations"
down_revision = "0004_visitor_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("conversations_schema.sql")


def downgrade() -> None:
    drop(tables=["conversation_message", "conversation"], types=[])
