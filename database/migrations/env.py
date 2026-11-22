"""Alembic environment: picks the database from .env.

Default target is DATABASE_URL (neondb). Pass `-x db=test` to use TEST_DATABASE_URL.
"""
import os
from logging.config import fileConfig

from alembic import context
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

load_dotenv(find_dotenv(usecwd=True))

target = context.get_x_argument(as_dictionary=True).get("db", "main")
env_var = "TEST_DATABASE_URL" if target == "test" else "DATABASE_URL"
url = os.environ[env_var]
# SQLAlchemy needs to be told to use the psycopg 3 driver
if url.startswith("postgresql://"):
    url = "postgresql+psycopg://" + url[len("postgresql://"):]

# The schema is written in plain SQL (database/schema/*.sql), so there is no ORM metadata.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
