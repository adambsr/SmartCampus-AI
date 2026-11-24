# smartcampus-backend

SmartCampus AI backend built with FastAPI, Psycopg, PyJWT, and Alembic. It serves the catalog and admissions APIs, visitor sessions and conversations, account authentication, candidate reads, and admin user provisioning.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)

## Install dependencies

From this directory:

```bash
uv sync
```

To create a local environment file, copy the example and adjust its values:

```powershell
Copy-Item .env.example .env
```

The `.env` file is ignored by Git. Configuration can also be supplied using
environment variables. In addition to `APP_NAME`, `APP_VERSION`,
`API_V1_PREFIX`, `ENVIRONMENT`, `APP_DEBUG`, and `CORS_ORIGINS`, the service needs
`DATABASE_URL`, `VISITOR_SESSION_SECRET`, and a distinct `ACCOUNT_JWT_SECRET`.
Account cookies are Secure by default; `AUTH_COOKIE_SECURE=false` is only for
local HTTP development. Never commit or print secret values.

## Start the development server

```bash
uv run fastapi dev
```

The API is served at http://127.0.0.1:8000. The FastAPI CLI discovers the root
`main.py`, which exposes the single app configured in `app.main`.

## Routes and documentation

- `GET /` — preserved FastAPI CLI starter response
- `GET /api/v1/health` — health check
- `/docs` — Swagger UI
- `/redoc` — ReDoc
- `/openapi.json` — OpenAPI schema

API endpoints live under `app/api`; business logic belongs in `app/services`;
shared settings and HTTP behavior live in `app/core`. Expected application errors,
HTTP errors, validation errors, and unexpected server errors use this response
shape:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Not Found",
    "details": [],
    "request_id": "request-id"
  }
}
```

Every response includes `X-Request-ID`. A caller-provided value is echoed; if it
is absent, the middleware generates a UUID.

The shared `ErrorResponse` schema is also attached to the documented 400, 404,
422, and 500 responses for API routes, so it appears in `/openapi.json` and the
interactive documentation.

## Run tests

```bash
uv run pytest
```

The test suite covers the preserved root route, health check, request IDs, common
error responses, and automatic API documentation.

## Database configuration

The backend connects to the team's Neon PostgreSQL database using `DATABASE_URL`.

When running the backend from the repository root, configure the root `.env` file with the connection string:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Never commit real database credentials. The `.env` file is ignored by Git.

The backend uses:
- Psycopg 3 for PostgreSQL connections.
- psycopg-pool for connection pooling.

Both dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

Database schema and demo data are managed in the repository's `database/`
directory. The default Neon branch is at migration `0006_account_auth`. The SA-18
seeder truncates application tables and requires `--confirm-reset`; never run it
against the default Neon database or records you need to preserve.

The API includes database-backed program and admission endpoints.


## Project structure

```text
main.py                         FastAPI CLI discovery entry point
app/
  api/v1/                       Versioned routes
  core/                         Settings, request IDs, and error handling
  schemas/                      Shared API schemas
  services/                     Business logic location
  main.py                       App factory and configured FastAPI app
tests/                          Automated tests
pyproject.toml                  Dependencies and pytest configuration
uv.lock                         Locked dependency versions
```

Database integration, migrations, visitor authentication, and account
authentication have been added after the original SA-7 foundation. External AI
services and SA-29 guest conversation linking remain future work.

## SA-28 account authentication

SA-28 adds account registration, login, refresh, logout, first-password activation,
role checks, and scoped candidate reads. Account JWTs use `ACCOUNT_JWT_SECRET`,
which must differ from `VISITOR_SESSION_SECRET`. Set it in the deployment environment;
do not use the placeholder from `.env.example`. The additive migration
`0006_account_auth` was applied to the default Neon `DATABASE_URL` on 2026-11-24.

The initial admin password was set privately on the default Neon database on
2026-11-24. The other nine demo accounts remain passwordless. The admin can
issue single-use invitations for those accounts. The one-time
`uv run python -m scripts.bootstrap_admin` command now refuses to run again.
The demo seed truncates data and must not be rerun.

See `../docs/sa28-auth-roles.md` for endpoints, access rules, and deployment notes.

## SA-29 guest conversation transfer

SA-29 adds consented, permanent transfer of an active visitor session's text
conversations to a candidate account. The transfer revokes visitor credentials;
the candidate can read and continue the same conversation IDs and messages after
the visitor session expires. Migration `0007_guest_account_link` is present in
source but has not been applied to Neon. See `../docs/sa29-guest-account-link.md`.
