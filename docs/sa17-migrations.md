# SA-17: Create tables and relations (Alembic migrations)

Status: 2026-11-21. Owner: Member A.

The 18 tables designed in SA-12, SA-13 and SA-14 are created by 3 Alembic migrations. Each migration runs the matching SQL file in `database/schema/`, so the SQL files stay the single source of truth.

| Revision | Creates | SQL file |
| --- | --- | --- |
| 0001_catalog | 9 catalog tables | catalog_schema.sql |
| 0002_users_applications | 5 user and application tables + status-history trigger | users_applications_schema.sql |
| 0003_documents_sync | 4 document and sync tables | documents_sync_schema.sql |

## Commands (from the repo root, with `.env` filled in)

| Goal | Command |
| --- | --- |
| Create or update the real database (`DATABASE_URL`) | `alembic -c database/alembic.ini upgrade head` |
| Same on the test database (`TEST_DATABASE_URL`) | `alembic -c database/alembic.ini -x db=test upgrade head` |
| See which revision a database is at | `alembic -c database/alembic.ini current` |
| Remove everything (test database only!) | `alembic -c database/alembic.ini -x db=test downgrade base` |

## Changing the schema later

1. Edit nothing that is already applied. Add a new migration instead:
   `alembic -c database/alembic.ini revision -m "short description"`
2. Write the change in `upgrade()` and its undo in `downgrade()`.
3. Apply it to the test database first, then to the real one.

## Tested

On PostgreSQL 16 + pgvector: `upgrade head` creates the 18 tables, `downgrade base` removes all tables and types, and `upgrade head` works again after that.
