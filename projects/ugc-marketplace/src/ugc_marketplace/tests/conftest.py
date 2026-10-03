"""Test configuration and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing.

    Returns:
        Sample text string.
    """
    return "This is sample content for testing purposes."


@pytest.fixture
def sample_creator_id() -> str:
    """Sample creator ID for testing.

    Returns:
        Sample creator ID.
    """
    return "creator_123"


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for testing.

    Returns:
        Sample user ID.
    """
    return "user_456"
