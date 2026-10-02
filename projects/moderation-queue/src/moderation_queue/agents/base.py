"""Base agent class for moderation queue AI agents."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from moderation_queue.config import Settings, get_settings
from moderation_queue.models import AgentResponse

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    model: BaseLanguageModel | None = Field(default=None, description="LangChain model")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=1000, ge=1, description="Max tokens for response")
    timeout_seconds: int = Field(default=30, ge=1, description="Timeout in seconds")


class BaseAgent(ABC, Generic[T, R]):
    """Abstract base class for all moderation queue agents.

    This class provides the foundation for AI-powered agents that process
    moderation items using LangChain and LangGraph.

    Type Parameters:
        T: Input model type for the agent.
        R: Output model type for the agent.
    """

    def __init__(self, config: AgentConfig, settings: Settings | None = None) -> None:
        """Initialize the agent.

        Args:
            config: Agent configuration.
            settings: Application settings. Uses global settings if not provided.
        """
        self.config = config
        self.settings = settings or get_settings()
        self._model = config.model or self._create_default_model()

    def _create_default_model(self) -> BaseLanguageModel:
        """Create a default LangChain model.

        Returns:
            BaseLanguageModel: Configured language model.

        Raises:
            ValueError: If no API key is configured.
        """
        if not self.settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY must be configured to use AI agents. "
                "Set it in environment variables or .env file."
            )

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.settings.langchain_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.settings.openai_api_key,
        )

    @property
    def name(self) -> str:
        """Get agent name.

        Returns:
            str: Agent name.
        """
        return self.config.name

    @abstractmethod
    async def process(self, input_data: T) -> R:
        """Process input data and return result.

        Args:
            input_data: Input data for the agent.

        Returns:
            R: Processed result.
        """
        ...

    async def run(self, input_data: T) -> AgentResponse:
        """Execute the agent with timing and error handling.

        Args:
            input_data: Input data for the agent.

        Returns:
            AgentResponse: Standardized agent response.
        """
        start_time = time.monotonic()
        try:
            result = await self.process(input_data)
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data=result.model_dump(),
                processing_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            return AgentResponse(
                success=False,
                agent_name=self.name,
                error=str(exc),
                processing_time_ms=elapsed_ms,
            )

    def _build_messages(
        self, system_prompt: str, user_content: str
    ) -> list[SystemMessage | HumanMessage | AIMessage]:
        """Build LangChain message list.

        Args:
            system_prompt: System prompt for the agent.
            user_content: User message content.

        Returns:
            list: List of LangChain messages.
        """
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

    def _parse_structured_output(
        self, response: AIMessage, output_model: type[R]
    ) -> R:
        """Parse structured output from AI response.

        Args:
            response: AI message response.
            output_model: Pydantic model to parse into.

        Returns:
            R: Parsed output model.
        """
        if hasattr(response, "content") and isinstance(response.content, str):
            return output_model.model_validate_json(response.content)
        return output_model.model_validate(response)

    def get_metadata(self) -> dict[str, Any]:
        """Get agent metadata.

        Returns:
            dict: Agent metadata.
        """
        return {
            "name": self.name,
            "description": self.config.description,
            "model": self.settings.langchain_model,
            "temperature": self.config.temperature,
        }
