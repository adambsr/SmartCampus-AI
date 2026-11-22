"""PostgreSQL access shared by the API (psycopg 3 + a small connection pool).

Endpoints get a connection with ``Depends(get_db)``; rows come back as dicts.
"""
from collections.abc import Iterator

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import get_settings
from app.core.errors import AppError

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        url = get_settings().database_url
        if not url:
            raise AppError(
                code="DATABASE_NOT_CONFIGURED",
                message="DATABASE_URL is not set.",
                status_code=503,
            )
        # Neon closes idle connections, so test each one before handing it out
        # and drop connections that sat unused for more than 2 minutes.
        _pool = ConnectionPool(
            url,
            min_size=1,
            max_size=5,
            max_idle=120,
            check=ConnectionPool.check_connection,
            open=True,
            kwargs={"row_factory": dict_row},
        )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_db() -> Iterator[Connection]:
    with get_pool().connection() as conn:
        yield conn
