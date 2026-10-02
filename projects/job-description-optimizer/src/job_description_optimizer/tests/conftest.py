"""Pytest configuration and fixtures."""

from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

from job_description_optimizer.config import Settings
from job_description_optimizer.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Create test settings.

    Returns:
        Settings instance with test configuration.
    """
    return Settings(
        app_name="test-jdo",
        app_env="testing",
        debug=True,
        openai_api_key="sk-test-key",
        openai_model="gpt-4o-mini",
        llm_temperature=0.0,
        llm_max_tokens=1024,
        max_agent_iterations=5,
        agent_timeout_seconds=30,
    )


@pytest.fixture
def app(settings: Settings):
    """Create test FastAPI application.

    Args:
        settings: Test settings.

    Returns:
        FastAPI application instance.
    """
    return create_app(settings=settings)


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create test client.

    Args:
        app: FastAPI application instance.

    Yields:
        TestClient instance.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_job_description() -> dict:
    """Create a sample job description for testing.

    Returns:
        Dictionary with sample job description data.
    """
    return {
        "title": "Senior Software Engineer",
        "description": "We are looking for a rockstar developer to join our team. "
        "The ideal candidate should be a young, energetic digital native who can "
        "hit the ground running. He will be responsible for developing web applications "
        "using Python and JavaScript. We require 5+ years of experience and a degree "
        "from a top-tier university. Must be able to work long hours and handle "
        "high-pressure situations.",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "department": "Engineering",
        "employment_type": "full-time",
        "experience_level": "senior",
        "skills": ["Python", "JavaScript", "React", "AWS"],
        "responsibilities": [
            "Develop web applications",
            "Write clean code",
            "Mentor junior developers",
        ],
        "qualifications": [
            "5+ years of experience",
            "Bachelor's degree in Computer Science",
        ],
        "salary_range": "$150,000 - $200,000",
        "benefits": ["Health insurance", "401k", "Unlimited PTO"],
        "industry": "Technology",
        "remote_policy": "Hybrid",
    }
