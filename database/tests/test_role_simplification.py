"""Opt-in migration tests on an explicitly approved disposable local PostgreSQL.

Never reads .env, DATABASE_URL or TEST_DATABASE_URL. Requires both
SMARTCAMPUS_RUN_LOCAL_MIGRATION_TESTS=1 and SMARTCAMPUS_LOCAL_MIGRATION_URL.
The approved local database must already have pgvector installed in public.
Each test owns and removes only its randomly named schema.
"""
import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.skipif(
    os.environ.get("SMARTCAMPUS_RUN_LOCAL_MIGRATION_TESTS") != "1",
    reason="Disposable local migration execution requires explicit approval and opt-in",
)
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def db(monkeypatch):
    url = os.environ.get("SMARTCAMPUS_LOCAL_MIGRATION_URL", "")
    parsed = urlparse(url)
    if parsed.scheme not in ("postgresql", "postgres") or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("An explicitly approved disposable local PostgreSQL URL is required")
    # No implicit network target, dotenv loading, shared Neon or test branch.
    schema = "role_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace WHERE e.extname='vector' AND n.nspname='public'").fetchone():
            pytest.fail("The approved disposable database must have pgvector in public")
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        conn.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
        from alembic import command
        from alembic.config import Config
        import dotenv
        import sqlalchemy
        from sqlalchemy.pool import NullPool

        engine = sqlalchemy.create_engine(
            "postgresql+psycopg://",
            creator=lambda: psycopg.connect(url, options=f"-csearch_path={schema},public"),
            poolclass=NullPool,
        )
        monkeypatch.setenv("DATABASE_URL", "postgresql://offline:offline@invalid/offline")
        monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
        monkeypatch.setattr(sqlalchemy, "create_engine", lambda *args, **kwargs: engine)
        config = Config(str(ROOT / "database/alembic.ini"))

        def upgrade(revision):
            command.upgrade(config, revision)

        try:
            yield conn, upgrade
        finally:
            engine.dispose()
            conn.execute("SET search_path TO public")
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_empty_database_upgrades_through_the_full_chain(db):
    conn, upgrade = db
    upgrade("0008_simplify_roles")
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0008_simplify_roles"
    assert conn.execute("SELECT enum_range(NULL::user_role)::text").fetchone()[0] == "{candidate,interviewer,admin}"
    assert conn.execute("SELECT count(*) FROM app_user").fetchone()[0] == 0


def _legacy_data(conn):
    conn.execute("INSERT INTO institution(code,name) VALUES ('IIT','IIT'),('ISB','ISB')")
    conn.execute("INSERT INTO program(institution_id,code,name,level) VALUES (1,'DEMO','Demo','licence')")
    conn.execute("""INSERT INTO app_user(email,full_name,role,institution_id,password_hash,is_active) VALUES
        ('admin@example.com','Admin','admin',NULL,'synthetic-password-hash',true),
        ('academic@example.com','Academic','academic_staff',1,'preserved-synthetic-hash',true),
        ('direction@example.com','Direction','direction',NULL,NULL,false),
        ('candidate@example.com','Candidate','candidate',NULL,'candidate-synthetic-hash',true),
        ('interview@example.com','Interviewer','interviewer',NULL,'interview-synthetic-hash',true)""")
    conn.execute("INSERT INTO candidate_profile(user_id) VALUES (4)")
    conn.execute("INSERT INTO application(user_id,program_id) VALUES (4,1)")
    conn.execute("UPDATE application_history SET changed_by=2")
    conn.execute("""INSERT INTO recommendation(user_id,program_id,justification,status,reviewed_by)
        VALUES (4,1,'Preserve review','confirmed',2)""")
    conn.execute("""INSERT INTO account_role_audit(actor_user_id,target_user_id,old_role,new_role,old_is_active,new_is_active)
        VALUES (1,2,'direction','academic_staff',false,true)""")
    for user_id in (1,2,3,4,5):
        conn.execute("""INSERT INTO account_session(id,user_id,refresh_token_hash,expires_at)
            VALUES (%s,%s,%s,now()+interval '1 day')""", (uuid4(),user_id,str(user_id)*64))
        conn.execute("""INSERT INTO account_invitation(id,user_id,token_hash,created_by,expires_at)
            VALUES (%s,%s,%s,2,now()+interval '1 day')""", (uuid4(),user_id,str(user_id)*64))
    visitor, conversation, message = uuid4(), uuid4(), uuid4()
    conn.execute("""INSERT INTO visitor_session(id,created_at,last_activity_at,idle_expires_at,absolute_expires_at,refresh_token_hash)
        VALUES (%s,now(),now(),now()+interval '30 minutes',now()+interval '1 day',%s)""", (visitor,'v'*64))
    conn.execute("INSERT INTO conversation(id,visitor_session_id,user_id,channel,created_at) VALUES (%s,%s,4,'text',now())", (conversation,visitor))
    conn.execute("INSERT INTO conversation_message(id,conversation_id,role,content,created_at) VALUES (%s,%s,'user','Preserve history',now())", (message,conversation))


