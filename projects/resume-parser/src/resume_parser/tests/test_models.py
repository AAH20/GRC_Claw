"""Tests for Pydantic data models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from resume_parser.models import (
    AgentResult,
    ContactInfo,
    Education,
    Experience,
    FileType,
    HealthResponse,
    ParseRequest,
    ParseResponse,
    ParsedResume,
    ParsingStatus,
    Resume,
    Skill,
    StatsResponse,
)


class TestContactInfo:
    """Test cases for ContactInfo model."""

    def test_valid_contact(self) -> None:
        """Test creating valid contact info."""
        contact = ContactInfo(
            full_name="John Doe",
            email="john@example.com",
            phone="+1-555-123-4567",
        )
        assert contact.full_name == "John Doe"
        assert contact.email == "john@example.com"

    def test_invalid_email(self) -> None:
        """Test contact with invalid email."""
        contact = ContactInfo(full_name="John Doe", email="not-an-email")
        assert contact.email is None

    def test_required_fields(self) -> None:
        """Test that full_name is required."""
        with pytest.raises(ValidationError):
            ContactInfo()  # type: ignore


class TestSkill:
    """Test cases for Skill model."""

    def test_valid_skill(self) -> None:
        """Test creating valid skill."""
        skill = Skill(name="Python", category="technical", proficiency="advanced")
        assert skill.name == "Python"
        assert skill.category == "technical"

    def test_default_category(self) -> None:
        """Test default skill category."""
        skill = Skill(name="Python")
        assert skill.category == "other"


class TestExperience:
    """Test cases for Experience model."""

    def test_valid_experience(self) -> None:
        """Test creating valid experience."""
        exp = Experience(
            company="Tech Corp",
            title="Software Engineer",
            start_date="2020-01",
            is_current=True,
        )
        assert exp.company == "Tech Corp"
        assert exp.is_current is True

    def test_achievements_list(self) -> None:
        """Test experience with achievements."""
        exp = Experience(
            company="Tech Corp",
            title="Engineer",
            achievements=["Led team of 5", "Increased performance by 50%"],
        )
        assert len(exp.achievements) == 2


class TestEducation:
    """Test cases for Education model."""

    def test_valid_education(self) -> None:
        """Test creating valid education."""
        edu = Education(
            institution="MIT",
            degree="B.S. Computer Science",
            gpa=3.8,
        )
        assert edu.institution == "MIT"
        assert edu.gpa == 3.8

    def test_invalid_gpa(self) -> None:
        """Test education with invalid GPA."""
        with pytest.raises(ValidationError):
            Education(institution="MIT", degree="BS", gpa=5.0)


class TestResume:
    """Test cases for Resume model."""

    def test_valid_resume(self) -> None:
        """Test creating valid resume."""
        resume = Resume(
            id="test-id",
            file_name="resume.pdf",
            file_type=FileType.PDF,
            file_size_bytes=1024,
            content="Resume text content",
        )
        assert resume.id == "test-id"
        assert resume.file_type == FileType.PDF


class TestParsedResume:
    """Test cases for ParsedResume model."""

    def test_valid_parsed_resume(self) -> None:
        """Test creating valid parsed resume."""
        parsed = ParsedResume(
            id="parsed-1",
            resume_id="resume-1",
            contact={"full_name": "John Doe"},
            skills=[{"name": "Python"}],
            experience=[],
            education=[],
        )
        assert parsed.id == "parsed-1"
        assert parsed.status == ParsingStatus.COMPLETED

    def test_default_status(self) -> None:
        """Test default parsing status."""
        parsed = ParsedResume(
            id="parsed-1",
            resume_id="resume-1",
            contact={"full_name": "John Doe"},
        )
        assert parsed.status == ParsingStatus.COMPLETED


class TestAgentResult:
    """Test cases for AgentResult model."""

    def test_success_result(self) -> None:
        """Test successful agent result."""
        result = AgentResult(
            agent_name="TestAgent",
            success=True,
            data={"key": "value"},
            execution_time_seconds=1.5,
        )
        assert result.success is True
        assert result.execution_time_seconds == 1.5

    def test_failure_result(self) -> None:
        """Test failed agent result."""
        result = AgentResult(
            agent_name="TestAgent",
            success=False,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"


class TestParseRequest:
    """Test cases for ParseRequest model."""

    def test_text_request(self) -> None:
        """Test parse request with text."""
        req = ParseRequest(text="Resume content")
        assert req.text == "Resume content"

    def test_empty_request(self) -> None:
        """Test empty parse request."""
        req = ParseRequest()
        assert req.text is None


class TestParseResponse:
    """Test cases for ParseResponse model."""

    def test_success_response(self) -> None:
        """Test successful parse response."""
        resp = ParseResponse(
            success=True,
            resume_id="test-id",
            total_execution_time_seconds=2.0,
        )
        assert resp.success is True


class TestHealthResponse:
    """Test cases for HealthResponse model."""

    def test_health_response(self) -> None:
        """Test health response."""
        resp = HealthResponse(status="healthy", version="0.1.0")
        assert resp.status == "healthy"


class TestStatsResponse:
    """Test cases for StatsResponse model."""

    def test_stats_response(self) -> None:
        """Test stats response."""
        resp = StatsResponse(
            total_resumes_parsed=10,
            success_rate=0.95,
        )
        assert resp.total_resumes_parsed == 10
        assert resp.success_rate == 0.95
