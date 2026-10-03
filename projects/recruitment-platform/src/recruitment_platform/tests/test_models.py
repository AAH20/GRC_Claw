"""Tests for data models."""

from __future__ import annotations

from recruitment_platform.models.schemas import (AgentResponse, HealthResponse,
                                                 ResumeParseRequest,
                                                 ResumeParseResponse)


class TestSchemas:
    """Test Pydantic schemas."""

    def test_health_response(self) -> None:
        """Test health response schema."""
        response = HealthResponse(status="healthy", service="test")
        assert response.status == "healthy"
        assert response.service == "test"

    def test_agent_response(self) -> None:
        """Test agent response schema."""
        response = AgentResponse[str](success=True, data="test")
        assert response.success is True
        assert response.data == "test"

    def test_resume_parse_request(self) -> None:
        """Test resume parse request schema."""
        request = ResumeParseRequest(text="test resume")
        assert request.text == "test resume"
        assert request.extract_contact is True

    def test_resume_parse_response(self) -> None:
        """Test resume parse response schema."""
        response = ResumeParseResponse(
            contact={"email": "test@example.com"},
            education=[],
            experience=[],
            skills=["Python"],
        )
        assert response.contact["email"] == "test@example.com"
        assert "Python" in response.skills
