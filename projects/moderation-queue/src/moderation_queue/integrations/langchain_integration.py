"""LangChain integration for AI-powered moderation agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.messages import BaseMessage

from moderation_queue.config import Settings, get_settings


class LangChainIntegration:
    """Integration layer for LangChain and LangGraph.

    This class provides a unified interface for creating and managing
    LangChain models and chains used by the moderation agents.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the LangChain integration.

        Args:
            settings: Application settings.
        """
        self.settings = settings or get_settings()
        self._models: dict[str, BaseLanguageModel] = {}

    def create_chat_model(
        self,
        model_name: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 1000,
    ) -> BaseLanguageModel:
        """Create a LangChain chat model.

        Args:
            model_name: Model name. Uses default from settings if not provided.
            temperature: Model temperature. Uses default from settings if not provided.
            max_tokens: Maximum tokens for response.

        Returns:
            BaseLanguageModel: Configured chat model.

        Raises:
            ValueError: If no API key is configured.
        """
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be configured for LangChain integration")

        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=model_name or self.settings.langchain_model,
            temperature=temperature if temperature is not None else self.settings.langchain_temperature,  # noqa: E501
            max_tokens=max_tokens,
            api_key=self.settings.openai_api_key,
        )
        return model

    def create_structured_chain(
        self,
        model: BaseLanguageModel,
        output_schema: type[Any],
        system_prompt: str,
    ) -> Any:
        """Create a structured output chain.

        Args:
            model: LangChain model.
            output_schema: Pydantic model for structured output.
            system_prompt: System prompt for the chain.

        Returns:
            Configured chain with structured output.
        """
        return model.with_structured_output(output_schema)

    async def ainvoke_with_retry(
        self,
        chain: Any,
        messages: list[BaseMessage],
        max_retries: int = 3,
    ) -> Any:
        """Invoke a chain with retry logic.

        Args:
            chain: LangChain chain or model.
            messages: Input messages.
            max_retries: Maximum retry attempts.

        Returns:
            Chain output.

        Raises:
            Exception: If all retries fail.
        """
        last_exception: Exception | None = None
        for attempt in range(max_retries):
            try:
                return await chain.ainvoke(messages)
            except Exception as exc:
                last_exception = exc
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        if last_exception:
            raise last_exception
        raise RuntimeError("All retries failed")

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the configured model.

        Returns:
            dict: Model information.
        """
        return {
            "model_name": self.settings.langchain_model,
            "temperature": self.settings.langchain_temperature,
            "configured": self.settings.openai_api_key is not None,
        }
