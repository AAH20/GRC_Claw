"""Database integration module."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fraud_detection.config.logging_config import get_logger
from fraud_detection.config.settings import get_settings

logger = get_logger(__name__)

_engine = None
_session_maker = None


async def get_db_session() -> AsyncSession:
    """Get a database session.

    Returns:
        AsyncSession instance.
    """
    global _engine, _session_maker
    settings = get_settings()

    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=settings.debug)
        _session_maker = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _session_maker() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables."""
    global _engine
    settings = get_settings()

    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=settings.debug)

    logger.info("Database initialized")


async def close_db() -> None:
    """Close database connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
