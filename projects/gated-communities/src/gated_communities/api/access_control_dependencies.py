"""FastAPI dependencies for the access control service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel

from access_control.agents import (
    AccessAuditorAgent,
    AccessRecommenderAgent,
    PermissionEvaluatorAgent,
    PolicyEnforcerAgent,
    RoleManagerAgent,
)
from access_control.config import Settings
from access_control.config import get_settings as _get_settings


def get_settings() -> Settings:
    """Dependency to get application settings."""
    return _get_settings()


def get_llm(settings: Settings | None = None) -> BaseLanguageModel:
    """Get or create the LLM instance for agents.

    Args:
        settings: Optional settings override.

    Returns:
        A LangChain language model instance.
    """
    s = settings or _get_settings()
    return ChatOpenAI(
        model=s.llm_model,
        temperature=s.llm_temperature,
        max_tokens=s.llm_max_tokens,
        api_key=s.openai_api_key.get_secret_value() or None,
    )


def get_permission_evaluator(
    settings: Settings | None = None,
) -> PermissionEvaluatorAgent:
    """Get the permission evaluator agent."""
    s = settings or _get_settings()
    return PermissionEvaluatorAgent(llm=get_llm(s), settings=s)


def get_role_manager(
    settings: Settings | None = None,
) -> RoleManagerAgent:
    """Get the role manager agent."""
    s = settings or _get_settings()
    return RoleManagerAgent(llm=get_llm(s), settings=s)


def get_access_auditor(
    settings: Settings | None = None,
) -> AccessAuditorAgent:
    """Get the access auditor agent."""
    s = settings or _get_settings()
    return AccessAuditorAgent(llm=get_llm(s), settings=s)


def get_policy_enforcer(
    settings: Settings | None = None,
) -> PolicyEnforcerAgent:
    """Get the policy enforcer agent."""
    s = settings or _get_settings()
    return PolicyEnforcerAgent(llm=get_llm(s), settings=s)


def get_access_recommender(
    settings: Settings | None = None,
) -> AccessRecommenderAgent:
    """Get the access recommender agent."""
    s = settings or _get_settings()
    return AccessRecommenderAgent(llm=get_llm(s), settings=s)