def test_obsolete_accounts_are_disabled_and_history_is_preserved(db):
    conn, upgrade = db
    upgrade("0007_guest_account_link")
    _legacy_data(conn)
    before = conn.execute("SELECT id,email,password_hash FROM app_user ORDER BY id").fetchall()
    upgrade("0008_simplify_roles")
    assert conn.execute("SELECT id,email,password_hash FROM app_user ORDER BY id").fetchall() == before
    assert conn.execute("SELECT id,role::text,is_active,institution_id FROM app_user ORDER BY id").fetchall() == [
        (1,'admin',True,None),(2,'interviewer',False,None),(3,'interviewer',False,None),
        (4,'candidate',True,None),(5,'interviewer',True,None),
    ]
    assert conn.execute("SELECT user_id FROM account_session WHERE revoked_at IS NOT NULL ORDER BY user_id").fetchall() == [(2,),(3,)]
    assert conn.execute("SELECT user_id FROM account_invitation WHERE revoked_at IS NOT NULL ORDER BY user_id").fetchall() == [(2,),(3,)]
    assert conn.execute("SELECT old_role,new_role,actor_user_id FROM account_role_audit WHERE id=1").fetchone() == ('direction','academic_staff',1)
    assert conn.execute("SELECT target_user_id,old_role,old_institution_id,old_is_active,actor_user_id FROM account_role_audit WHERE migration_reason='0008_simplify_roles' ORDER BY target_user_id").fetchall() == [(2,'academic_staff',1,True,None),(3,'direction',None,False,None)]
    assert conn.execute("SELECT reviewed_by FROM recommendation").fetchone()[0] == 2
    assert conn.execute("SELECT changed_by FROM application_history").fetchone()[0] == 2
    assert conn.execute("SELECT user_id,content FROM conversation c JOIN conversation_message m ON m.conversation_id=c.id").fetchone() == (4,'Preserve history')
    assert conn.execute("SELECT count(*) FROM program").fetchone()[0] == 1
    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
        conn.execute("UPDATE app_user SET role='academic_staff' WHERE id=2")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO account_role_audit(target_user_id,old_role,new_role,old_is_active,new_is_active) VALUES (2,'interviewer','admin',false,true)")


@pytest.mark.parametrize("failure", ["missing_admin", "enum_dependency"])
def test_migration_failures_roll_back_all_changes(db, failure):
    conn, upgrade = db
    upgrade("0007_guest_account_link")
    _legacy_data(conn)
    if failure == "missing_admin":
        conn.execute("UPDATE app_user SET is_active=false WHERE role='admin'")
    else:
        conn.execute("CREATE TABLE unexpected_dependency(role user_role)")
    with pytest.raises(DBAPIError):
        upgrade("0008_simplify_roles")
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0007_guest_account_link"
    assert conn.execute("SELECT role::text,is_active,institution_id FROM app_user WHERE id=2").fetchone() == ('academic_staff',True,1)
    assert conn.execute("SELECT count(*) FROM account_role_audit").fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM account_session WHERE revoked_at IS NOT NULL").fetchone()[0] == 0
