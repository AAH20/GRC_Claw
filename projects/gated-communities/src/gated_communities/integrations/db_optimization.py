"""Database query optimization utilities."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Database query optimization utilities."""

    @staticmethod
    def add_pagination(query: str, offset: int = 0, limit: int = 100) -> str:
        """Add pagination to query."""
        return f"{query} LIMIT {limit} OFFSET {offset}"

    @staticmethod
    def add_index_hint(query: str, index_name: str) -> str:
        """Add index hint to query."""
        return f"{query} /*+ INDEX({index_name}) */"

    @staticmethod
    def optimize_count(query: str) -> str:
        """Optimize count query."""
        # Replace SELECT * with SELECT 1 for count queries
        return query.replace("SELECT *", "SELECT 1")

    @staticmethod
    def add_query_timeout(query: str, timeout_ms: int = 5000) -> str:
        """Add query timeout."""
        return f"SET LOCAL statement_timeout = '{timeout_ms}ms'; {query}"


class ConnectionPool:
    """Database connection pool manager."""

    def __init__(self, pool_size: int = 20, max_overflow: int = 10) -> None:
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool = None

    async def initialize(self, database_url: str) -> None:
        """Initialize connection pool."""
        from sqlalchemy.ext.asyncio import create_async_engine

        self._pool = create_async_engine(
            database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info("connection_pool_initialized", pool_size=self.pool_size)

    async def dispose(self) -> None:
        """Dispose connection pool."""
        if self._pool:
            await self._pool.dispose()

    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        async with self._pool.connect() as conn:
            yield conn


class BulkInserter:
    """Efficient bulk data insertion."""

    def __init__(self, batch_size: int = 1000) -> None:
        self.batch_size = batch_size
        self._buffer = []

    async def add(self, record: dict[str, Any]) -> None:
        """Add record to buffer."""
        self._buffer.append(record)
        if len(self._buffer) >= self.batch_size:
            await self.flush()

    async def flush(self) -> None:
        """Flush buffer to database."""
        if not self._buffer:
            return

        # Use COPY for PostgreSQL or bulk insert
        records = self._buffer[:]
        self._buffer.clear()

        logger.info("bulk_insert", count=len(records))
        # Implementation depends on database backend
