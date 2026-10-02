"""Tests for the content generator API endpoints."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from content_generator.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_agents() -> dict[str, Any]:
    """Mock all agent dependencies."""
    return {
        "researcher": MagicMock(),
        "strategist": MagicMock(),
        "writer": MagicMock(),
        "seo_editor": MagicMock(),
        "atomizer": MagicMock(),
    }


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "content-generator"


class TestGenerateEndpoint:
    """Tests for the content generation endpoint."""

    def test_generate_success(self, client: TestClient) -> None:
        """Test successful content generation."""
        with patch("content_generator.api.content.get_researcher") as mock_get_researcher, \
             patch("content_generator.api.content.get_strategist") as mock_get_strategist, \
             patch("content_generator.api.content.get_writer") as mock_get_writer, \
             patch("content_generator.api.content.get_seo_editor") as mock_get_seo, \
             patch("content_generator.api.content.get_atomizer") as mock_get_atomizer:

            # Mock researcher
            from content_generator.agents.researcher import ResearchResult
            mock_researcher = MagicMock()
            mock_researcher.research = AsyncMock(return_value=ResearchResult(
                query="AI content",
                serp_data={},
                competitors=[],
                trending_topics=[],
                keywords=["AI"],
                summary="Summary",
            ))
            mock_get_researcher.return_value = mock_researcher

            # Mock strategist
            from content_generator.agents.strategist import StrategyResult
            mock_strategist = MagicMock()
            mock_strategist.strategize = AsyncMock(return_value=StrategyResult(
                content_type="article",
                target_audience="Marketers",
                tone="professional",
                angle="Data-driven",
                key_messages=["Msg1"],
                content_outline=[{"heading": "Intro", "key_points": ["Hook"]}],
                seo_recommendations={"primary_keyword": "AI"},
                word_count_target=1000,
            ))
            mock_get_strategist.return_value = mock_strategist

            # Mock writer
            from content_generator.agents.writer import WriterResult
            mock_writer = MagicMock()
            mock_writer.write = AsyncMock(return_value=WriterResult(
                title="Test Title",
                content="# Test\n\nContent here.",
                word_count=50,
                sections=[],
                meta_description="Test",
            ))
            mock_get_writer.return_value = mock_writer

            # Mock SEO editor
            from content_generator.agents.seo_editor import SEOResult
            mock_seo = MagicMock()
            mock_seo.optimize = AsyncMock(return_value=SEOResult(
                optimized_content="# Test\n\nOptimized.",
                meta_title="Test Title",
                meta_description="Test",
                slug="test",
                keyword_density={"AI": 0.01},
                readability_score=80.0,
                seo_score=85.0,
                suggestions=[],
            ))
            mock_get_seo.return_value = mock_seo

            # Mock atomizer
            from content_generator.agents.atomizer import AtomizerResult, AtomizedContent
            mock_atomizer = MagicMock()
            mock_atomizer.atomize = AsyncMock(return_value=AtomizerResult(
                original_title="Test Title",
                pieces=[AtomizedContent(
                    platform="twitter",
                    format="tweet",
                    content="Test tweet",
                    character_count=10,
                    hashtags=["#AI"],
                    call_to_action="Learn more",
                )],
                total_pieces=1,
            ))
            mock_get_atomizer.return_value = mock_atomizer

            response = client.post(
                "/api/v1/content/generate",
                json={
                    "query": "AI content generation",
                    "content_type": "article",
                    "language": "en",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "AI content generation"
        assert data["language"] == "en"
        assert "strategy" in data
        assert "content" in data
        assert "seo" in data
        assert "atomized" in data

    def test_generate_missing_query_returns_422(self, client: TestClient) -> None:
        """Test that missing query returns validation error."""
        response = client.post(
            "/api/v1/content/generate",
            json={"content_type": "article"},
        )
        assert response.status_code == 422


class TestAtomizeEndpoint:
    """Tests for the atomize endpoint."""

    def test_atomize_success(self, client: TestClient) -> None:
        """Test successful atomization."""
        with patch("content_generator.api.content.get_atomizer") as mock_get_atomizer:
            from content_generator.agents.atomizer import AtomizerResult, AtomizedContent
            mock_atomizer = MagicMock()
            mock_atomizer.atomize = AsyncMock(return_value=AtomizerResult(
                original_title="Test",
                pieces=[AtomizedContent(
                    platform="twitter",
                    format="tweet",
                    content="Test",
                    character_count=4,
                    hashtags=[],
                    call_to_action="",
                )],
                total_pieces=1,
            ))
            mock_get_atomizer.return_value = mock_atomizer

            response = client.post(
                "/api/v1/content/atomize",
                json={
                    "content": "Test content to atomize",
                    "title": "Test Title",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_pieces"] == 1
        assert len(data["pieces"]) == 1

    def test_atomize_empty_content_returns_422(self, client: TestClient) -> None:
        """Test that empty content returns validation error."""
        response = client.post(
            "/api/v1/content/atomize",
            json={"content": ""},
        )
        assert response.status_code == 422


class TestTranslationEndpoints:
    """Tests for the translation endpoints."""

    def test_get_supported_languages(self, client: TestClient) -> None:
        """Test getting supported languages."""
        response = client.get("/api/v1/content/languages")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert len(data["languages"]) >= 2

    def test_translate_success(self, client: TestClient) -> None:
        """Test successful translation."""
        with patch("content_generator.api.translation.ChatAnthropic") as mock_llm_class:
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "مرحبا بالعالم"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm

            response = client.post(
                "/api/v1/content/translate",
                json={
                    "content": "Hello world",
                    "source_language": "en",
                    "target_language": "ar",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["source_language"] == "en"
        assert data["target_language"] == "ar"
        assert data["translated_content"] == "مرحبا بالعالم"

    def test_translate_same_language_returns_400(self, client: TestClient) -> None:
        """Test that same source and target language returns 400."""
        response = client.post(
            "/api/v1/content/translate",
            json={
                "content": "Hello",
                "source_language": "en",
                "target_language": "en",
            },
        )
        assert response.status_code == 400

    def test_translate_unsupported_language_returns_400(self, client: TestClient) -> None:
        """Test that unsupported language returns 400."""
        response = client.post(
            "/api/v1/content/translate",
            json={
                "content": "Hello",
                "source_language": "en",
                "target_language": "xx",
            },
        )
        assert response.status_code == 400
