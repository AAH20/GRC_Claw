"""Tests for the content generator agents."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_generator.agents.atomizer import AtomizerAgent, AtomizerResult
from content_generator.agents.researcher import ResearcherAgent, ResearchResult
from content_generator.agents.seo_editor import SEOEditorAgent, SEOResult
from content_generator.agents.strategist import StrategistAgent, StrategyResult
from content_generator.agents.writer import WriterAgent, WriterResult


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def mock_serpapi_response() -> dict[str, Any]:
    """Mock SerpAPI response."""
    return {
        "organic_results": [
            {
                "title": "Test Result 1",
                "link": "https://example.com/1",
                "snippet": "This is a test snippet for result 1.",
                "position": 1,
            },
            {
                "title": "Test Result 2",
                "link": "https://example.com/2",
                "snippet": "This is a test snippet for result 2.",
                "position": 2,
            },
        ],
        "related_searches": [
            {"query": "test query 1"},
            {"query": "test query 2"},
        ],
        "people_also_ask": [
            {"question": "What is test?", "answer": "Test answer"},
        ],
    }


@pytest.fixture
def sample_research() -> ResearchResult:
    """Sample research result."""
    return ResearchResult(
        query="AI content generation",
        serp_data={"organic_results": []},
        competitors=[
            {"title": "Competitor 1", "url": "https://comp1.com", "snippet": "Snippet", "position": 1},
        ],
        trending_topics=["AI marketing", "Content automation"],
        keywords=["AI", "content", "generation"],
        summary="Top result: AI Content Generation — A comprehensive guide.",
    )


@pytest.fixture
def sample_strategy() -> StrategyResult:
    """Sample strategy result."""
    return StrategyResult(
        content_type="article",
        target_audience="Marketing professionals",
        tone="professional",
        angle="Data-driven insights",
        key_messages=["Message 1", "Message 2"],
        content_outline=[
            {"heading": "Introduction", "key_points": ["Hook", "Context"]},
            {"heading": "Main Content", "key_points": ["Data", "Examples"]},
        ],
        seo_recommendations={
            "primary_keyword": "AI content generation",
            "secondary_keywords": ["AI marketing", "content automation"],
            "meta_description": "Learn about AI content generation.",
            "suggested_title": "AI Content Generation Guide",
        },
        word_count_target=1500,
    )


@pytest.fixture
def sample_writer_result() -> WriterResult:
    """Sample writer result."""
    return WriterResult(
        title="AI Content Generation Guide",
        content="# AI Content Generation Guide\n\nThis is the content.",
        word_count=100,
        sections=[{"heading": "Introduction", "key_points": ["Hook"]}],
        meta_description="Learn about AI content generation.",
    )


@pytest.fixture
def sample_seo_result() -> SEOResult:
    """Sample SEO result."""
    return SEOResult(
        optimized_content="# AI Content Generation Guide\n\nOptimized content.",
        meta_title="AI Content Generation Guide",
        meta_description="Learn about AI content generation.",
        slug="ai-content-generation-guide",
        keyword_density={"AI content generation": 0.02},
        readability_score=85.0,
        seo_score=90.0,
        suggestions=["Add more internal links"],
    )


# ── ResearcherAgent Tests ─────────────────────────────────


class TestResearcherAgent:
    """Tests for the ResearcherAgent."""

    @pytest.mark.asyncio
    async def test_research_success(self, mock_serpapi_response: dict[str, Any]) -> None:
        """Test successful research."""
        agent = ResearcherAgent(serpapi_key="test-key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_serpapi_response
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await agent.research("AI content generation")

        assert result.query == "AI content generation"
        assert len(result.competitors) == 2
        assert len(result.trending_topics) == 2
        assert len(result.keywords) > 0
        assert result.summary != ""

    @pytest.mark.asyncio
    async def test_research_empty_query_raises(self) -> None:
        """Test that empty query raises ValueError."""
        agent = ResearcherAgent(serpapi_key="test-key")

        with pytest.raises(ValueError, match="Query must not be empty"):
            await agent.research("")

    @pytest.mark.asyncio
    async def test_research_api_failure_raises(self) -> None:
        """Test that API failure raises RuntimeError."""
        agent = ResearcherAgent(serpapi_key="test-key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("API Error")

            with pytest.raises(RuntimeError, match="SerpAPI request failed"):
                await agent.research("test query")


# ── StrategistAgent Tests ─────────────────────────────────


class TestStrategistAgent:
    """Tests for the StrategistAgent."""

    @pytest.mark.asyncio
    async def test_strategize_success(self, sample_research: ResearchResult) -> None:
        """Test successful strategy generation."""
        agent = StrategistAgent()

        mock_response = MagicMock()
        mock_response.content = """{
            "content_type": "article",
            "target_audience": "Marketing professionals",
            "tone": "professional",
            "angle": "Data-driven insights",
            "key_messages": ["Message 1", "Message 2"],
            "content_outline": [{"heading": "Intro", "key_points": ["Hook"]}],
            "seo_recommendations": {
                "primary_keyword": "AI content",
                "secondary_keywords": ["AI marketing"],
                "meta_description": "Test description",
                "suggested_title": "Test Title"
            },
            "word_count_target": 1500
        }"""

        with patch.object(agent._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await agent.strategize(sample_research)

        assert result.content_type == "article"
        assert result.target_audience == "Marketing professionals"
        assert result.tone == "professional"
        assert result.word_count_target == 1500
        assert len(result.key_messages) == 2

    @pytest.mark.asyncio
    async def test_strategize_invalid_json_raises(self, sample_research: ResearchResult) -> None:
        """Test that invalid JSON raises RuntimeError."""
        agent = StrategistAgent()

        mock_response = MagicMock()
        mock_response.content = "not valid json"

        with patch.object(agent._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response

            with pytest.raises(RuntimeError, match="invalid JSON"):
                await agent.strategize(sample_research)


# ── WriterAgent Tests ─────────────────────────────────────


class TestWriterAgent:
    """Tests for the WriterAgent."""

    @pytest.mark.asyncio
    async def test_write_success(self, sample_strategy: StrategyResult) -> None:
        """Test successful content writing."""
        agent = WriterAgent()

        mock_response = MagicMock()
        mock_response.content = "# Test Title\n\nThis is the test content."

        with patch.object(agent._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await agent.write(sample_strategy)

        assert result.title == "Test Title"
        assert "test content" in result.content
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_write_empty_strategy_raises(self) -> None:
        """Test that empty strategy raises ValueError."""
        agent = WriterAgent()
        empty_strategy = StrategyResult(
            content_type="article",
            target_audience="",
            tone="",
            angle="",
        )

        with pytest.raises(ValueError, match="content outline"):
            await agent.write(empty_strategy)


# ── SEOEditorAgent Tests ──────────────────────────────────


class TestSEOEditorAgent:
    """Tests for the SEOEditorAgent."""

    @pytest.mark.asyncio
    async def test_optimize_success(
        self,
        sample_writer_result: WriterResult,
        sample_strategy: StrategyResult,
    ) -> None:
        """Test successful SEO optimization."""
        agent = SEOEditorAgent()

        mock_response = MagicMock()
        mock_response.content = """# Optimized Title

