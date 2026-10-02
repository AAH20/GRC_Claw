"""Test configuration and fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from resume_parser.config import Settings
from resume_parser.integrations import BaseLLMClient
from resume_parser.integrations.storage import InMemoryStorage
from resume_parser.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing."""

    def __init__(self) -> None:
        """Initialize mock client."""
        self._responses: list[str] = []
        self._call_count = 0

    def add_response(self, response: str) -> None:
        """Add a mock response.

        Args:
            response: Response to return.
        """
        self._responses.append(response)

    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate a mock response.

        Args:
            prompt: Input prompt.
            **kwargs: Additional parameters.

        Returns:
            str: Mock response.
        """
        if self._call_count < len(self._responses):
            response = self._responses[self._call_count]
            self._call_count += 1
            return response
        return "{}"

    async def agenerate(self, prompt: str, **kwargs: object) -> str:
        """Asynchronously generate a mock response.

        Args:
            prompt: Input prompt.
            **kwargs: Additional parameters.

        Returns:
            str: Mock response.
        """
        return self.generate(prompt, **kwargs)


@pytest.fixture
def settings() -> Settings:
    """Create test settings.

    Returns:
        Settings: Test settings.
    """
    return Settings(
        app_name="resume-parser-test",
        app_env="testing",
        debug=True,
        log_level="DEBUG",
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        storage_backend="memory",
        upload_dir=Path("/tmp/resume-parser-test-uploads"),
        storage_path=Path("/tmp/resume-parser-test-data"),
    )


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Create mock LLM client.

    Returns:
        MockLLMClient: Mock LLM client.
    """
    return MockLLMClient()


@pytest.fixture
def mock_llm(mock_llm_client: MockLLMClient) -> MockLLMClient:
    """Alias for mock_llm_client fixture.

    Args:
        mock_llm_client: The mock LLM client fixture.

    Returns:
        MockLLMClient: Mock LLM client.
    """
    return mock_llm_client


@pytest.fixture
def storage() -> InMemoryStorage:
    """Create in-memory storage.

    Returns:
        InMemoryStorage: In-memory storage.
    """
    return InMemoryStorage()


@pytest_asyncio.fixture
async def app(
    settings: Settings,
    mock_llm_client: MockLLMClient,
    storage: InMemoryStorage,
) -> AsyncGenerator[FastAPI, None]:
    """Create test FastAPI app.

    Args:
        settings: Test settings.
        mock_llm_client: Mock LLM client.
        storage: In-memory storage.

    Yields:
        FastAPI: Test application.
    """
    app = create_app(settings)
    app.state.llm_client = mock_llm_client
    app.state.storage = storage
    yield app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client.

    Args:
        app: Test application.

    Yields:
        AsyncClient: Test HTTP client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
