"""Test configuration and fixtures."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from community_governance.api.dependencies import set_agents, set_metrics
from community_governance.integrations import MetricsIntegration
from community_governance.main import create_app


@pytest.fixture
def app():
    """Create a test application instance."""
    return create_app()


@pytest.fixture(autouse=True)
async def setup_agents(app):
    """Initialize agents and metrics for testing.

    ASGITransport does not trigger lifespan events, so we must
    manually initialize agents and metrics here.
    """
    from community_governance.main import create_agents

    agents = create_agents()
    for agent in agents.values():
        await agent.initialize()
    set_agents(agents)

    metrics_integration = MetricsIntegration(enabled=False)
    set_metrics(metrics_integration)

    yield

    # Cleanup
    set_agents({})
    set_metrics(None)


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_rule_data():
    """Sample rule creation data."""
    return {
        "name": "No Spam",
        "description": "Users must not post spam content",
        "category": "content_moderation",
        "severity": "medium",
        "conditions": {"action_types": ["create", "update"]},
        "actions": ["flag", "notify_moderator"],
        "priority": 50,
    }


@pytest.fixture
def sample_dispute_data():
    """Sample dispute creation data."""
    return {
        "title": "Content Removal Dispute",
        "description": "User disputes the removal of their post",
        "priority": "medium",
        "category": "content_moderation",
        "initiator_id": "user_123",
        "respondent_id": "moderator_456",
    }


@pytest.fixture
def sample_policy_data():
    """Sample policy creation data."""
    return {
        "name": "Community Content Policy",
        "description": "Guidelines for acceptable content in the community",
        "scope": "global",
        "guidelines": [
            "Be respectful to other members",
            "No hate speech or harassment",
            "Keep discussions on-topic",
        ],
        "enforcement_level": "standard",
    }
