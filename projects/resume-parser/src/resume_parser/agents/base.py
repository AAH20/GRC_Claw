"""Base agent class for resume parsing agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from resume_parser.config import Settings
from resume_parser.integrations import BaseLLMClient
from resume_parser.models import AgentResult

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all resume parsing agents.

    Each agent is responsible for extracting specific information from
    resume text using LLM-powered analysis.
    """

    def __init__(self, llm_client: BaseLLMClient, settings: Settings) -> None:
        """Initialize the base agent.

        Args:
            llm_client: LLM client for generating responses.
            settings: Application settings.
        """
        self._llm = llm_client
        self._settings = settings
        self._logger = logger.bind(agent=self.name)

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent name.

        Returns:
            str: Agent name.
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the agent description.

        Returns:
            str: Agent description.
        """
        ...

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent.

        Returns:
            str: System prompt.
        """
        ...

    @abstractmethod
    def _build_user_prompt(self, text: str, **kwargs: Any) -> str:
        """Build the user prompt for this agent.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context.

        Returns:
            str: User prompt.
        """
        ...

    @abstractmethod
    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response into structured data.

        Args:
            response: Raw LLM response.

        Returns:
            dict[str, Any]: Parsed structured data.
        """
        ...

    async def run(self, text: str, **kwargs: Any) -> AgentResult:
        """Execute the agent on the given text.

        Args:
            text: Resume text to analyze.
            **kwargs: Additional context for the agent.

        Returns:
            AgentResult: Result of the agent execution.
        """
        start_time = time.monotonic()
        self._logger.info("agent_started", text_length=len(text))

        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(text, **kwargs)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self._llm.agenerate(
                messages,
                max_tokens=self._settings.llm_max_tokens,
                temperature=self._settings.llm_temperature,
            )

            data = self._parse_response(response)
            execution_time = time.monotonic() - start_time

            self._logger.info(
                "agent_completed",
                execution_time=execution_time,
                data_keys=list(data.keys()),
            )

            return AgentResult(
                agent_name=self.name,
                success=True,
                data=data,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            execution_time = time.monotonic() - start_time
            self._logger.error("agent_failed", error=str(e), execution_time=execution_time)
            return AgentResult(
                agent_name=self.name,
                success=False,
                data={},
                error=str(e),
                execution_time_seconds=execution_time,
            )