Optimized content here.

```json
{
    "meta_title": "Optimized Title",
    "meta_description": "Optimized description",
    "slug": "optimized-title",
    "keyword_density": {"AI": 0.02},
    "readability_score": 85.0,
    "seo_score": 90.0,
    "suggestions": ["Add links"]
}
```"""

        with patch.object(agent._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await agent.optimize(sample_writer_result, sample_strategy)

        assert result.meta_title == "Optimized Title"
        assert result.seo_score == 90.0
        assert result.readability_score == 85.0
        assert len(result.suggestions) == 1

    @pytest.mark.asyncio
    async def test_optimize_empty_content_raises(self, sample_strategy: StrategyResult) -> None:
        """Test that empty content raises ValueError."""
        agent = SEOEditorAgent()
        empty_content = WriterResult(title="", content="", word_count=0)

        with pytest.raises(ValueError, match="Content must not be empty"):
            await agent.optimize(empty_content, sample_strategy)


# ── AtomizerAgent Tests ───────────────────────────────────


class TestAtomizerAgent:
    """Tests for the AtomizerAgent."""

    @pytest.mark.asyncio
    async def test_atomize_success(self, sample_seo_result: SEOResult) -> None:
        """Test successful content atomization."""
        agent = AtomizerAgent()

        mock_response = MagicMock()
        mock_response.content = """{
            "pieces": [
                {
                    "platform": "twitter",
                    "format": "tweet",
                    "content": "Test tweet content",
                    "character_count": 19,
                    "hashtags": ["#AI", "#Content"],
                    "call_to_action": "Learn more"
                },
                {
                    "platform": "linkedin",
                    "format": "post",
                    "content": "Test LinkedIn post",
                    "character_count": 18,
                    "hashtags": ["#AI"],
                    "call_to_action": "Connect"
                }
            ]
        }"""

        with patch.object(agent._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await agent.atomize(sample_seo_result)

        assert result.total_pieces == 2
        assert result.pieces[0].platform == "twitter"
        assert result.pieces[0].character_count == 19
        assert len(result.pieces[0].hashtags) == 2

    @pytest.mark.asyncio
    async def test_atomize_empty_content_raises(self) -> None:
        """Test that empty content raises ValueError."""
        agent = AtomizerAgent()
        empty_seo = SEOResult(optimized_content="", meta_title="", meta_description="", slug="")

        with pytest.raises(ValueError, match="Content must not be empty"):
            await agent.atomize(empty_seo)
