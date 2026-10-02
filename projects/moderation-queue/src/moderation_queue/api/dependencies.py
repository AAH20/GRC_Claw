"""API dependencies for the moderation queue application."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import Request

from moderation_queue.config import Settings, get_settings

logger = structlog.get_logger(__name__)


async def get_settings_dependency() -> Settings:
    """Dependency to get application settings.

    Returns:
        Settings: Application settings.
    """
    return get_settings()


async def get_logger(request: Request) -> structlog.BoundLogger:
    """Dependency to get a request-scoped logger.

    Args:
        request: FastAPI request object.

    Returns:
        BoundLogger: Request-scoped logger.
    """
    return logger.bind(
        request_id=getattr(request.state, "request_id", None),
        path=request.url.path,
        method=request.method,
    )


class AgentRegistry:
    """Registry for managing AI agent instances."""

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: dict[str, object] = {}

    def register(self, name: str, agent: object) -> None:
        """Register an agent.

        Args:
            name: Agent name.
            agent: Agent instance.
        """
        self._agents[name] = agent

    def get(self, name: str) -> object | None:
        """Get an agent by name.

        Args:
            name: Agent name.

        Returns:
            Agent instance or None if not found.
        """
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names.
        """
        return list(self._agents.keys())


_agent_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry.

    Returns:
        AgentRegistry: Global agent registry instance.
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


async def get_db() -> AsyncGenerator[None, None]:
    """Database session dependency.

    Yields:
        None: Database session placeholder.
    """
    # In production, this would yield an actual database session
    try:
        yield None
    finally:
        pass


async def get_redis() -> AsyncGenerator[None, None]:
    """Redis connection dependency.

    Yields:
        None: Redis connection placeholder.
    """
    # In production, this would yield an actual Redis connection
    try:
        yield None
    finally:
        pass
