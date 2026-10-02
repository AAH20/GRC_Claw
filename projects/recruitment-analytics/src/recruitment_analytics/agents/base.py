"""Base agent class for recruitment analytics agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from recruitment_analytics.config.settings import get_settings

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R", bound=BaseModel)


class BaseAgent(ABC, Generic[T, R]):
    """Base class for all recruitment analytics agents.

    Uses LangChain DeepAgents pattern with structured output.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        self.settings = get_settings()
        self.model = model or self._default_model()

    def _default_model(self) -> BaseChatModel:
        """Create default LLM model."""
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            api_key=self.settings.openai_api_key or None,
        )

    @abstractmethod
    async def run(self, request: T) -> R:
        """Execute the agent with the given request.

        Args:
            request: The input request model.

        Returns:
            The agent response model.
        """
        ...

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the human-readable agent name."""
        ...
