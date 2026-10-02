"""Unit tests for custom exceptions."""

from __future__ import annotations

import pytest

from core.exceptions import (
    AgentError,
    AgentMaxIterationsError,
    AgentTimeoutError,
    CampaignNotFoundError,
    CampaignOptimizerError,
    CampaignValidationError,
    ConfigurationError,
    DatabaseError,
    GovernanceApprovalRequired,
    GovernanceError,
    LLMError,
    LLMQuotaError,
    LLMTimeoutError,
)


class TestCampaignOptimizerError:
    """Tests for the base exception class."""

    def test_basic_exception(self) -> None:
        """Test basic exception creation."""
        exc = CampaignOptimizerError("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.details == {}
        assert str(exc) == "Something went wrong"

    def test_exception_with_details(self) -> None:
        """Test exception with additional details."""
        details = {"campaign_id": "camp_123", "field": "budget"}
        exc = CampaignOptimizerError("Validation failed", details=details)
        assert exc.details == details

    def test_exception_inheritance(self) -> None:
        """Test that all custom exceptions inherit from the base."""
        exceptions = [
            AgentError("test"),
            AgentTimeoutError("test"),
            AgentMaxIterationsError("test"),
            CampaignNotFoundError("test"),
            CampaignValidationError("test"),
            ConfigurationError("test"),
            DatabaseError("test"),
            GovernanceError("test"),
            GovernanceApprovalRequired("test"),
            LLMError("test"),
            LLMTimeoutError("test"),
            LLMQuotaError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, CampaignOptimizerError)
