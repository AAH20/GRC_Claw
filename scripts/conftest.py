"""
GRC_Claw Unified Test Framework — Shared Fixtures

This conftest.py provides shared fixtures for all test suites across the
GRC_Claw monorepo. Place it at the root of any test directory or use it
as a reference for sub-project conftest.py files.

Usage:
    pytest --confcutdir=scripts scripts/
    # or from any sub-project:
    pytest --confcutdir=../../scripts tests/
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def specs_dir(repo_root: Path) -> Path:
    """Return the specs directory path."""
    path = repo_root / "specs"
    if not path.exists():
        pytest.skip(f"Specs directory not found: {path}")
    return path


@pytest.fixture(scope="session")
def scripts_dir(repo_root: Path) -> Path:
    """Return the scripts directory path."""
    return repo_root / "scripts"


@pytest.fixture(scope="session")
def packages_dir(repo_root: Path) -> Path:
    """Return the packages directory path."""
    return repo_root / "packages"


@pytest.fixture(scope="session")
def deployment_dir(repo_root: Path) -> Path:
    """Return the deployment directory path."""
    return repo_root / "deployment"


@pytest.fixture(scope="session")
def docs_dir(repo_root: Path) -> Path:
    """Return the docs directory path."""
    return repo_root / "docs"


# ---------------------------------------------------------------------------
# Async / Event Loop Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[Any, None]:
    """Create an async HTTP test client (httpx-based).

    Override in sub-project conftest.py to provide a real app client.
    """
    httpx = pytest.importorskip("httpx")
    transport = httpx.ASGITransport(app=MagicMock())
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Mock Data Fixtures
# ---------------------------------------------------------------------------


@dataclass
class MockPolicy:
    """Mock policy object for testing."""

    id: str = "pol-test-001"
    name: str = "Test Policy"
    version: str = "1.0.0"
    status: str = "draft"
    tenant_id: str = "tenant-test"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    rules: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MockEvidence:
    """Mock evidence object for testing."""

    id: str = "ev-test-001"
    control_id: str = "AC-2"
    framework: str = "NIST-800-53"
    evidence_type: str = "artifact"
    collected_by: str = "agent-test-001"
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    content: dict[str, Any] = field(default_factory=dict)
    hash_value: str = "a" * 64


@dataclass
class MockEnforcement:
    """Mock enforcement decision for testing."""

    id: str = "enf-test-001"
    policy_id: str = "pol-test-001"
    principal: str = "agent-test-001"
    action: str = "allow"
    reason: str = "policy permits"
    request_id: str = "req-test-001"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class MockAssessment:
    """Mock assessment object for testing."""

    id: str = "asm-test-001"
    name: str = "Test Assessment"
    framework: str = "ISO-42001"
    status: str = "in_progress"
    score: float = 0.0
    tenant_id: str = "tenant-test"


@pytest.fixture
def mock_policy() -> MockPolicy:
    """Return a mock policy object."""
    return MockPolicy()


@pytest.fixture
def mock_evidence() -> MockEvidence:
    """Return a mock evidence object."""
    return MockEvidence()


@pytest.fixture
def mock_enforcement() -> MockEnforcement:
    """Return a mock enforcement decision."""
    return MockEnforcement()


@pytest.fixture
def mock_assessment() -> MockAssessment:
    """Return a mock assessment object."""
    return MockAssessment()


@pytest.fixture
def mock_tenant_context() -> dict[str, str]:
    """Return a mock tenant context for multi-tenant tests."""
    return {
        "tenant_id": "tenant-test-001",
        "tenant_name": "Test Tenant",
        "tenant_tier": "enterprise",
    }


# ---------------------------------------------------------------------------
# Spec Validation Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def spec_files(specs_dir: Path) -> list[Path]:
    """Return all markdown spec files in the specs directory."""
    return sorted(specs_dir.glob("*.md"))


@pytest.fixture(scope="session")
def spec_file_contents(spec_files: list[Path]) -> dict[str, str]:
    """Return a mapping of spec filename to its content."""
    contents: dict[str, str] = {}
    for f in spec_files:
        try:
            contents[f.name] = f.read_text(encoding="utf-8")
        except Exception:
            contents[f.name] = ""
    return contents


@pytest.fixture
def required_spec_sections() -> list[str]:
    """Return the list of required sections for spec validation."""
    return [
        "Purpose",
        "Scope",
        "References",
        "Architecture",
        "Data Model",
        "API",
        "Security",
        "Metrics",
    ]


# ---------------------------------------------------------------------------
# Configuration Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_config() -> dict[str, Any]:
    """Return test configuration loaded from environment or defaults."""
    return {
        "base_url": os.environ.get("GRC_CLAW_BASE_URL", "http://127.0.0.1:18791"),
        "gateway_token": os.environ.get("GRC_CLAW_GATEWAY_TOKEN", "grc-test-token"),
        "test_timeout": int(os.environ.get("GRC_CLAW_TEST_TIMEOUT", "30")),
        "skip_integration": os.environ.get("GRC_CLAW_SKIP_INTEGRATION", "false").lower()
        == "true",
        "skip_slow": os.environ.get("GRC_CLAW_SKIP_SLOW", "false").lower() == "true",
    }


@pytest.fixture
def gateway_url(test_config: dict[str, Any]) -> str:
    """Return the gateway URL for integration tests."""
    return test_config["base_url"]


@pytest.fixture
def gateway_token(test_config: dict[str, Any]) -> str:
    """Return the gateway token for integration tests."""
    return test_config["gateway_token"]


# ---------------------------------------------------------------------------
# Utility Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_spec_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary spec file for testing."""
    spec_file = tmp_path / "test-spec.md"
    spec_file.write_text(
        "# Test Spec\n\n"
        "## Purpose & Scope\n\n"
        "This is a test specification.\n\n"
        "## References\n\n"
        "None.\n",
        encoding="utf-8",
    )
    yield spec_file
    spec_file.unlink(missing_ok=True)


@pytest.fixture
def json_serializable() -> Any:
    """Return a JSON-serializable test object."""
    return {
        "id": "test-001",
        "name": "Test Object",
        "version": "1.0.0",
        "tags": ["test", "fixture"],
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "owner": "test-suite",
        },
    }


# ---------------------------------------------------------------------------
# Pytest Hooks
# ---------------------------------------------------------------------------


def pytest_configure(config: Any) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires running services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers", "spec_validation: mark test as spec validation test"
    )
    config.addinivalue_line(
        "markers", "quality_gate: mark test as quality gate test"
    )


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Skip integration tests if GRC_CLAW_SKIP_INTEGRATION is set."""
    if os.environ.get("GRC_CLAW_SKIP_INTEGRATION", "false").lower() == "true":
        skip_integration = pytest.mark.skip(
            reason="Integration tests disabled via GRC_CLAW_SKIP_INTEGRATION"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    if os.environ.get("GRC_CLAW_SKIP_SLOW", "false").lower() == "true":
        skip_slow = pytest.mark.skip(
            reason="Slow tests disabled via GRC_CLAW_SKIP_SLOW"
        )
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
