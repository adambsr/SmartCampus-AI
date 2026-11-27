# SmartCampus AI

SmartCampus AI is a FastAPI and React application backed by PostgreSQL. It provides a public academic-program catalog and detail pages, candidate accounts and application/profile views, visitor conversations with consented transfer to candidate accounts, and role-restricted staff and admin workspaces. The frontend also includes authentication, account activation, staff provisioning, and candidate dossier views.

## Local setup

### Backend

From `backend/`, install the locked dependencies and start the API:

```powershell
uv sync
Copy-Item .env.example .env  # only when creating a new local env file
uv run fastapi dev
```

The API listens at `http://127.0.0.1:8000`. Configure `DATABASE_URL`, `VISITOR_SESSION_SECRET`, and a distinct `ACCOUNT_JWT_SECRET` in `backend/.env`. For local HTTP, `AUTH_COOKIE_SECURE=false` is allowed only with `ENVIRONMENT=development`. Never commit or print `.env` values.

### Frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

Vite serves the application at `http://localhost:5173` and proxies `/api` to the local backend at port 8000. The backend CORS configuration must allow `http://localhost:5173`.

## Database and migrations

The application uses `DATABASE_URL` exclusively for database access. The configured Neon database was at Alembic revision `0007_guest_account_link` when checked on 2026-11-27. The migration chain includes catalog, user/application, documents/sync, visitor session, conversation, account authentication, and guest-account linking schemas.

The consented conversation transfer endpoints require `0007_guest_account_link`; it is applied to the configured Neon database. Other database environments must apply it before using transfer.

Migrations are managed from the repository root with the pinned database requirements. For example:

```powershell
uv run --no-project --with-requirements database/requirements.txt python -m alembic -c database/alembic.ini current
```

Do not downgrade, reset, reseed, or run the demo seeder against the default Neon database. The SA-18 seeder truncates every application table. It now requires `--confirm-reset` and is intended only for a disposable demo database.

## Sign in

- Candidate: open `/register`, create an account, then sign in at `/login`.
- Admin: sign in with the provisioned admin account. The admin workspace is at `/staff`; account provisioning and invitations are at `/staff/users`.
- Staff: an admin creates a pending staff account, issues an invitation, and shares the returned one-time token with the recipient. The recipient opens `/activate`, sets a password, then signs in at `/login`.

Invitation delivery is manual; the system does not send email. See [SA-28 account authentication and roles](docs/sa28-auth-roles.md) and the [frontend guide](frontend/README.md) for routes and local setup.

## Documentation

- [SA-18 demo data and seeder](docs/sa18-demo-data.md)
- [SA-17 migrations](docs/sa17-migrations.md)
- [SA-28 authentication and role rules](docs/sa28-auth-roles.md)
- [SA-29 guest conversation transfer](docs/sa29-guest-account-link.md)
- [Backend guide](backend/README.md)
- [Frontend guide](frontend/README.md)
