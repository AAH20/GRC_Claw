"""Base agent class for all access control agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from access_control.config import Settings
    from langchain_core.language_models import BaseLanguageModel


InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentContext(BaseModel):
    """Context passed to agents during execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    settings: Settings
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all access control agents.

    Each agent wraps a LangChain DeepAgents instance and provides a typed
    interface for its specific domain responsibility.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        settings: Settings,
        *,
        name: str,
        description: str,
    ) -> None:
        self.llm = llm
        self.settings = settings
        self.name = name
        self.description = description
        self._agent: Any = None

    @abstractmethod
    async def run(
        self, payload: InputT, context: AgentContext | None = None
    ) -> OutputT:
        """Execute the agent with the given input payload.

        Args:
            payload: Typed input for the agent.
            context: Optional execution context.

        Returns:
            Typed output from the agent.
        """
        ...

    @abstractmethod
    def _build_agent(self) -> Any:
        """Build and return the underlying LangChain DeepAgents instance."""
        ...
