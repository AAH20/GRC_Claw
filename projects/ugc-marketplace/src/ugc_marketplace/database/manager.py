"""Database management utilities for UGC Marketplace."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from ugc_marketplace.config import get_settings
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections with pooling, retries, and health checks."""

    def __init__(
        self,
        database_url: str | None = None,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        query_timeout: int = 30,
        max_retries: int = 5,
        retry_delay: float = 0.1,
        retry_max_delay: float = 30.0,
        retry_jitter: float = 0.2,
    ) -> None:
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.query_timeout = query_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_max_delay = retry_max_delay
        self.retry_jitter = retry_jitter

        self.engine = create_async_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            echo=False,
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.slow_query_threshold_ms = 100
        self.query_metrics: dict[str, list[float]] = {}

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("Database health check failed", error=str(exc))
            return False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic retry."""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def execute_with_retry(
        self, operation: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute database operation with exponential backoff retry."""
        last_exception = None
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                if attempt < self.max_retries - 1:
                    jitter = delay * self.retry_jitter * (2 * random.random() - 1)
                    sleep_time = min(delay + jitter, self.retry_max_delay)
                    logger.warning(
                        "Database operation failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=round(sleep_time, 2),
                        error=str(exc),
                    )
                    await asyncio.sleep(sleep_time)
                    delay = min(delay * 2, self.retry_max_delay)

        logger.error(
            "Database operation failed after all retries",
            max_retries=self.max_retries,
            error=str(last_exception),
        )
        raise last_exception

    async def execute_with_timeout(
        self, session: AsyncSession, query: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute query with timeout."""
        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                session.execute(query, *args, **kwargs),
                timeout=self.query_timeout,
            )
            duration_ms = (time.monotonic() - start_time) * 1000

            if duration_ms > self.slow_query_threshold_ms:
                query_str = str(query)[:200]
                logger.warning(
                    "Slow query detected",
                    duration_ms=round(duration_ms, 2),
                    query=query_str,
                )
                self.query_metrics.setdefault(query_str, []).append(duration_ms)

            return result
        except TimeoutError:
            logger.error(
                "Query timeout", timeout=self.query_timeout, query=str(query)[:200]
            )
            raise

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")

    def get_metrics(self) -> dict[str, Any]:
        """Get database metrics."""
        metrics: dict[str, Any] = {
            "pool": {"size": self.pool_size, "max_overflow": self.max_overflow},
            "slow_queries": {},
        }
        for query, durations in self.query_metrics.items():
            if durations:
                metrics["slow_queries"][query] = {
                    "count": len(durations),
                    "avg_ms": round(sum(durations) / len(durations), 2),
                    "max_ms": round(max(durations), 2),
                }
        return metrics


_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
