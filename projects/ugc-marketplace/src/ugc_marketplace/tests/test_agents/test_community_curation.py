"""Tests for community curation agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.community_curation import (ContentRankerAgent,
                                                       CurationExplainerAgent,
                                                       QualityFilterAgent,
                                                       TopicClusterAgent,
                                                       TrendSurferAgent)


@pytest.mark.asyncio
async def test_content_ranker_agent() -> None:
    """Test content ranker agent."""
    agent = ContentRankerAgent()
    status = agent.get_status()
    assert status["agent_name"] == "ContentRankerAgent"


@pytest.mark.asyncio
async def test_curation_explainer_agent() -> None:
    """Test curation explainer agent."""
    agent = CurationExplainerAgent()
    status = agent.get_status()
    assert status["agent_name"] == "CurationExplainerAgent"


@pytest.mark.asyncio
async def test_quality_filter_agent() -> None:
    """Test quality filter agent."""
    agent = QualityFilterAgent()
    status = agent.get_status()
    assert status["agent_name"] == "QualityFilterAgent"


@pytest.mark.asyncio
async def test_topic_cluster_agent() -> None:
    """Test topic cluster agent."""
    agent = TopicClusterAgent()
    status = agent.get_status()
    assert status["agent_name"] == "TopicClusterAgent"


@pytest.mark.asyncio
async def test_trend_surfer_agent() -> None:
    """Test trend surfer agent."""
    agent = TrendSurferAgent()
    status = agent.get_status()
    assert status["agent_name"] == "TrendSurferAgent"
