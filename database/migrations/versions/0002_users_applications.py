"""SA-13: users and applications tables

Revision ID: 0002_users_applications
Revises: 0001_catalog
Create Date: 2026-11-21
"""
from migrations.sql_file import drop, run_sql_file

revision = "0002_users_applications"
down_revision = "0001_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("users_applications_schema.sql")


def downgrade() -> None:
    drop(
        tables=["recommendation", "application_history", "application", "candidate_profile", "app_user"],
        types=["recommendation_source", "recommendation_status", "application_status",
               "preferred_language", "user_role"],
        extra=["DROP FUNCTION IF EXISTS log_application_status() CASCADE"],
    )
