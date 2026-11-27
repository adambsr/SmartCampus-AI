"""Migration execution regression tests without a PostgreSQL connection.

Use the real SQLAlchemy Psycopg dialect and Psycopg parameter parser. Only the
server transport is replaced: literal percent signs must reach Psycopg without
an empty parameter collection, which would incorrectly enable placeholder parsing.
"""
from io import StringIO
from pathlib import Path
import sys

from alembic.migration import MigrationContext
from alembic.operations import Operations
import psycopg
from psycopg.adapt import Transformer
from psycopg._queries import PostgresQuery
import pytest
from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migrations import sql_file


class ParserCursor:
    description = None
    rowcount = -1

    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, parameters=None):
        # This is Psycopg's actual conversion, including its ProgrammingError for
        # literal '%' SQL when parameters is {} or (). No server is contacted.
        query = PostgresQuery(Transformer())
        query.convert(statement, parameters)
        self.connection.calls.append((query.query, parameters))

    def close(self):
        pass


class ParserConnection:
    def __init__(self):
        self.closed = False
        self.broken = False
        self.calls = []

    def cursor(self):
        return ParserCursor(self)

    def rollback(self):
        pass

    def commit(self):
        pass

    def close(self):
        self.closed = True


@pytest.fixture
def driver():
    recording = ParserConnection()
    # Construct directly to avoid create_engine's server initialization/connect
    # hooks; execution still uses the real PostgreSQL dialect and Engine path.
    engine = Engine(
        StaticPool(creator=lambda: recording),
        PGDialect_psycopg(dbapi=psycopg),
        make_url("postgresql+psycopg://"),
    )
    try:
        with engine.connect() as connection:
            yield connection, recording
    finally:
        engine.dispose()


SCRIPTS = [
    "SELECT 'academic_staff' LIKE '%academic_staff%';",
    "SELECT format('%I', 'candidate_profile');",
    "DO $$ BEGIN RAISE EXCEPTION 'Found % obsolete roles', 2; END $$;",
    """SELECT 'academic_staff' LIKE '%''academic_staff''%';
SELECT format('%I', 'app_user');
DO $$ BEGIN RAISE EXCEPTION 'Expected one constraint, found %', 2; END $$;""",
]


def test_default_driver_execution_reproduces_percent_placeholder_error(driver):
    connection, _ = driver
    with pytest.raises(ProgrammingError, match="only '%s', '%b', '%t'"):
        connection.exec_driver_sql("SELECT 'academic_staff' LIKE '%''academic_staff''%';")


@pytest.mark.parametrize("statement", SCRIPTS)
def test_online_script_preserves_literal_percent_signs(tmp_path, monkeypatch, driver, statement):
    connection, recording = driver
    script = "BEGIN;\n" + statement + "\nCOMMIT;\n"
    (tmp_path / "percent.sql").write_text(script, encoding="utf-8-sig")
    monkeypatch.setattr(sql_file, "SCHEMA_DIR", tmp_path)
    monkeypatch.setattr(sql_file.context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(sql_file.op, "get_bind", lambda: connection)

    sql_file.run_sql_file("percent.sql")

    assert recording.calls == [(statement.encode("utf-8"), None)]
    # The option belongs to this script execution, not the shared connection.
    connection.exec_driver_sql("SELECT %s", (7,))
    assert recording.calls[-1] == (b"SELECT $1", (7,))


@pytest.mark.parametrize("script", sorted(sql_file.SCHEMA_DIR.glob("*.sql")), ids=lambda p: p.name)
def test_existing_migration_scripts_remain_parameterless(monkeypatch, driver, script):
    connection, recording = driver
    monkeypatch.setattr(sql_file.context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(sql_file.op, "get_bind", lambda: connection)

    sql_file.run_sql_file(script.name)

    assert len(recording.calls) == 1
    assert recording.calls[0][1] is None


def test_offline_sql_generation_preserves_literal_percent_signs(tmp_path, monkeypatch):
    statement = SCRIPTS[-1]
    (tmp_path / "percent.sql").write_text("BEGIN;\n" + statement + "\nCOMMIT;\n", encoding="utf-8-sig")
    monkeypatch.setattr(sql_file, "SCHEMA_DIR", tmp_path)
    monkeypatch.setattr(sql_file.context, "is_offline_mode", lambda: True)
    output = StringIO()
    context = MigrationContext.configure(
        url="postgresql+psycopg://",
        dialect_opts={"paramstyle": "named"},
        opts={"as_sql": True, "literal_binds": True, "output_buffer": output},
    )
    with Operations.context(context):
        sql_file.run_sql_file("percent.sql")

    # Alembic appends its own statement terminator, as it did before this fix.
    assert output.getvalue().strip() == statement + ";"
