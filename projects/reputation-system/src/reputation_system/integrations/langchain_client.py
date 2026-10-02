"""LangChain integration client for LLM interactions."""

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from reputation_system.config.settings import Settings, get_settings


class LangChainClient:
    """Client for interacting with LangChain and LLM providers."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the LangChain client.

        Args:
            settings: Application settings.
        """
        self.settings = settings or get_settings()
        self._llm: BaseLanguageModel | None = None

    async def initialize(self) -> None:
        """Initialize the LLM connection."""
        if not self.settings.OPENAI_API_KEY:
            return

        try:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(
                model=self.settings.OPENAI_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
                temperature=0.1,
                max_tokens=1024,
            )
        except ImportError:
            pass

    async def generate(
        self,
        prompt: str,
        system_message: str | None = None,
    ) -> str:
        """Generate a response using the LLM.

        Args:
            prompt: User prompt.
            system_message: Optional system message.

        Returns:
            Generated response text.

        Raises:
            RuntimeError: If LLM is not initialized.
        """
        if not self._llm:
            raise RuntimeError("LLM not initialized. Call initialize() first.")

        messages: list[BaseMessage] = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        response = await self._llm.ainvoke(messages)
        return str(response.content)

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_message: str | None = None,
    ) -> BaseModel:
        """Generate a structured response using the LLM.

        Args:
            prompt: User prompt.
            response_model: Pydantic model for structured output.
            system_message: Optional system message.

        Returns:
            Structured response.

        Raises:
            RuntimeError: If LLM is not initialized.
        """
        if not self._llm:
            raise RuntimeError("LLM not initialized. Call initialize() first.")

        structured_llm = self._llm.with_structured_output(response_model)
        messages: list[BaseMessage] = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        result = await structured_llm.ainvoke(messages)
        return result

    async def health_check(self) -> dict[str, Any]:
        """Check LLM connection health.

        Returns:
            Health status dictionary.
        """
        return {
            "initialized": self._llm is not None,
            "model": self.settings.OPENAI_MODEL if self._llm else None,
        }
