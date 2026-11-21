"""Helper used by the migrations: run one of the SQL files in database/schema/."""
from pathlib import Path

from alembic import op

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def run_sql_file(name: str) -> None:
    sql = (SCHEMA_DIR / name).read_text(encoding="utf-8-sig")
    # Alembic already wraps each migration in a transaction, so drop the file's own BEGIN/COMMIT.
    lines = [l for l in sql.splitlines() if l.strip().upper() not in ("BEGIN;", "COMMIT;")]
    op.get_bind().exec_driver_sql("\n".join(lines))


def drop(tables: list[str], types: list[str], extra: list[str] | None = None) -> None:
    for stmt in extra or []:
        op.execute(stmt)
    for t in tables:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for t in types:
        op.execute(f"DROP TYPE IF EXISTS {t}")
