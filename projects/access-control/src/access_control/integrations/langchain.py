"""LangChain integration for the access control service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

if TYPE_CHECKING:
    from access_control.config import Settings


class LangChainIntegration:
    """Integration with LangChain for LLM-powered agents.

    Provides a factory for creating LangChain language models and
    manages the lifecycle of LangChain components.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm: BaseLanguageModel | None = None

    def get_llm(self) -> BaseLanguageModel:
        """Get or create the LangChain language model.

        Returns:
            A LangChain language model instance.
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                api_key=self.settings.openai_api_key.get_secret_value() or None,
            )
        return self._llm

    def create_chain(self, system_prompt: str, human_template: str) -> Any:
        """Create a simple LangChain chain.

        Args:
            system_prompt: The system prompt for the chain.
            human_template: The human message template.

        Returns:
            A LangChain chain.
        """
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template),
        ])

        return prompt | self.get_llm()
