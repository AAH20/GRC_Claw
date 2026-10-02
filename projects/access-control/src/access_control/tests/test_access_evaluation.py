"""Tests for access evaluation workflows."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from access_control.agents.permission_evaluator import (
    PermissionEvaluatorAgent,
)
from access_control.agents.policy_enforcer import PolicyEnforcerAgent
from access_control.config import Settings
from access_control.models.enums import AccessDecision
from access_control.models.schemas import AccessRequest, Permission, Policy


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM."""
    return MagicMock()


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(app_env="development", secret_key="test", openai_api_key="test")


class TestAccessEvaluation:
    """Test suite for access evaluation workflows."""

    @pytest.mark.asyncio
    async def test_evaluate_allow_decision(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test evaluating an access request that should be allowed."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "allow", "reason": "User has permission", "confidence": 0.95}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="documents",
            action="read",
            roles=["editor"],
        )
        result = await agent.evaluate(request)

        assert result.decision == AccessDecision.ALLOW
        assert result.confidence == 0.95
        assert result.request.principal_id == "user-1"

    @pytest.mark.asyncio
    async def test_evaluate_deny_decision(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test evaluating an access request that should be denied."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "deny", "reason": "Insufficient permissions", "confidence": 0.9}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="admin-panel",
            action="delete",
        )
        result = await agent.evaluate(request)

        assert result.decision == AccessDecision.DENY

    @pytest.mark.asyncio
    async def test_evaluate_with_policies(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test evaluating with policy context."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "allow", "reason": "Policy allows", "confidence": 0.85, "policy_ids": ["policy-1"]}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="documents",
            action="read",
        )
        policies = [
            {
                "id": "policy-1",
                "name": "Allow read",
                "rules": [{"resource": "documents", "action": "read", "effect": "allow"}],
            }
        ]
        result = await agent.evaluate(request, policies=policies)

        assert result.decision == AccessDecision.ALLOW
        assert "policy-1" in result.policy_ids

    @pytest.mark.asyncio
    async def test_enforce_policies(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test policy enforcement."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "allow", "enforced_policies": ["policy-1"], "violations": []}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PolicyEnforcerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="documents",
            action="read",
        )
        policies = [
            Policy(
                name="Test Policy",
                rules=[Permission(resource="documents", action="read")],
            )
        ]
        result = await agent.enforce(request, policies)

        assert result.decision == AccessDecision.ALLOW
        assert len(result.policy_ids) > 0

    @pytest.mark.asyncio
    async def test_enforce_with_violations(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test policy enforcement with violations."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "deny", "violations": ["Unauthorized access attempt"]}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PolicyEnforcerAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="admin",
            action="delete",
        )
        result = await agent.enforce(request)

        assert result.decision == AccessDecision.DENY

    @pytest.mark.asyncio
    async def test_conditional_access(
        self, mock_llm: MagicMock, settings: Settings
    ) -> None:
        """Test conditional access decision."""
        mock_response = MagicMock()
        mock_response.content = '{"decision": "conditional", "reason": "MFA required", "obligations": ["mfa"], "confidence": 0.8}'  # noqa: E501
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        agent = PermissionEvaluatorAgent(llm=mock_llm, settings=settings)
        agent._build_agent = MagicMock(return_value=mock_chain)

        request = AccessRequest(
            principal_id="user-1",
            resource="sensitive-data",
            action="read",
        )
        result = await agent.evaluate(request)

        assert result.decision == AccessDecision.CONDITIONAL
        assert "mfa" in result.obligations
