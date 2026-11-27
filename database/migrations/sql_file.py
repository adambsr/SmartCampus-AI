"""Helper used by the migrations: run one of the SQL files in database/schema/."""
from pathlib import Path

from alembic import context, op

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def run_sql_file(name: str) -> None:
    sql = (SCHEMA_DIR / name).read_text(encoding="utf-8-sig")
    # Alembic already wraps each migration in a transaction, so drop the file's own BEGIN/COMMIT.
    lines = [l for l in sql.splitlines() if l.strip().upper() not in ("BEGIN;", "COMMIT;")]
    statement = "\n".join(lines)
    if context.is_offline_mode():
        op.execute(statement)
    else:
        # These scripts have no bound parameters. Omit even an empty parameter
        # collection so Psycopg leaves literal PostgreSQL '%' syntax untouched.
        op.get_bind().exec_driver_sql(statement, execution_options={"no_parameters": True})


def drop(tables: list[str], types: list[str], extra: list[str] | None = None) -> None:
    for stmt in extra or []:
        op.execute(stmt)
    for t in tables:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for t in types:
        op.execute(f"DROP TYPE IF EXISTS {t}")
