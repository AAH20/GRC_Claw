"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from tier_management.exceptions import (
    AccessDeniedError,
    AgentExecutionError,
    BenefitNotFoundError,
    EvaluationError,
    MemberNotFoundError,
    PolicyNotFoundError,
    TierManagementError,
    TierNotFoundError,
    UpgradeNotEligibleError,
)


def test_tier_management_error() -> None:
    """Test base TierManagementError."""
    error = TierManagementError("Test error", status_code=400, details={"key": "value"})
    assert error.message == "Test error"
    assert error.status_code == 400
    assert error.details == {"key": "value"}
    assert str(error) == "Test error"


def test_tier_not_found_error() -> None:
    """Test TierNotFoundError."""
    error = TierNotFoundError("tier-123")
    assert error.status_code == 404
    assert "tier-123" in error.message
    assert error.details["tier_id"] == "tier-123"


def test_member_not_found_error() -> None:
    """Test MemberNotFoundError."""
    error = MemberNotFoundError("member-456")
    assert error.status_code == 404
    assert "member-456" in error.message


def test_evaluation_error() -> None:
    """Test EvaluationError."""
    error = EvaluationError("Evaluation failed", details={"member_id": "123"})
    assert error.status_code == 422
    assert error.message == "Evaluation failed"


def test_access_denied_error() -> None:
    """Test AccessDeniedError."""
    error = AccessDeniedError("member-1", "premium_forum", "Insufficient tier")
    assert error.status_code == 403
    assert "member-1" in error.message
    assert "premium_forum" in error.message


def test_upgrade_not_eligible_error() -> None:
    """Test UpgradeNotEligibleError."""
    error = UpgradeNotEligibleError("member-1", "tier-2", "Score too low")
    assert error.status_code == 400
    assert "Score too low" in error.message


def test_benefit_not_found_error() -> None:
    """Test BenefitNotFoundError."""
    error = BenefitNotFoundError("benefit-789")
    assert error.status_code == 404
    assert "benefit-789" in error.message


def test_policy_not_found_error() -> None:
    """Test PolicyNotFoundError."""
    error = PolicyNotFoundError("policy-101")
    assert error.status_code == 404
    assert "policy-101" in error.message


def test_agent_execution_error() -> None:
    """Test AgentExecutionError."""
    error = AgentExecutionError("TierEvaluatorAgent", "LLM timeout")
    assert error.status_code == 500
    assert "TierEvaluatorAgent" in error.message
    assert "LLM timeout" in error.message
    assert error.details["agent_name"] == "TierEvaluatorAgent"


def test_exception_inheritance() -> None:
    """Test all exceptions inherit from TierManagementError."""
    exceptions = [
        TierNotFoundError("test"),
        MemberNotFoundError("test"),
        EvaluationError("test"),
        AccessDeniedError("test", "resource"),
        UpgradeNotEligibleError("test", "tier", "reason"),
        BenefitNotFoundError("test"),
        PolicyNotFoundError("test"),
        AgentExecutionError("agent", "error"),
    ]
    for exc in exceptions:
        assert isinstance(exc, TierManagementError)
