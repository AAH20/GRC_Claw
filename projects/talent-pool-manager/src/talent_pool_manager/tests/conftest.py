"""Test configuration and fixtures."""

from __future__ import annotations

from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from talent_pool_manager.main import create_app


@pytest.fixture
def app():
    """Create a test application instance."""
    return create_app()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pool_data() -> dict:
    """Sample talent pool data for testing."""
    return {
        "name": "Engineering Talent Pool",
        "description": "Top engineering candidates for Q4 hiring",
        "visibility": "private",
        "tags": ["engineering", "senior", "backend"],
        "criteria": {"skills": ["Python", "Go"], "experience_years": 5},
        "auto_refresh": True,
        "refresh_interval_hours": 24,
        "organization_id": str(uuid4()),
    }


@pytest.fixture
def sample_candidate_data() -> dict:
    """Sample candidate data for testing."""
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "headline": "Senior Software Engineer",
        "summary": "Experienced backend engineer with 8 years in distributed systems.",
        "skills": [
            {"name": "Python", "proficiency": "expert", "years_experience": 8},
            {"name": "Go", "proficiency": "advanced", "years_experience": 4},
        ],
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "start_date": "2020-01-01T00:00:00",
                "is_current": True,
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "B.S. Computer Science",
                "graduation_year": 2015,
            }
        ],
        "source": "linkedin",
        "tags": ["backend", "distributed-systems"],
        "pool_id": str(uuid4()),
    }


@pytest.fixture
def sample_segment_data() -> dict:
    """Sample segment data for testing."""
    return {
        "name": "Senior Backend Engineers",
        "description": "Candidates with 5+ years in backend development",
        "segment_type": "experience_based",
        "criteria": {"min_experience": 5, "skills": ["Python", "Go"]},
        "is_dynamic": True,
        "pool_id": str(uuid4()),
    }


@pytest.fixture
def sample_engagement_data() -> dict:
    """Sample engagement data for testing."""
    return {
        "engagement_type": "email",
        "subject": "Exciting opportunity at TechCorp",
        "content": "Hi Jane, we have an exciting opportunity...",
        "channel": "email",
        "candidate_id": str(uuid4()),
    }


@pytest.fixture
def sample_outreach_template_data() -> dict:
    """Sample outreach template data for testing."""
    return {
        "name": "Initial Outreach - Senior Engineer",
        "subject_template": "Opportunity at {{company_name}} - {{role_title}}",
        "body_template": "Hi {{first_name}},\n\nI came across your profile...",
        "channel": "email",
        "tone": "professional",
        "variables": ["company_name", "role_title", "first_name"],
    }


@pytest.fixture
def sample_outreach_campaign_data() -> dict:
    """Sample outreach campaign data for testing."""
    return {
        "name": "Q4 Senior Engineer Outreach",
        "description": "Outreach campaign for senior engineering candidates",
        "template_id": str(uuid4()),
        "pool_id": str(uuid4()),
    }
