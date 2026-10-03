"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing.

    Returns:
        Sample resume text.
    """
    return """
    John Doe
    john.doe@email.com
    (555) 123-4567
    linkedin.com/in/johndoe

    Education:
    Bachelor of Science in Computer Science
    Stanford University, 2018

    Experience:
    Senior Software Engineer at Google
    Jan 2020 - Present
    Led development of cloud infrastructure.

    Skills: Python, Java, AWS, Kubernetes, Machine Learning
    """


@pytest.fixture
def sample_candidate() -> dict:
    """Sample candidate data for testing.

    Returns:
        Sample candidate dictionary.
    """
    return {
        "id": "cand-001",
        "name": "Jane Smith",
        "skills": ["Python", "AWS", "Docker"],
        "experience_years": 5,
        "match_score": 0.85,
    }


@pytest.fixture
def sample_job_requirements() -> dict:
    """Sample job requirements for testing.

    Returns:
        Sample job requirements dictionary.
    """
    return {
        "title": "Senior Software Engineer",
        "required_skills": ["Python", "AWS", "Kubernetes"],
        "min_experience_years": 3,
    }
