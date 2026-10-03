"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from recruitment_platform.main import create_app


@pytest.fixture
async def client() -> AsyncClient:
    """Create test client.

    Returns:
        Async test client.
    """
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient) -> None:
        """Test readiness check endpoint."""
        response = await client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestResumeParserEndpoints:
    """Test resume parser endpoints."""

    @pytest.mark.asyncio
    async def test_parse_resume(self, client: AsyncClient) -> None:
        """Test resume parsing endpoint."""
        response = await client.post(
            "/api/v1/resume-parser/parse",
            json={"text": "John Doe\njohn@example.com\nPython, AWS"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @pytest.mark.asyncio
    async def test_extract_contact(self, client: AsyncClient) -> None:
        """Test contact extraction endpoint."""
        response = await client.post(
            "/api/v1/resume-parser/extract-contact",
            json={"text": "Email: test@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestCandidateMatcherEndpoints:
    """Test candidate matcher endpoints."""

    @pytest.mark.asyncio
    async def test_match_candidates(self, client: AsyncClient) -> None:
        """Test candidate matching endpoint."""
        response = await client.post(
            "/api/v1/candidate-matcher/match",
            json={
                "candidates": [{"id": "1", "skills": ["Python"]}],
                "job_requirements": {"required_skills": ["Python"]},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestInterviewSchedulerEndpoints:
    """Test interview scheduler endpoints."""

    @pytest.mark.asyncio
    async def test_optimize_slots(self, client: AsyncClient) -> None:
        """Test slot optimization endpoint."""
        response = await client.post(
            "/api/v1/interview-scheduler/optimize-slots",
            json={"participants": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSkillsAssessorEndpoints:
    """Test skills assessor endpoints."""

    @pytest.mark.asyncio
    async def test_assess_skills(self, client: AsyncClient) -> None:
        """Test skills assessment endpoint."""
        response = await client.post(
            "/api/v1/skills-assessor/assess",
            json={"skill_assessments": {"Python": 0.9}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestBiasDetectorEndpoints:
    """Test bias detector endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_language(self, client: AsyncClient) -> None:
        """Test language analysis endpoint."""
        response = await client.post(
            "/api/v1/bias-detector/analyze-language",
            json={"text": "We need a young candidate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestTalentPoolEndpoints:
    """Test talent pool endpoints."""

    @pytest.mark.asyncio
    async def test_source_candidates(self, client: AsyncClient) -> None:
        """Test candidate sourcing endpoint."""
        response = await client.post(
            "/api/v1/talent-pool/source",
            json={"job_requirements": {}, "pool_criteria": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    @pytest.mark.asyncio
    async def test_cost_analysis(self, client: AsyncClient) -> None:
        """Test cost analysis endpoint."""
        response = await client.post(
            "/api/v1/analytics/cost-analysis",
            json={"hiring_data": {}, "cost_data": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestOnboardingEndpoints:
    """Test onboarding endpoints."""

    @pytest.mark.asyncio
    async def test_check_compliance(self, client: AsyncClient) -> None:
        """Test compliance check endpoint."""
        response = await client.post(
            "/api/v1/onboarding/check-compliance",
            json={"employee_data": {}, "jurisdiction": "US"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestJobDescriptionEndpoints:
    """Test job description endpoints."""

    @pytest.mark.asyncio
    async def test_check_ats(self, client: AsyncClient) -> None:
        """Test ATS compatibility endpoint."""
        response = await client.post(
            "/api/v1/job-description/check-ats",
            json={"job_description": "Software Engineer"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestEmployerBrandingEndpoints:
    """Test employer branding endpoints."""

    @pytest.mark.asyncio
    async def test_brand_strategy(self, client: AsyncClient) -> None:
        """Test brand strategy endpoint."""
        response = await client.post(
            "/api/v1/employer-branding/brand-strategy",
            json={"company_data": {}, "target_audience": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
