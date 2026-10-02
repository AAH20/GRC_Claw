"""Shared base class and result types for all agents."""

from __future__ import annotations

import abc
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentResult:
    """Standardised output envelope returned by every agent.

    Attributes:
        agent: Name of the agent that produced the result.
        success: Whether the agent completed without error.
        data: Structured payload produced by the agent.
        error: Human-readable error message when ``success`` is ``False``.
        duration_ms: Wall-clock execution time in milliseconds.
        metadata: Arbitrary extra context about the run.
    """

    agent: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the result."""
        return {
            "agent": self.agent,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


class BaseAgent(abc.ABC):
    """Abstract base class implementing the agent contract.

    Subclasses must implement :meth:`run`, which receives a payload and
    returns a plain dictionary. Error handling, timing and envelope
    construction are handled here so subclasses stay focused on logic.
    """

    name: str = "base"
    description: str = "Abstract base agent"

    def __init__(self, *, model: str = "gpt-4", temperature: float = 0.7) -> None:
        """Initialise the agent.

        Args:
            model: LLM model identifier used by the agent.
            temperature: Sampling temperature for generation.
        """
        self.model = model
        self.temperature = temperature

    @abc.abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's core logic.

        Args:
            payload: Input parameters for the agent.

        Returns:
            A dictionary of results.

        Raises:
            ValueError: If required payload fields are missing.
        """

    def invoke(self, payload: dict[str, Any] | None = None) -> AgentResult:
        """Run the agent with timing and error handling.

        Args:
            payload: Optional input parameters; defaults to ``{}``.

        Returns:
            An :class:`AgentResult` describing the outcome.
        """
        payload = payload or {}
        start = time.perf_counter()
        try:
            data = self.run(payload)
            duration = (time.perf_counter() - start) * 1000
            logger.info("agent=%s status=ok duration_ms=%.2f", self.name, duration)
            return AgentResult(
                agent=self.name,
                success=True,
                data=data,
                duration_ms=duration,
                metadata={"model": self.model},
            )
        except Exception as exc:  # noqa: BLE001 - agent boundary must not raise
            duration = (time.perf_counter() - start) * 1000
            logger.exception("agent=%s status=error", self.name)
            return AgentResult(
                agent=self.name,
                success=False,
                error=str(exc),
                duration_ms=duration,
                metadata={"model": self.model},
            )

    @staticmethod
    def _require(payload: dict[str, Any], key: str) -> Any:
        """Return ``payload[key]`` or raise :class:`ValueError` if absent."""
        if key not in payload or payload[key] in (None, ""):
            raise ValueError(f"Missing required field: '{key}'")
        return payload[key]
