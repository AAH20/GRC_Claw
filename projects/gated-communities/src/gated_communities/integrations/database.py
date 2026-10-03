"""Database integration client for tier management."""

from __future__ import annotations

from typing import Any

from tier_management.config.logging_config import get_logger
from tier_management.config.settings import get_settings

logger = get_logger(__name__)


class DatabaseClient:
    """Client for database operations.

    Provides async database connectivity for persisting tier
    management data. Supports PostgreSQL via asyncpg or SQLAlchemy.
    """

    def __init__(self, settings: Any = None) -> None:
        """Initialize the database client.

        Args:
            settings: Application settings. Uses global settings if None.
        """
        self.settings = settings or get_settings()
        self._engine: Any = None
        self._session_factory: Any = None

    async def connect(self) -> None:
        """Establish database connection."""
        try:
            from sqlalchemy.ext.asyncio import create_async_engine

            # Convert sync URL to async
            db_url = self.settings.database_url
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            self._engine = create_async_engine(
                db_url, echo=self.settings.is_development
            )
            logger.info("database_connected")
        except ImportError:
            logger.warning(
                "sqlalchemy_not_available", detail="Database features disabled"
            )

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            logger.info("database_disconnected")

    async def health_check(self) -> bool:
        """Check database connectivity.

        Returns:
            True if database is reachable, False otherwise.
        """
        if not self._engine:
            return False
        try:
            from sqlalchemy import text

            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False

    @property
    def engine(self) -> Any:
        """Get the SQLAlchemy engine instance.

        Returns:
            The async engine or None if not connected.
        """
        return self._engine
