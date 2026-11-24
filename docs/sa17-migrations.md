# SA-17: Database schema and Alembic migrations

The migration chain uses SQL files in `database/schema/` as the schema source of truth. Each Alembic revision applies one additive schema step:

| Revision | Scope | SQL file |
| --- | --- | --- |
| `0001_catalog` | Institution and program catalog | `catalog_schema.sql` |
| `0002_users_applications` | Users, candidate profiles, applications, history, recommendations | `users_applications_schema.sql` |
| `0003_documents_sync` | Source documents, chunks, uploads, sync jobs | `documents_sync_schema.sql` |
| `0004_visitor_sessions` | Anonymous visitor sessions and creation throttling | `visitor_sessions_schema.sql` |
| `0005_conversations` | Visitor-owned conversations and messages | `conversations_schema.sql` |
| `0006_account_auth` | Account sessions, invitations, role audit, auth throttling | `account_auth_schema.sql` |

The default Neon database is at `0006_account_auth`. Existing records were preserved when that additive migration was applied.

## Connection policy

Use `DATABASE_URL` only. The default target is the team's Neon branch (`neondb`). Do not select `TEST_DATABASE_URL` or `smartcampus-test`. Keep connection strings out of command output and source control.

The Alembic environment reads `DATABASE_URL` from the root `.env` or process environment. From the repository root, inspect the current revision with the pinned database dependencies:

```powershell
uv run --no-project --with-requirements database/requirements.txt python -m alembic -c database/alembic.ini current
```

Schema work must be additive: preserve applied revisions and create a new migration for later changes. Applying migrations to the default Neon database requires explicit approval. Never downgrade or reset the current database.

## Seeder

The demo seeder is destructive and separate from schema migrations. It truncates all application tables and now requires `--confirm-reset`. Do not run it against the default Neon database or any database containing records to preserve. See [SA-18 demo data](sa18-demo-data.md).
