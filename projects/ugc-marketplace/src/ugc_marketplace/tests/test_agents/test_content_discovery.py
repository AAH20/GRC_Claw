"""Tests for content discovery agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.content_discovery import (PersonalizationAgent,
                                                      RecommendationAgent,
                                                      SearchExplainerAgent,
                                                      SemanticSearchAgent,
                                                      TrendDetectorAgent)


@pytest.mark.asyncio
async def test_personalization_agent() -> None:
    """Test personalization agent."""
    agent = PersonalizationAgent()
    status = agent.get_status()
    assert status["agent_name"] == "PersonalizationAgent"


@pytest.mark.asyncio
async def test_recommendation_agent() -> None:
    """Test recommendation agent."""
    agent = RecommendationAgent()
    status = agent.get_status()
    assert status["agent_name"] == "RecommendationAgent"


@pytest.mark.asyncio
async def test_search_explainer_agent() -> None:
    """Test search explainer agent."""
    agent = SearchExplainerAgent()
    status = agent.get_status()
    assert status["agent_name"] == "SearchExplainerAgent"


@pytest.mark.asyncio
async def test_semantic_search_agent() -> None:
    """Test semantic search agent."""
    agent = SemanticSearchAgent()
    status = agent.get_status()
    assert status["agent_name"] == "SemanticSearchAgent"


@pytest.mark.asyncio
async def test_trend_detector_agent() -> None:
    """Test trend detector agent."""
    agent = TrendDetectorAgent()
    status = agent.get_status()
    assert status["agent_name"] == "TrendDetectorAgent"
