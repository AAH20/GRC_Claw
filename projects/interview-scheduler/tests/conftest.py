"""Test configuration."""

import asyncio
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests.

    Returns:
        Event loop instance.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
