"""SA-12: academic catalog tables

Revision ID: 0001_catalog
Revises:
Create Date: 2026-11-21
"""
from migrations.sql_file import drop, run_sql_file

revision = "0001_catalog"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file("catalog_schema.sql")


def downgrade() -> None:
    drop(
        tables=["admission_campaign", "pathway", "fee_rule", "tariff", "accepted_background",
                "admission_requirement", "specialization", "program", "institution"],
        types=["campaign_status", "fee_period", "student_category", "background_kind",
               "entry_level", "program_level"],
    )
