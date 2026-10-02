"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from quality_scoring.main import create_app


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return """
# The Future of Artificial Intelligence

Artificial intelligence is transforming every industry at an unprecedented pace. From healthcare to finance, AI is revolutionizing how we work and live.

## What is AI?

AI refers to computer systems that can perform tasks typically requiring human intelligence. These tasks include learning, reasoning, and self-correction.

## Why Does AI Matter?

AI matters because it can process vast amounts of data faster than any human. This capability enables breakthroughs in medicine, science, and technology.

Consider these key benefits:
- Faster decision making
- Improved accuracy
- Cost reduction
- Enhanced creativity

## How to Get Started

Getting started with AI is easier than you might think. Here are some steps:

1. Learn the basics of machine learning
2. Explore AI tools and platforms
3. Start with small projects
4. Join AI communities

The future of AI is bright. Are you ready to be part of it?

**Start your AI journey today!**
"""


@pytest.fixture
def sample_content_input(sample_content):
    """Sample ContentInput for testing."""
    from quality_scoring.models.schemas import ContentInput, ContentType

    return ContentInput(
        content=sample_content,
        content_type=ContentType.ARTICLE,
        title="The Future of AI",
    )
