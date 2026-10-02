"""Tests for API routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from job_description_optimizer.models import JobDescription


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAgentsEndpoints:
    """Tests for agent endpoints."""

    def test_list_agents(self, client: TestClient) -> None:
        """Test listing all agents."""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        names = [a["name"] for a in data]
        assert "bias_remover" in names
        assert "seo_optimizer" in names
        assert "ats_compatibility" in names
        assert "tone_analyzer" in names
        assert "keyword_optimizer" in names

    def test_get_agent_by_name(self, client: TestClient) -> None:
        """Test getting a specific agent."""
        response = client.get("/api/v1/agents/bias_remover")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "bias_remover"
        assert "capabilities" in data

    def test_get_nonexistent_agent(self, client: TestClient) -> None:
        """Test getting a non-existent agent."""
        response = client.get("/api/v1/agents/nonexistent")
        assert response.status_code == 404


class TestOptimizeEndpoints:
    """Tests for optimization endpoints."""

    @pytest.fixture
    def sample_jd(self) -> dict:
        """Create sample job description."""
        return {
            "title": "Software Engineer",
            "description": "We are looking for a software engineer to join our team. "
            "The ideal candidate should have strong technical skills.",
        }

    def test_optimize_bias(self, client: TestClient, sample_jd: dict) -> None:
        """Test bias optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                cleaned_text="Clean text",
                instances=[],
                overall_score=0.1,
                summary="No bias found",
            ))
            mock_get_agents.return_value = {"bias_remover": mock_agent}

            response = client.post("/api/v1/optimize/bias", json=sample_jd)
            assert response.status_code == 200

    def test_optimize_seo(self, client: TestClient, sample_jd: dict) -> None:
        """Test SEO optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                optimized_text="Optimized text",
                seo_score=0.8,
                readability_score=0.9,
            ))
            mock_get_agents.return_value = {"seo_optimizer": mock_agent}

            response = client.post("/api/v1/optimize/seo", json=sample_jd)
            assert response.status_code == 200

    def test_optimize_ats(self, client: TestClient, sample_jd: dict) -> None:
        """Test ATS optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                compatible_text="Compatible text",
                ats_score=0.7,
            ))
            mock_get_agents.return_value = {"ats_compatibility": mock_agent}

            response = client.post("/api/v1/optimize/ats", json=sample_jd)
            assert response.status_code == 200

    def test_optimize_tone(self, client: TestClient, sample_jd: dict) -> None:
        """Test tone optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                detected_tones=["professional"],
                primary_tone="professional",
                inclusivity_score=0.8,
            ))
            mock_get_agents.return_value = {"tone_analyzer": mock_agent}

            response = client.post("/api/v1/optimize/tone", json=sample_jd)
            assert response.status_code == 200

    def test_optimize_keywords(self, client: TestClient, sample_jd: dict) -> None:
        """Test keyword optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                optimized_text="Optimized text",
                industry_relevance=0.75,
            ))
            mock_get_agents.return_value = {"keyword_optimizer": mock_agent}

            response = client.post("/api/v1/optimize/keywords", json=sample_jd)
            assert response.status_code == 200

    def test_full_optimize(self, client: TestClient, sample_jd: dict) -> None:
        """Test full optimization endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agents = {}
            for name in ["bias_remover", "seo_optimizer", "ats_compatibility", "tone_analyzer", "keyword_optimizer"]:
                mock_agent = MagicMock()
                mock_agent.analyze = AsyncMock(return_value=MagicMock(
                    original_text=sample_jd["description"],
                    cleaned_text="Clean",
                    optimized_text="Optimized",
                    compatible_text="Compatible",
                    instances=[],
                    overall_score=0.1,
                    seo_score=0.8,
                    ats_score=0.7,
                    detected_tones=["professional"],
                    primary_tone="professional",
                    inclusivity_score=0.8,
                    industry_relevance=0.75,
                ))
                mock_agents[name] = mock_agent
            mock_get_agents.return_value = mock_agents

            request_data = {
                "job_description": sample_jd,
                "options": {},
            }
            response = client.post("/api/v1/optimize", json=request_data)
            assert response.status_code == 200

    def test_analyze_endpoint(self, client: TestClient, sample_jd: dict) -> None:
        """Test analysis endpoint."""
        with patch("job_description_optimizer.api.routes.get_agents") as mock_get_agents:
            mock_agent = MagicMock()
            mock_agent.analyze = AsyncMock(return_value=MagicMock(
                original_text=sample_jd["description"],
                overall_score=0.5,
            ))
            mock_get_agents.return_value = {"bias_remover": mock_agent}

            request_data = {
                "job_description": sample_jd,
                "analyses": ["bias"],
            }
            response = client.post("/api/v1/analyze", json=request_data)
            assert response.status_code == 200
