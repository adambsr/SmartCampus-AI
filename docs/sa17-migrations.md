# SA-17: Database schema and Alembic migrations

The migration chain uses SQL files in `database/schema/` as the schema source of truth. Historical revisions remain immutable; the latest role simplification replaces the active enum while preserving records:

| Revision | Scope | SQL file |
| --- | --- | --- |
| `0001_catalog` | Institution and program catalog | `catalog_schema.sql` |
| `0002_users_applications` | Users, candidate profiles, applications, history, recommendations | `users_applications_schema.sql` |
| `0003_documents_sync` | Source documents, chunks, uploads, sync jobs | `documents_sync_schema.sql` |
| `0004_visitor_sessions` | Anonymous visitor sessions and creation throttling | `visitor_sessions_schema.sql` |
| `0005_conversations` | Visitor-owned conversations and messages | `conversations_schema.sql` |
| `0006_account_auth` | Account sessions, invitations, role audit, auth throttling | `account_auth_schema.sql` |
| `0007_guest_account_link` | Consented visitor-to-candidate conversation transfer (applied to default Neon) | `guest_account_link_schema.sql` |
| `0008_simplify_roles` | Three active roles, preserved historical audit values, disabled obsolete accounts (applied and read-only verified on default Neon) | `role_simplification_schema.sql` |

Default Neon is at `0008_simplify_roles`, matching the repository head, confirmed by authorized read-only verification on 2026-11-27. The project owner applied the migration; verification performed no database writes.

## Connection policy

Use `DATABASE_URL` only. The default target is the team's Neon branch (`neondb`). Do not select `TEST_DATABASE_URL` or `smartcampus-test`. Keep connection strings out of command output and source control.

The Alembic environment reads `DATABASE_URL` from the root `.env` or process environment. From the repository root, inspect the current revision with the pinned database dependencies:

```powershell
uv run --no-project --with-requirements database/requirements.txt python -m alembic -c database/alembic.ini current
```

Preserve data and historical migration inputs: preserve applied revisions and create a new migration for later changes. Applying migrations to the default Neon database requires explicit approval. Never downgrade or reset the current database.

## Seeder

The demo seeder is destructive and separate from schema migrations. It truncates all application tables and now requires `--confirm-reset`. Do not run it against the default Neon database or any database containing records to preserve. See [SA-18 demo data](sa18-demo-data.md).


## Default Neon application verified 2026 11 27

The project owner applied `0008_simplify_roles`; an authorized read-only, repeatable-read transaction through `DATABASE_URL` confirmed revision `0008_simplify_roles`, matching the repository head. No database writes or migrations were performed during verification.

- `user_role` contains exactly `candidate`, `interviewer`, `admin`; the obsolete academic institution constraint is absent.
- Two former academic_staff accounts and one former direction account are inactive interviewers with null institution assignments. Three system audit entries preserve their original role, institution and active state; audit role columns are text and all audit references are valid. There are no pre-existing ordinary role-audit rows in this database.
- No account sessions or unused invitations existed for the affected accounts at migration time; zero affected credentials remain unrevoked.
- All 10 original seeded account IDs are present among 11 current accounts: one usable active admin, six candidates and four interviewers. Six candidate profiles, five applications, 16 application-history records and five recommendations remain present, with no orphan actor/reviewer references.
- Three visitor sessions, three conversations and three messages remain present with valid ownership/message references and complete metadata on linked sessions. IIT and ISB and all 31 original program codes are present.

These checks establish current consistency and preservation of known account IDs/catalog codes; no pre-migration content snapshot was available for a byte-for-byte comparison. The rollout procedure below remains guidance for other environments; do not reapply or stamp the verified default database. Existing obsolete accounts still require explicit administrator review before reactivation.

## Role simplification rollout for other environments

`0008_simplify_roles` depends directly on `0007_guest_account_link`; one revision handles all changes in one transaction. It takes exclusive locks on the account, session, invitation and role-audit tables with a five-second lock timeout. The enum conversion can rewrite app_user, so stop and drain all account writers first. On timeout, missing usable admin in a nonempty database, an unexpected academic constraint, or an unrecognized enum dependency, the transaction fails and rolls back. Empty databases can install the full chain before first-admin bootstrap.

The migration changes audit role columns to checked historical text, permits explicitly marked system migration entries, records original role/institution/active values, disables obsolete-role accounts as interviewers, clears their institution assignment, and revokes their sessions and unused invitations. It removes the old academic constraint/default, replaces the enum with candidate/interviewer/admin, restores the candidate default and drops the retired type without CASCADE. It deletes no account or business record and leaves candidate, catalog and conversation tables untouched. Automatic downgrade is intentionally unsupported.

Before approved writes, verify DATABASE_URL targets the approved default Neon branch, the current revision is 0007_guest_account_link, actual enum dependencies and affected counts match expectations, and at least one active password-bearing admin exists. Never print credentials. Confirm a recovery point and prepare the matching backend/frontend release.

After explicit migration approval, from the repository root:

```powershell
uv run --no-project --with-requirements database/requirements.txt python -m alembic -c database/alembic.ini upgrade 0008_simplify_roles
```

Deploy the matching application before reopening account access. Verify revision, exact enum labels, preserved IDs/references/counts, inactive migrated accounts and revoked sessions/invitations. Smoke-test admin dossier access, interviewer stage restrictions, candidate ownership and guest transfer. Monitor existing logs for authorization/validation errors and unexpected 500 responses. Review disabled accounts individually through existing admin tools; never restore all accounts automatically.

Prefer a forward fix after successful rollout. A database restore requires separate approval and accounting for subsequent writes. Do not downgrade, reset or reseed Neon.

Offline verification uses a process-local dummy DATABASE_URL, disables dotenv loading, and generates `upgrade 0007_guest_account_link:0008_simplify_roles --sql` without connecting. Populated/fresh PostgreSQL migration execution still requires approval for a disposable local target; never run those tests against shared Neon or TEST_DATABASE_URL.

The opt-in tests in `database/tests/test_role_simplification.py` exercise fresh full-chain installation, populated upgrades, preserved identities/history/conversations, credential revocation, and rollback on missing admin or unexpected enum dependencies. They skip unless `SMARTCAMPUS_RUN_LOCAL_MIGRATION_TESTS=1` is explicitly set. Set `SMARTCAMPUS_LOCAL_MIGRATION_URL` privately to the approved disposable localhost PostgreSQL database, which must already have pgvector in public. Tests neither read .env nor use the shared database configuration; they create and clean only randomly named test schemas. After that separate approval, run:

```powershell
uv run --no-project --with-requirements database/requirements.txt --with "pytest>=8,<9" python -m pytest -q database/tests/test_role_simplification.py
```
