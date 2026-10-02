"""Tests for the content generator integrations."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_generator.integrations.anthropic import AnthropicClient
from content_generator.integrations.openai import OpenAIClient
from content_generator.integrations.serpapi import SerpAPIClient


# ── OpenAIClient Tests ────────────────────────────────────


class TestOpenAIClient:
    """Tests for the OpenAI integration."""

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """Test successful text generation."""
        client = OpenAIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = "Generated text response"

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await client.generate([MagicMock()])

        assert result == "Generated text response"

    @pytest.mark.asyncio
    async def test_generate_json_success(self) -> None:
        """Test successful JSON generation."""
        client = OpenAIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = '{"key": "value", "number": 42}'

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await client.generate_json([MagicMock()])

        assert result == {"key": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_generate_json_with_code_block(self) -> None:
        """Test JSON generation with markdown code block."""
        client = OpenAIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = '```json\n{"key": "value"}\n```'

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await client.generate_json([MagicMock()])

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_generate_failure_raises(self) -> None:
        """Test that API failure raises RuntimeError."""
        client = OpenAIClient(api_key="test-key")

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("API Error")

            with pytest.raises(RuntimeError, match="OpenAI API call failed"):
                await client.generate([MagicMock()])


# ── AnthropicClient Tests ─────────────────────────────────


class TestAnthropicClient:
    """Tests for the Anthropic integration."""

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """Test successful text generation."""
        client = AnthropicClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = "Generated text from Claude"

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await client.generate([MagicMock()])

        assert result == "Generated text from Claude"

    @pytest.mark.asyncio
    async def test_generate_json_success(self) -> None:
        """Test successful JSON generation."""
        client = AnthropicClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = '{"result": "success"}'

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            result = await client.generate_json([MagicMock()])

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_generate_failure_raises(self) -> None:
        """Test that API failure raises RuntimeError."""
        client = AnthropicClient(api_key="test-key")

        with patch.object(client._llm, "ainvoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("API Error")

            with pytest.raises(RuntimeError, match="Anthropic API call failed"):
                await client.generate([MagicMock()])


# ── SerpAPIClient Tests ───────────────────────────────────


class TestSerpAPIClient:
    """Tests for the SerpAPI integration."""

    @pytest.mark.asyncio
    async def test_search_success(self) -> None:
        """Test successful search."""
        client = SerpAPIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic_results": [
                {"title": "Result 1", "link": "https://example.com", "snippet": "Snippet"}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            result = await client.search("test query")

        assert "organic_results" in result
        assert len(result["organic_results"]) == 1

    @pytest.mark.asyncio
    async def test_search_empty_query_raises(self) -> None:
        """Test that empty query raises ValueError."""
        client = SerpAPIClient(api_key="test-key")

        with pytest.raises(ValueError, match="Search query must not be empty"):
            await client.search("")

    @pytest.mark.asyncio
    async def test_search_http_error_raises(self) -> None:
        """Test that HTTP error raises RuntimeError."""
        client = SerpAPIClient(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("HTTP Error")

            with pytest.raises(RuntimeError, match="SerpAPI request failed"):
                await client.search("test")

    @pytest.mark.asyncio
    async def test_get_related_searches(self) -> None:
        """Test getting related searches."""
        client = SerpAPIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "related_searches": [
                {"query": "related 1"},
                {"query": "related 2"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            result = await client.get_related_searches("test")

        assert result == ["related 1", "related 2"]

    @pytest.mark.asyncio
    async def test_get_competitors(self) -> None:
        """Test getting competitors."""
        client = SerpAPIClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic_results": [
                {"title": "Comp 1", "link": "https://comp1.com", "snippet": "Snippet", "position": 1},
                {"title": "Comp 2", "link": "https://comp2.com", "snippet": "Snippet", "position": 2},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            result = await client.get_competitors("test")

        assert len(result) == 2
        assert result[0]["title"] == "Comp 1"
        assert result[0]["position"] == 1
