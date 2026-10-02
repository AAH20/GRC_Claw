"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

    from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
    from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
    from candidate_matcher.agents.match_explainer import MatchExplainerAgent
    from candidate_matcher.agents.semantic_matcher import SemanticMatcherAgent
    from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent
    from candidate_matcher.integrations.embedding_client import BaseEmbeddingClient
    from candidate_matcher.integrations.llm_client import BaseLLMClient
    from candidate_matcher.integrations.vector_store import BaseVectorStore


async def get_llm_client(request: Request) -> BaseLLMClient:
    """Get the LLM client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The LLM client instance.
    """
    return request.app.state.llm_client


async def get_embedding_client(request: Request) -> BaseEmbeddingClient:
    """Get the embedding client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The embedding client instance.
    """
    return request.app.state.embedding_client


async def get_vector_store(request: Request) -> BaseVectorStore:
    """Get the vector store from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The vector store instance.
    """
    return request.app.state.vector_store


async def get_semantic_matcher(request: Request) -> SemanticMatcherAgent:
    """Get the semantic matcher agent from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The semantic matcher agent instance.
    """
    return request.app.state.semantic_matcher


async def get_skills_gap_analyzer(request: Request) -> SkillsGapAnalyzerAgent:
    """Get the skills gap analyzer agent from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The skills gap analyzer agent instance.
    """
    return request.app.state.skills_gap_analyzer


async def get_bias_aware_ranker(request: Request) -> BiasAwareRankerAgent:
    """Get the bias-aware ranker agent from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The bias-aware ranker agent instance.
    """
    return request.app.state.bias_aware_ranker


async def get_culture_fit_assessor(request: Request) -> CultureFitAssessorAgent:
    """Get the culture fit assessor agent from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The culture fit assessor agent instance.
    """
    return request.app.state.culture_fit_assessor


async def get_match_explainer(request: Request) -> MatchExplainerAgent:
    """Get the match explainer agent from app state.

    Args:
        request: FastAPI request object.

    Returns:
        The match explainer agent instance.
    """
    return request.app.state.match_explainer
