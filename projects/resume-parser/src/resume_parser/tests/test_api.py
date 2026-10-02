"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from resume_parser.tests.conftest import MockLLMClient


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test basic health check.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient) -> None:
        """Test detailed health check.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "details" in data


class TestParseEndpoints:
    """Test cases for parsing endpoints."""

    @pytest.mark.asyncio
    async def test_parse_text_success(
        self, client: AsyncClient, mock_llm: MockLLMClient
    ) -> None:
        """Test successful text parsing.

        Args:
            client: Test HTTP client.
            mock_llm: Mock LLM client.
        """
        mock_llm.add_response(
            '{"contact": {"full_name": "John Doe"}, "skills": [], "experience": [], "education": []}'
        )
        response = await client.post(
            "/api/v1/parse/text",
            json={"text": "John Doe's resume content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "resume_id" in data

    @pytest.mark.asyncio
    async def test_parse_text_empty(
        self, client: AsyncClient
    ) -> None:
        """Test parsing with empty text.

        Args:
            client: Test HTTP client.
        """
        response = await client.post(
            "/api/v1/parse/text",
            json={"text": ""},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_parse_text_missing_field(
        self, client: AsyncClient
    ) -> None:
        """Test parsing with missing text field.

        Args:
            client: Test HTTP client.
        """
        response = await client.post(
            "/api/v1/parse/text",
            json={},
        )
        assert response.status_code == 422


class TestResumeEndpoints:
    """Test cases for resume CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_resumes_empty(self, client: AsyncClient) -> None:
        """Test listing resumes when empty.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/resumes")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_get_resume_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent resume.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/resumes/non-existent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_resume_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent resume.

        Args:
            client: Test HTTP client.
        """
        response = await client.delete("/api/v1/resumes/non-existent-id")
        assert response.status_code == 404


class TestAgentEndpoints:
    """Test cases for agent endpoints."""

    @pytest.mark.asyncio
    async def test_list_agents(self, client: AsyncClient) -> None:
        """Test listing agents.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 5

    @pytest.mark.asyncio
    async def test_get_agent_info(self, client: AsyncClient) -> None:
        """Test getting agent info.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/agents/contact_extractor")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ContactExtractorAgent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent agent.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/agents/non_existent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_agent(
        self, client: AsyncClient, mock_llm: MockLLMClient
    ) -> None:
        """Test running a specific agent.

        Args:
            client: Test HTTP client.
            mock_llm: Mock LLM client.
        """
        mock_llm.add_response('{"full_name": "Jane Doe"}')
        response = await client.post(
            "/api/v1/agents/contact_extractor/run",
            json={"text": "Jane Doe's resume"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "ContactExtractorAgent"
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_run_agent_not_found(self, client: AsyncClient) -> None:
        """Test running non-existent agent.

        Args:
            client: Test HTTP client.
        """
        response = await client.post(
            "/api/v1/agents/non_existent/run",
            json={"text": "test"},
        )
        assert response.status_code == 404


class TestStatsEndpoints:
    """Test cases for stats endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient) -> None:
        """Test getting service stats.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_resumes_parsed" in data
        assert "active_agents" in data


class TestUtilityEndpoints:
    """Test cases for utility endpoints."""

    @pytest.mark.asyncio
    async def test_get_file_types(self, client: AsyncClient) -> None:
        """Test getting supported file types.

        Args:
            client: Test HTTP client.
        """
        response = await client.get("/api/v1/file-types")
        assert response.status_code == 200
        data = response.json()
        assert "supported_types" in data
        assert "pdf" in data["supported_types"]
