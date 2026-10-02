"""Base agent class for all Journey Orchestrator agents."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from core.config import AgentSettings
from core.exceptions import AgentError, AgentTimeoutError
from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    name: str
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0
    system_prompt: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, name: str, settings: AgentSettings, **overrides: Any) -> AgentConfig:
        """Create an agent config from application settings.

        Args:
            name: The agent name.
            settings: The agent settings from configuration.
            **overrides: Additional overrides for the config.

        Returns:
            A new AgentConfig instance.
        """
        return cls(
            name=name,
            model=overrides.get("model", settings.model),
            temperature=overrides.get("temperature", settings.temperature),
            max_tokens=overrides.get("max_tokens", settings.max_tokens),
            timeout=overrides.get("timeout", settings.timeout),
            retry_attempts=overrides.get("retry_attempts", settings.retry_attempts),
            retry_delay=overrides.get("retry_delay", settings.retry_delay),
            system_prompt=overrides.get("system_prompt", ""),
            metadata=overrides.get("metadata", {}),
        )


@dataclass
class AgentResult(Generic[T]):
    """Result returned by an agent execution."""

    success: bool
    data: T | None = None
    error: str | None = None
    agent_name: str = ""
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def failed(self) -> bool:
        """Check if the agent execution failed."""
        return not self.success


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all agents in the Journey Orchestrator.

    All agents must inherit from this class and implement the `run` method.
    The base class provides common functionality for LLM interaction,
    retry logic, timeout handling, and structured logging.
    """

    def __init__(self, config: AgentConfig, llm: BaseChatModel | None = None) -> None:
        """Initialize the base agent.

        Args:
            config: The agent configuration.
            llm: An optional pre-configured language model. If not provided,
                 a default model will be created from the config.
        """
        self.config = config
        self.llm = llm or self._create_llm()
        self._logger = get_logger(
            f"agent.{config.name}",
            agent_name=config.name,
            model=config.model,
        )

    def _create_llm(self) -> BaseChatModel:
        """Create a default language model from the configuration.

        Returns:
            A configured BaseChatModel instance.

        Raises:
            AgentError: If the model cannot be created.
        """
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
        except ImportError as e:
            raise AgentError(
                f"Failed to create LLM for agent {self.config.name}: {e}. "
                "Ensure langchain-openai is installed.",
                code="LLM_CREATION_ERROR",
            ) from e

    async def execute(self, input_data: dict[str, Any]) -> AgentResult[T]:
        """Execute the agent with the given input data.

        This method wraps the `run` method with timing, error handling,
        and retry logic.

        Args:
            input_data: The input data for the agent.

        Returns:
            An AgentResult containing the execution outcome.
        """
        start_time = time.monotonic()
        self._logger.info(
            "agent_execution_started",
            agent_name=self.config.name,
            input_keys=list(input_data.keys()),
        )

        last_error: Exception | None = None

        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                result = await self.run(input_data)
                execution_time = (time.monotonic() - start_time) * 1000

                self._logger.info(
                    "agent_execution_completed",
                    agent_name=self.config.name,
                    execution_time_ms=execution_time,
                    attempt=attempt,
                    success=result.success,
                )

                return AgentResult(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    agent_name=self.config.name,
                    execution_time_ms=execution_time,
                    tokens_used=result.tokens_used,
                    metadata=result.metadata,
                )

            except AgentTimeoutError:
                raise
            except Exception as e:
                last_error = e
                self._logger.warning(
                    "agent_execution_retry",
                    agent_name=self.config.name,
                    attempt=attempt,
                    max_attempts=self.config.retry_attempts,
                    error=str(e),
                )
                if attempt < self.config.retry_attempts:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay * attempt)

        execution_time = (time.monotonic() - start_time) * 1000
        error_msg = str(last_error) if last_error else "Unknown error"

        self._logger.error(
            "agent_execution_failed",
            agent_name=self.config.name,
            execution_time_ms=execution_time,
            error=error_msg,
        )

        return AgentResult(
            success=False,
            error=error_msg,
            agent_name=self.config.name,
            execution_time_ms=execution_time,
        )

    def _build_messages(self, input_data: dict[str, Any]) -> list[BaseMessage]:
        """Build the message list for the LLM call.

        Args:
            input_data: The input data to include in the user message.

        Returns:
            A list of messages for the LLM.
        """
        messages: list[BaseMessage] = []

        if self.config.system_prompt:
            messages.append(SystemMessage(content=self.config.system_prompt))

        user_content = self._format_input(input_data)
        messages.append(HumanMessage(content=user_content))

        return messages

    def _format_input(self, input_data: dict[str, Any]) -> str:
        """Format the input data as a string for the LLM.

        Args:
            input_data: The input data dictionary.

        Returns:
            A formatted string representation.
        """
        import json
        return json.dumps(input_data, indent=2, default=str)

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> AgentResult[T]:
        """Run the agent's core logic.

        This method must be implemented by all concrete agent classes.

        Args:
            input_data: The input data for the agent.

        Returns:
            An AgentResult containing the execution outcome.
        """
        ...
