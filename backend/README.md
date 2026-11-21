# smartcampus-backend

SmartCampus SA-7 backend foundation. This project keeps the FastAPI CLI generated
project as its foundation and adds the API, configuration, and error-handling
structure from the SA7 skeleton.

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
environment variables. The supported settings are `APP_NAME`, `APP_VERSION`,
`API_V1_PREFIX`, `ENVIRONMENT`, `APP_DEBUG`, and `CORS_ORIGINS` (comma-separated).

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

Database integration, migrations, authentication, and external AI services are
outside the scope of this SA-7 foundation.
