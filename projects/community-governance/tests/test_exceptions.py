"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from community_governance.exceptions import (
    AgentExecutionException,
    DisputeNotFoundException,
    DisputeResolutionException,
    GovernanceException,
    PolicyEnforcementException,
    PolicyNotFoundException,
    RuleNotFoundException,
    RuleValidationException,
)


def test_governance_exception() -> None:
    """Test base governance exception."""
    exc = GovernanceException("Test error", {"key": "value"})
    assert exc.message == "Test error"
    assert exc.details == {"key": "value"}
    assert str(exc) == "Test error"


def test_rule_not_found_exception() -> None:
    """Test rule not found exception."""
    exc = RuleNotFoundException("rule_123")
    assert exc.rule_id == "rule_123"
    assert "rule_123" in exc.message


def test_dispute_not_found_exception() -> None:
    """Test dispute not found exception."""
    exc = DisputeNotFoundException("dispute_123")
    assert exc.dispute_id == "dispute_123"
    assert "dispute_123" in exc.message


def test_policy_not_found_exception() -> None:
    """Test policy not found exception."""
    exc = PolicyNotFoundException("policy_123")
    assert exc.policy_id == "policy_123"
    assert "policy_123" in exc.message


def test_rule_validation_exception() -> None:
    """Test rule validation exception."""
    exc = RuleValidationException("Validation failed", {"name": "Name is required"})
    assert exc.field_errors == {"name": "Name is required"}


def test_dispute_resolution_exception() -> None:
    """Test dispute resolution exception."""
    exc = DisputeResolutionException("dispute_123", "Insufficient information")
    assert exc.dispute_id == "dispute_123"
    assert exc.reason == "Insufficient information"


def test_policy_enforcement_exception() -> None:
    """Test policy enforcement exception."""
    exc = PolicyEnforcementException("policy_123", "action_456", "Rule conflict")
    assert exc.policy_id == "policy_123"
    assert exc.action_id == "action_456"
    assert exc.reason == "Rule conflict"


def test_agent_execution_exception() -> None:
    """Test agent execution exception."""
    exc = AgentExecutionException("rule_enforcer", "LLM timeout")
    assert exc.agent_name == "rule_enforcer"
    assert exc.reason == "LLM timeout"


def test_exception_inheritance() -> None:
    """Test that all exceptions inherit from GovernanceException."""
    exceptions = [
        RuleNotFoundException("test"),
        DisputeNotFoundException("test"),
        PolicyNotFoundException("test"),
        RuleValidationException("test"),
        DisputeResolutionException("test", "test"),
        PolicyEnforcementException("test", "test", "test"),
        AgentExecutionException("test", "test"),
    ]
    for exc in exceptions:
        assert isinstance(exc, GovernanceException)
