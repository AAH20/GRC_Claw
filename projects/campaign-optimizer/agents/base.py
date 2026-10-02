"""Base agent class for all Campaign Optimizer agents."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from core.config import get_settings
from core.exceptions import AgentError, AgentMaxIterationsError, AgentTimeoutError
from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass
class AgentResult(Generic[T]):
    """Result from an agent execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    iterations: int = 0

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()


@dataclass
class AgentContext:
    """Context passed to agents during execution."""

    campaign_id: str
    task: str
    parameters: dict[str, Any] = field(default_factory=dict)
    parent_result: AgentResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all Campaign Optimizer agents."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        timeout: int = 120,
        max_iterations: int = 5,
        max_retries: int = 3,
    ) -> None:
        self._name = name
        self._description = description
        self._llm = llm
        self._tools = tools or []
        self._timeout = timeout
        self._max_iterations = max_iterations
        self._max_retries = max_retries
        self._status = AgentStatus.IDLE
        self._logger = get_logger(f"agent.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools.copy()

    async def execute(self, context: AgentContext) -> AgentResult[T]:
        self._status = AgentStatus.RUNNING
        self._logger.info(
            "agent_execution_started",
            agent=self._name,
            campaign_id=context.campaign_id,
            task=context.task,
        )

        try:
            result = await asyncio.wait_for(
                self._execute_with_retries(context),
                timeout=self._timeout,
            )
            self._status = AgentStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            self._logger.info(
                "agent_execution_completed",
                agent=self._name,
                campaign_id=context.campaign_id,
                duration=result.duration_seconds,
                success=result.success,
            )
            return result

        except asyncio.TimeoutError:
            self._status = AgentStatus.TIMED_OUT
            self._logger.error(
                "agent_execution_timed_out",
                agent=self._name,
                campaign_id=context.campaign_id,
                timeout=self._timeout,
            )
            return AgentResult(
                success=False,
                error=f"Agent timed out after {self._timeout}s",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

        except AgentMaxIterationsError:
            self._status = AgentStatus.FAILED
            raise

        except Exception as exc:
            self._status = AgentStatus.FAILED
            self._logger.error(
                "agent_execution_failed",
                agent=self._name,
                campaign_id=context.campaign_id,
                error=str(exc),
            )
            return AgentResult(
                success=False,
                error=str(exc),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

    async def _execute_with_retries(self, context: AgentContext) -> AgentResult[T]:
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._execute(context)
            except Exception as exc:
                last_error = exc
                self._logger.warning(
                    "agent_retry",
                    agent=self._name,
                    attempt=attempt,
                    max_retries=self._max_retries,
                    error=str(exc),
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** (attempt - 1))

        raise AgentError(
            f"Agent failed after {self._max_retries} attempts: {last_error}"
        )

    @abstractmethod
    async def _execute(self, context: AgentContext) -> AgentResult[T]:
        ...

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "status": self._status.value,
            "tools_count": len(self._tools),
            "timeout": self._timeout,
            "max_iterations": self._max_iterations,
        }
