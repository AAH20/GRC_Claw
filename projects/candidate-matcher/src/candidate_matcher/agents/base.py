"""Base agent class and shared utilities for all matching agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from candidate_matcher.config.exceptions import AgentExecutionError
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.integrations.llm_client import BaseLLMClient, create_llm_client

logger = get_logger(__name__)

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all matching agents.

    Provides common functionality for LLM interaction, error handling,
    and structured output generation.
    """

    def __init__(
        self,
        name: str,
        llm_client: BaseLLMClient | None = None,
        system_prompt: str = "",
    ) -> None:
        """Initialize the base agent.

        Args:
            name: Agent name for logging and identification.
            llm_client: LLM client for generating responses. Creates default if not provided.
            system_prompt: System prompt for the agent.
        """
        self._name = name
        self._llm_client = llm_client or create_llm_client()
        self._system_prompt = system_prompt

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    async def _generate(
        self,
        prompt: str,
        temperature: float = 0.1,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt to send.
            temperature: Sampling temperature.

        Returns:
            Generated response text.

        Raises:
            AgentExecutionError: If generation fails.
        """
        messages: list[BaseMessage] = []
        if self._system_prompt:
            messages.append(SystemMessage(content=self._system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self._llm_client.generate(messages, temperature=temperature)
            logger.debug(
                "agent_generated_response",
                agent=self._name,
                response_length=len(response),
            )
            return response
        except Exception as e:
            logger.error(
                "agent_generation_failed",
                agent=self._name,
                error=str(e),
            )
            raise AgentExecutionError(self._name, str(e)) from e

    async def _generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a structured response from the LLM.

        Args:
            prompt: User prompt to send.
            schema: JSON schema for structured output.

        Returns:
            Structured response as dictionary.

        Raises:
            AgentExecutionError: If generation fails.
        """
        messages: list[BaseMessage] = []
        if self._system_prompt:
            messages.append(SystemMessage(content=self._system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            response = await self._llm_client.generate_structured(messages, schema)
            logger.debug(
                "agent_generated_structured_response",
                agent=self._name,
                keys=list(response.keys()),
            )
            return response
        except Exception as e:
            logger.error(
                "agent_structured_generation_failed",
                agent=self._name,
                error=str(e),
            )
            raise AgentExecutionError(self._name, str(e)) from e

    @abstractmethod
    async def execute(self, **kwargs: Any) -> T:
        """Execute the agent's primary function.

        Args:
            **kwargs: Agent-specific input parameters.

        Returns:
            Agent-specific output.
        """
        ...
