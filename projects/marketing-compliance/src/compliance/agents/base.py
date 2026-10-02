"""Base agent abstractions and shared models for the compliance platform."""

from __future__ import annotations

import abc
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Severity(StrEnum):
    """Severity levels for compliance violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(StrEnum):
    """Execution status for an agent run."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AgentResult(BaseModel):
    """Structured result returned by every agent run."""

    agent: str = Field(..., description="Name of the agent that produced the result")
    status: AgentStatus = Field(default=AgentStatus.SUCCEEDED)
    items: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None


class BaseAgent(abc.ABC):
    """Abstract base class for all compliance agents.

    Subclasses implement :meth:`run` and receive shared configuration at
    construction time. Error handling is centralised in :meth:`execute` so
    that every agent reports failures through a uniform :class:`AgentResult`.
    """

    name: str = "base"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise the agent.

        Args:
            config: Optional agent-specific configuration mapping.
        """
        self.config: dict[str, Any] = config or {}
        self.logger = logging.getLogger(f"compliance.agents.{self.name}")
        self._status: AgentStatus = AgentStatus.IDLE

    @property
    def status(self) -> AgentStatus:
        """Return the current execution status of the agent."""
        return self._status

    @abc.abstractmethod
    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Execute the agent's core logic.

        Args:
            payload: Input data for the agent.

        Returns:
            A structured :class:`AgentResult`.
        """
        raise NotImplementedError

    async def execute(self, payload: dict[str, Any]) -> AgentResult:
        """Run the agent with uniform error handling.

        Args:
            payload: Input data for the agent.

        Returns:
            A structured :class:`AgentResult`, marked ``FAILED`` if an
            exception was raised during :meth:`run`.
        """
        self._status = AgentStatus.RUNNING
        self.logger.info("Agent %s starting", self.name)
        try:
            result = await self.run(payload)
            result.finished_at = datetime.now(UTC)
            self._status = result.status
            self.logger.info("Agent %s finished with status %s", self.name, result.status)
            return result
        except Exception as exc:  # noqa: BLE001 - agents must never crash the pipeline
            self.logger.exception("Agent %s failed", self.name)
            self._status = AgentStatus.FAILED
            return AgentResult(
                agent=self.name,
                status=AgentStatus.FAILED,
                errors=[str(exc)],
                finished_at=datetime.now(UTC),
            )
