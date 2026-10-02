"""Tests for scoring agents."""

from __future__ import annotations

import pytest

from quality_scoring.agents import (
    EngagementScorerAgent,
    OriginalityScorerAgent,
    ReadabilityScorerAgent,
    SEOScorerAgent,
)
from quality_scoring.models.schemas import ScoreDimension


class TestReadabilityScorerAgent:
    """Tests for ReadabilityScorerAgent."""

    @pytest.fixture
    def agent(self):
        return ReadabilityScorerAgent()

    @pytest.mark.asyncio
    async def test_score_returns_dimension_score(self, agent):
        content = "This is a simple sentence. It is easy to read."
        result = await agent.score(content)
        assert result.success
        assert result.data is not None
        assert result.data.dimension == ScoreDimension.READABILITY
        assert 0 <= result.data.score <= 100

    @pytest.mark.asyncio
    async def test_score_complex_content(self, agent):
        content = "The multifaceted ramifications of the epistemological underpinnings necessitate a comprehensive elucidation of the ontological presuppositions inherent in the discourse."
        result = await agent.score(content)
        assert result.success
        assert result.data.score < 50  # Complex content should score lower

    @pytest.mark.asyncio
    async def test_score_simple_content(self, agent):
        content = "See Spot run. Run, Spot, run. Spot runs fast."
        result = await agent.score(content)
        assert result.success
        assert result.data.score > 70  # Simple content should score higher


class TestOriginalityScorerAgent:
    """Tests for OriginalityScorerAgent."""

    @pytest.fixture
    def agent(self):
        return OriginalityScorerAgent()

    @pytest.mark.asyncio
    async def test_score_returns_dimension_score(self, agent):
        content = "The unique perspective offers fresh insights into the topic."
        result = await agent.score(content)
        assert result.success
        assert result.data is not None
        assert result.data.dimension == ScoreDimension.ORIGINALITY
        assert 0 <= result.data.score <= 100

    @pytest.mark.asyncio
    async def test_detects_cliches(self, agent):
        content = "At the end of the day, this is a game changer that will revolutionize the industry."
        result = await agent.score(content)
        assert result.success
        assert result.data.metrics["cliche_count"] > 0


class TestEngagementScorerAgent:
    """Tests for EngagementScorerAgent."""

    @pytest.fixture
    def agent(self):
        return EngagementScorerAgent()

    @pytest.mark.asyncio
    async def test_score_returns_dimension_score(self, agent):
        content = "Discover the amazing secrets that will transform your life today!"
        result = await agent.score(content)
        assert result.success
        assert result.data is not None
        assert result.data.dimension == ScoreDimension.ENGAGEMENT
        assert 0 <= result.data.score <= 100

    @pytest.mark.asyncio
    async def test_detects_questions(self, agent):
        content = "What is the secret? How can you benefit? Why wait any longer?"
        result = await agent.score(content)
        assert result.success
        assert result.data.metrics["question_count"] >= 3


class TestSEOScorerAgent:
    """Tests for SEOScorerAgent."""

    @pytest.fixture
    def agent(self):
        return SEOScorerAgent()

    @pytest.mark.asyncio
    async def test_score_returns_dimension_score(self, agent):
        content = "# Title\n\nSome content with keywords and structure."
        result = await agent.score(content)
        assert result.success
        assert result.data is not None
        assert result.data.dimension == ScoreDimension.SEO
        assert 0 <= result.data.score <= 100

    @pytest.mark.asyncio
    async def test_detects_headings(self, agent):
        content = "# Main Title\n## Subtitle\n### Section"
        result = await agent.score(content)
        assert result.success
        assert result.data.metrics["h1_count"] == 1
        assert result.data.metrics["h2_count"] == 1
