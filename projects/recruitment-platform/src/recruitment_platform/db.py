"""Database connection pool management for recruitment-platform."""

from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Default database URL — override via DATABASE_URL env var
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/recruitment_platform",
)


async def create_pool(
    dsn: str | None = None,
    min_size: int = 2,
    max_size: int = 10,
    **kwargs: Any,
) -> Any:
    """Create an async database connection pool.

    Args:
        dsn: Database connection string. Defaults to DATABASE_URL env var.
        min_size: Minimum number of connections in the pool.
        max_size: Maximum number of connections in the pool.
        **kwargs: Additional arguments passed to the pool creator.

    Returns:
        An async connection pool with acquire() and release() methods.

    Raises:
        ImportError: If asyncpg is not installed.
    """
    try:
        import asyncpg
    except ImportError as exc:
        raise ImportError(
            "asyncpg is required for database operations. "
            "Install it with: pip install asyncpg"
        ) from exc

    dsn = dsn or DEFAULT_DATABASE_URL

    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
        **kwargs,
    )

    logger.info(
        "Database pool created",
        min_size=min_size,
        max_size=max_size,
        dsn=dsn.replace(dsn.split("@")[-1], "***") if "@" in dsn else dsn,
    )

    return pool


async def close_pool(pool: Any) -> None:
    """Close a database connection pool.

    Args:
        pool: The pool to close.
    """
    if pool is not None:
        await pool.close()
        logger.info("Database pool closed")


async def fetch_one(pool: Any, query: str, *args: Any) -> dict[str, Any] | None:
    """Fetch a single row from the database.

    Args:
        pool: Database connection pool.
        query: SQL query string.
        *args: Query parameters.

    Returns:
        A dictionary representing the row, or None if no rows found.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_many(pool: Any, query: str, *args: Any) -> list[dict[str, Any]]:
    """Fetch multiple rows from the database.

    Args:
        pool: Database connection pool.
        query: SQL query string.
        *args: Query parameters.

    Returns:
        A list of dictionaries representing the rows.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def execute(pool: Any, query: str, *args: Any) -> str:
    """Execute a query that doesn't return rows.

    Args:
        pool: Database connection pool.
        query: SQL query string.
        *args: Query parameters.

    Returns:
        The status of the execution.
    """
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)
