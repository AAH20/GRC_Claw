"""Tests for access control agents."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from access_control.agents import (
    AccessAuditorAgent,
    AccessRecommenderAgent,
    PermissionEvaluatorAgent,
    PolicyEnforcerAgent,
    RoleManagerAgent,
)
from access_control.agents.base import AgentContext
from access_control.config import Settings
from access_control.models.enums import AccessDecision, AuditSeverity
from access_control.models.schemas import (
    AccessRequest,
)


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM."""
    llm = MagicMock()
    return llm


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        app_env="development",
        secret_key="test-secret",
        openai_api_key="test-key",
    )


@pytest.fixture
def agent_context(settings: Settings) -> AgentContext:
    """Create an agent context."""
    return AgentContext(settings=settings)


class TestAgents:
    """Test suite for access control agents."""

    @pytest.mark.asyncio
    async def test_permission_evaluator_agent_init(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test permission evaluator agent initialization."""
        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        assert agent.name == "permission_evaluator"
        assert agent.llm is mock_llm

    @pytest.mark.asyncio
    async def test_permission_evaluator_agent_build(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test permission evaluator agent builds chain."""
        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        chain = agent._build_agent()
        assert chain is not None

    @pytest.mark.asyncio
    async def test_role_manager_agent_init(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test role manager agent initialization."""
        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        assert agent.name == "role_manager"

    @pytest.mark.asyncio
    async def test_access_auditor_agent_init(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test access auditor agent initialization."""
        agent = AccessAuditorAgent(llm=mock_llm, settings=settings)
        assert agent.name == "access_auditor"

    @pytest.mark.asyncio
    async def test_policy_enforcer_agent_init(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test policy enforcer agent initialization."""
        agent = PolicyEnforcerAgent(llm=mock_llm, settings=settings)
        assert agent.name == "policy_enforcer"

    @pytest.mark.asyncio
    async def test_access_recommender_agent_init(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test access recommender agent initialization."""
        agent = AccessRecommenderAgent(llm=mock_llm, settings=settings)
        assert agent.name == "access_recommender"

    @pytest.mark.asyncio
    async def test_permission_evaluator_run(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test permission evaluator agent run method."""
        # Mock the chain response
        mock_response = MagicMock()
        mock_response.content = '{"decision": "allow", "reason": "Test allow", "confidence": 0.9}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.permission_evaluator import PermissionEvaluatorInput

        payload = PermissionEvaluatorInput(
            request=AccessRequest(principal_id="user-1", resource="docs", action="read")
        )
        result = await agent.run(payload, agent_context)

        assert result.decision == AccessDecision.ALLOW
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_access_auditor_run(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test access auditor agent run method."""
        mock_response = MagicMock()
        mock_response.content = '{"severity": "info", "flagged": false, "anomaly_score": 0.1}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = AccessAuditorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.access_auditor import AccessAuditorInput

        payload = AccessAuditorInput(
            event_type="access_attempt",
            audit_entry={"principal_id": "user-1"},
        )
        result = await agent.run(payload, agent_context)

        assert result.severity == AuditSeverity.INFO
        assert result.flagged is False

    @pytest.mark.asyncio
    async def test_role_manager_run(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test role manager agent run method."""
        mock_response = MagicMock()
        mock_response.content = '{"success": true, "role": {"name": "test"}, "message": "Created"}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = RoleManagerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.role_manager import RoleManagerInput

        payload = RoleManagerInput(
            operation="create",
            role_data={"name": "test-role"},
        )
        result = await agent.run(payload, agent_context)

        assert result.success is True
        assert result.role is not None

    @pytest.mark.asyncio
    async def test_policy_enforcer_run(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test policy enforcer agent run method."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "deny", "violations": ["Test violation"]}'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PolicyEnforcerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.policy_enforcer import PolicyEnforcerInput

        payload = PolicyEnforcerInput(
            request=AccessRequest(principal_id="user-1", resource="docs", action="read")
        )
        result = await agent.run(payload, agent_context)

        assert result.decision == AccessDecision.DENY

    @pytest.mark.asyncio
    async def test_access_recommender_run(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test access recommender agent run method."""
        mock_response = MagicMock()
        mock_response.content = '{"recommendations": [{"resource": "docs", "action": "read", "recommendation": "grant"}], "summary": "Test"}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = AccessRecommenderAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.access_recommender import AccessRecommenderInput

        payload = AccessRecommenderInput(principal_id="user-1")
        result = await agent.run(payload, agent_context)

        assert len(result.recommendations) == 1
        assert result.recommendations[0]["recommendation"] == "grant"

    @pytest.mark.asyncio
    async def test_agent_error_handling(
        self, mock_llm: MagicMock, settings: Settings, agent_context: AgentContext
    ) -> None:
        """Test agent error handling with invalid response."""
        mock_response = MagicMock()
        mock_response.content = "invalid json"
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        from access_control.agents.permission_evaluator import PermissionEvaluatorInput

        payload = PermissionEvaluatorInput(
            request=AccessRequest(principal_id="user-1", resource="docs", action="read")
        )
        result = await agent.run(payload, agent_context)

        # Should return abstain on parse failure
        assert result.decision == AccessDecision.ABSTAIN
