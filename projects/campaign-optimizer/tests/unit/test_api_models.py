"""Unit tests for API models and schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.models.schemas import (
    CampaignCreateRequest,
    CampaignGoal,
    CampaignStatus,
    CampaignUpdateRequest,
    Channel,
    HealthResponse,
    OptimizationRequest,
)


class TestCampaignCreateRequest:
    """Tests for campaign creation request model."""

    def test_valid_request(self) -> None:
        """Test creating a valid request."""
        data = {
            "name": "Test Campaign",
            "goals": ["awareness"],
            "total_budget": 10000.0,
            "daily_budget": 333.33,
            "channels": ["search"],
            "duration_days": 30,
        }
        request = CampaignCreateRequest(**data)
        assert request.name == "Test Campaign"
        assert request.goals == [CampaignGoal.AWARENESS]
        assert request.total_budget == 10000.0

    def test_invalid_budget(self) -> None:
        """Test that negative budget is rejected."""
        with pytest.raises(ValidationError):
            CampaignCreateRequest(
                name="Test",
                goals=["awareness"],
                total_budget=-100,
                daily_budget=10,
                channels=["search"],
                duration_days=30,
            )

    def test_invalid_duration(self) -> None:
        """Test that invalid duration is rejected."""
        with pytest.raises(ValidationError):
            CampaignCreateRequest(
                name="Test",
                goals=["awareness"],
                total_budget=1000,
                daily_budget=100,
                channels=["search"],
                duration_days=0,
            )

    def test_empty_goals(self) -> None:
        """Test that empty goals list is rejected."""
        with pytest.raises(ValidationError):
            CampaignCreateRequest(
                name="Test",
                goals=[],
                total_budget=1000,
                daily_budget=100,
                channels=["search"],
                duration_days=30,
            )


class TestCampaignUpdateRequest:
    """Tests for campaign update request model."""

    def test_partial_update(self) -> None:
        """Test that partial updates are allowed."""
        request = CampaignUpdateRequest(name="New Name")
        assert request.name == "New Name"
        assert request.total_budget is None

    def test_empty_update(self) -> None:
        """Test that empty update is valid."""
        request = CampaignUpdateRequest()
        assert request.name is None


class TestEnums:
    """Tests for enum values."""

    def test_campaign_status_values(self) -> None:
        """Test campaign status enum values."""
        assert CampaignStatus.DRAFT.value == "draft"
        assert CampaignStatus.ACTIVE.value == "active"
        assert CampaignStatus.COMPLETED.value == "completed"

    def test_channel_values(self) -> None:
        """Test channel enum values."""
        assert Channel.SEARCH.value == "search"
        assert Channel.SOCIAL.value == "social"
        assert Channel.DISPLAY.value == "display"

    def test_goal_values(self) -> None:
        """Test goal enum values."""
        assert CampaignGoal.AWARENESS.value == "awareness"
        assert CampaignGoal.CONVERSION.value == "conversion"
