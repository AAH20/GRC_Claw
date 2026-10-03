"""LangChain DeepAgents integration adapter."""

from typing import Any

from langchain_core.language_models import BaseChatModel
from moderation_queue.config.settings import get_settings

settings = get_settings()


def get_llm() -> BaseChatModel | None:
    """Initialize and return the LLM for agent use.

    Returns None if no API key is configured, causing agents to fall back
    to heuristic implementations.
    """
    if not settings.openai_api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key,
        )
    except ImportError:
        return None


class LangChainAgentAdapter:
    """Adapter for integrating LangChain DeepAgents with the moderation queue."""

    def __init__(self, llm: BaseChatModel | None = None):
        self._llm = llm or get_llm()

    def get_agent(self, agent_type: str) -> Any:
        """Get an agent instance with the LLM injected."""
        from moderation_queue.agents.auto_moderator import AutoModeratorAgent
        from moderation_queue.agents.human_review_router import \
            HumanReviewRouterAgent
        from moderation_queue.agents.priority_scorer import PriorityScorerAgent

        agents = {
            "priority_scorer": PriorityScorerAgent,
            "auto_moderator": AutoModeratorAgent,
            "human_review_router": HumanReviewRouterAgent,
        }

        agent_cls = agents.get(agent_type)
        if agent_cls is None:
            raise ValueError(f"Unknown agent type: {agent_type}")

        return agent_cls(llm=self._llm)
