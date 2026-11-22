# SmartCampus AI

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Access to the team's Neon PostgreSQL project

## Database setup (Windows)

### 1. Configure environment variables

From the repository root, create `.env` using `.env.example`.

Configure:

- `DATABASE_URL`: Neon PostgreSQL connection string.
- `TEST_DATABASE_URL`: connection string for the test database.

Never commit `.env` or share database credentials.

### 2. Create the database environment

From the repository root:

```powershell
uv venv database/.venv
```

### 3. Install database dependencies

```powershell
uv pip install --python database/.venv/Scripts/python.exe -r database/requirements.txt
```

### 4. Test database connections

```powershell
uv run --python database/.venv/Scripts/python.exe python database/check_db.py
```

The script checks both database connections and verifies PostgreSQL extensions, including `vector`.

### 5. Apply migrations

For the test database:

```powershell
uv run --python database/.venv/Scripts/python.exe alembic -c database/alembic.ini -x db=test upgrade head
```

Check the current migration:

```powershell
uv run --python database/.venv/Scripts/python.exe alembic -c database/alembic.ini -x db=test current
```

### 6. Load demo data (optional)

**Warning:** The seed script empties the existing tables before inserting demo data.

Only run against an approved test database:

```powershell
uv run --python database/.venv/Scripts/python.exe python database/seed/seed_demo.py --db test
```

Do not use `--db main` unless you have explicitly confirmed that the target database can safely be emptied.

## Neon

The project uses PostgreSQL hosted on Neon, with the pgvector extension.

Console: https://console.neon.tech/

Ask the database owner for access to the existing SmartCampus project.

## Environments

- `database/.venv`: migrations, database checks and seed scripts.
- `backend/.venv`: FastAPI and backend dependencies.

Keep these environments separate.
