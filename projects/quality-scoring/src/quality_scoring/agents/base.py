"""Base agent class for quality scoring agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel

from quality_scoring.config.settings import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AgentResult(BaseModel, Generic[T]):
    """Generic result wrapper for agent outputs."""

    success: bool = True
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseScoringAgent(ABC, Generic[T]):
    """Abstract base class for all scoring agents."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the scoring agent.

        Args:
            llm: Language model instance for agent reasoning.
            settings: Application settings.
        """
        self.llm = llm
        self.settings = settings or Settings()
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the human-readable agent name."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> str:
        """Return the scoring dimension this agent handles."""
        ...

    @abstractmethod
    async def score(self, content: str, **kwargs: Any) -> AgentResult[T]:
        """Score the given content.

        Args:
            content: The content text to score.
            **kwargs: Additional keyword arguments for scoring.

        Returns:
            AgentResult containing the score or error information.
        """
        ...

    async def execute_with_retry(
        self,
        func: Any,
        *args: Any,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retry logic.

        Args:
            func: The async function to execute.
            *args: Positional arguments for the function.
            max_retries: Maximum number of retries (defaults to settings).
            **kwargs: Keyword arguments for the function.

        Returns:
            The function result.

        Raises:
            Exception: If all retries are exhausted.
        """
        retries = max_retries or self.settings.agent_max_retries
        last_exception: Exception | None = None

        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                self.logger.warning(
                    "Agent %s attempt %d/%d failed: %s",
                    self.agent_name,
                    attempt + 1,
                    retries,
                    str(exc),
                )
                if attempt < retries - 1:
                    import asyncio

                    await asyncio.sleep(self.settings.agent_retry_delay * (2**attempt))

        raise last_exception or RuntimeError("All retries exhausted")
