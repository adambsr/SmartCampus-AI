"""SA-14: documents and synchronisation tables

Revision ID: 0003_documents_sync
Revises: 0002_users_applications
Create Date: 2026-11-21
"""
from migrations.sql_file import drop, run_sql_file

revision = "0003_documents_sync"
down_revision = "0002_users_applications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("documents_sync_schema.sql")


def downgrade() -> None:
    drop(
        tables=["application_document", "sync_job", "document_chunk", "source_document"],
        types=["upload_kind", "sync_status", "document_status", "document_format", "document_type"],
    )
