"""Tests for quality scoring agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.quality_scoring import (
    EngagementScorerAgent,
    ImprovementSuggesterAgent,
    OriginalityScorerAgent,
    ReadabilityScorerAgent,
    SEOScorerAgent,
)


@pytest.mark.asyncio
async def test_engagement_scorer_agent() -> None:
    """Test engagement scorer agent."""
    agent = EngagementScorerAgent()
    result = await agent.score("Test content for engagement scoring.")
    assert result.success is True


@pytest.mark.asyncio
async def test_improvement_suggester_agent() -> None:
    """Test improvement suggester agent."""
    agent = ImprovementSuggesterAgent()
    result = await agent.score("Short content.")
    assert result.success is True


@pytest.mark.asyncio
async def test_originality_scorer_agent() -> None:
    """Test originality scorer agent."""
    agent = OriginalityScorerAgent()
    result = await agent.score("Unique original content with fresh perspective.")
    assert result.success is True


@pytest.mark.asyncio
async def test_readability_scorer_agent() -> None:
    """Test readability scorer agent."""
    agent = ReadabilityScorerAgent()
    result = await agent.score("This is a simple sentence. It is easy to read.")
    assert result.success is True


@pytest.mark.asyncio
async def test_seo_scorer_agent() -> None:
    """Test SEO scorer agent."""
    agent = SEOScorerAgent()
    result = await agent.score(
        "# SEO Title\n\nContent with keywords for SEO optimization."
    )
    assert result.success is True
