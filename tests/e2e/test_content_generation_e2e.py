"""E2E tests for the full Content Generation workflow.

Tests the complete lifecycle of content generation through the
Content Generator API: research, strategy, writing, SEO optimization,
and atomization.
"""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from conftest import (
    assert_health_check,
    assert_response_error,
    assert_response_success,
    generate_unique_id,
)


class TestContentGenerationE2E:
    """End-to-end test suite for content generation workflow."""

    def test_health_check(self, content_client: TestClient) -> None:
        """Verify the Content Generator service is healthy.

        Args:
            content_client: Test client for the Content Generator API.
        """
        assert_health_check(content_client)

    def test_generate_content_full_workflow(
        self, content_client: TestClient, sample_content_request: dict[str, Any]
    ) -> None:
        """Test the complete content generation workflow.

        Steps:
            1. Generate full content pipeline (research -> strategy -> write -> SEO -> atomize).
            2. Verify all pipeline stages produced output.
            3. Verify content structure and metadata.

        Args:
            content_client: Test client for the Content Generator API.
            sample_content_request: Sample content generation payload.
        """
        response = content_client.post(
            "/api/v1/content/generate", json=sample_content_request
        )
        result = assert_response_success(response)

        # Verify top-level structure
        assert result["query"] == sample_content_request["query"]
        assert result["language"] == sample_content_request["language"]

        # Verify strategy stage
        strategy = result["strategy"]
        assert "content_type" in strategy
        assert "target_audience" in strategy
        assert "tone" in strategy
        assert "angle" in strategy
        assert "key_messages" in strategy
        assert "content_outline" in strategy
        assert "seo_recommendations" in strategy
        assert "word_count_target" in strategy

        # Verify content stage
        content = result["content"]
        assert "title" in content
        assert "content" in content
        assert "word_count" in content
        assert "meta_description" in content
        assert content["word_count"] > 0

        # Verify SEO stage
        seo = result["seo"]
        assert "optimized_content" in seo
        assert "meta_title" in seo
        assert "meta_description" in seo
        assert "slug" in seo
        assert "keyword_density" in seo
        assert "readability_score" in seo
        assert "seo_score" in seo
        assert "suggestions" in seo

        # Verify atomization stage
        atomized = result["atomized"]
        assert "original_title" in atomized
        assert "pieces" in atomized
        assert "total_pieces" in atomized
        assert atomized["total_pieces"] > 0

        # Verify atomized pieces structure
        for piece in atomized["pieces"]:
            assert "platform" in piece
            assert "format" in piece
            assert "content" in piece
            assert "character_count" in piece
            assert "hashtags" in piece
            assert "call_to_action" in piece

    def test_atomize_content_workflow(self, content_client: TestClient) -> None:
        """Test the content atomization workflow.

        Args:
            content_client: Test client for the Content Generator API.
        """
        atomize_request: dict[str, Any] = {
            "content": "This is a comprehensive guide to AI-powered marketing automation. "
            "It covers everything from lead scoring to campaign optimization.",
            "title": "The Complete Guide to AI Marketing Automation",
            "meta_description": "Learn how AI transforms marketing automation",
            "platforms": ["twitter", "linkedin"],
            "language": "en",
        }
        response = content_client.post(
            "/api/v1/content/atomize", json=atomize_request
        )
        result = assert_response_success(response)

        assert result["original_title"] == atomize_request["title"]
        assert result["total_pieces"] > 0
        assert len(result["pieces"]) > 0

        for piece in result["pieces"]:
            assert "platform" in piece
            assert "format" in piece
            assert "content" in piece
            assert "character_count" in piece
            assert "hashtags" in piece
            assert "call_to_action" in piece

    def test_generate_content_different_types(
        self, content_client: TestClient
    ) -> None:
        """Test content generation for different content types.

        Args:
            content_client: Test client for the Content Generator API.
        """
        content_types = ["article", "blog_post", "social_media", "email"]
        for content_type in content_types:
            request: dict[str, Any] = {
                "query": f"Test query for {content_type}",
                "content_type": content_type,
                "language": "en",
                "location": "us",
            }
            response = content_client.post(
                "/api/v1/content/generate", json=request
            )
            result = assert_response_success(response)
            assert result["strategy"]["content_type"] == content_type

    def test_generate_content_different_languages(
        self, content_client: TestClient
    ) -> None:
        """Test content generation in different languages.

        Args:
            content_client: Test client for the Content Generator API.
        """
        languages = ["en", "es", "fr", "de"]
        for lang in languages:
            request: dict[str, Any] = {
                "query": "AI marketing automation",
                "content_type": "article",
                "language": lang,
                "location": "us",
            }
            response = content_client.post(
                "/api/v1/content/generate", json=request
            )
            result = assert_response_success(response)
            assert result["language"] == lang

    def test_generate_content_validation_error(
        self, content_client: TestClient
    ) -> None:
        """Test that content generation validates required fields.

        Args:
            content_client: Test client for the Content Generator API.
        """
        invalid_request: dict[str, Any] = {
            "query": "",
            "content_type": "article",
        }
        response = content_client.post(
            "/api/v1/content/generate", json=invalid_request
        )
        assert_response_error(response, expected_status=422)

    def test_atomize_content_validation_error(
        self, content_client: TestClient
    ) -> None:
        """Test that atomization validates required fields.

        Args:
            content_client: Test client for the Content Generator API.
        """
        invalid_request: dict[str, Any] = {
            "content": "",
        }
        response = content_client.post(
            "/api/v1/content/atomize", json=invalid_request
        )
        assert_response_error(response, expected_status=422)

    def test_generate_content_with_platforms(
        self, content_client: TestClient
    ) -> None:
        """Test content generation with specific platform targeting.

        Args:
            content_client: Test client for the Content Generator API.
        """
        request: dict[str, Any] = {
            "query": "AI marketing trends 2026",
            "content_type": "article",
            "language": "en",
            "location": "us",
            "platforms": ["twitter", "linkedin", "facebook"],
        }
        response = content_client.post(
            "/api/v1/content/generate", json=request
        )
        result = assert_response_success(response)

        platforms_in_result = {
            piece["platform"] for piece in result["atomized"]["pieces"]
        }
        assert "twitter" in platforms_in_result
        assert "linkedin" in platforms_in_result
        assert "facebook" in platforms_in_result
