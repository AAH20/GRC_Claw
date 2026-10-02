"""Tests for rights-management agents."""

from __future__ import annotations

import pytest

from rights_management.agents.infringement_detector import InfringementDetectorAgent
from rights_management.agents.license_detector import LicenseDetectorAgent
from rights_management.agents.rights_validator import RightsValidatorAgent
from rights_management.agents.takedown import TakedownAgent
from rights_management.agents.usage_tracker import UsageTrackerAgent
from rights_management.models import (
    InfringementDetectionRequest,
    LicenseDetectionRequest,
    RightsValidationRequest,
    TakedownProcessRequest,
    TakedownRequest,
    TakedownStatus,
    UsageRecord,
    UsageType,
)


class TestLicenseDetectorAgent:
    """Tests for the LicenseDetectorAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_result(self) -> None:
        """Test that the agent returns a detection result."""
        agent = LicenseDetectorAgent()
        payload = LicenseDetectionRequest(
            content_id="test-content",
            content_text="Test content for license detection",
        )
        result = await agent.run(payload)
        assert result.content_id == "test-content"
        assert 0.0 <= result.confidence <= 1.0


class TestUsageTrackerAgent:
    """Tests for the UsageTrackerAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_record(self) -> None:
        """Test that the agent returns a usage record."""
        agent = UsageTrackerAgent()
        payload = {
            "content_id": "test-content",
            "usage_type": "view",
            "user_id": "test-user",
        }
        result = await agent.run(payload)
        assert result.content_id == "test-content"
        assert result.user_id == "test-user"

    @pytest.mark.asyncio
    async def test_summarize(self) -> None:
        """Test usage summary generation."""
        agent = UsageTrackerAgent()
        records = [
            UsageRecord(
                id="1",
                content_id="test-content",
                usage_type=UsageType.VIEW,
                user_id="user-1",
            ),
            UsageRecord(
                id="2",
                content_id="test-content",
                usage_type=UsageType.DOWNLOAD,
                user_id="user-2",
            ),
        ]
        summary = await agent.summarize("test-content", records)
        assert summary.content_id == "test-content"
        assert summary.total_uses == 2
        assert summary.unique_users == 2


class TestInfringementDetectorAgent:
    """Tests for the InfringementDetectorAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_result(self) -> None:
        """Test that the agent returns a detection result."""
        agent = InfringementDetectorAgent()
        payload = InfringementDetectionRequest(
            content_id="test-content",
            content_text="Test content for infringement detection",
        )
        result = await agent.run(payload)
        assert result.content_id == "test-content"
        assert 0.0 <= result.risk_score <= 1.0


class TestRightsValidatorAgent:
    """Tests for the RightsValidatorAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_validation(self) -> None:
        """Test that the agent returns a validation result."""
        agent = RightsValidatorAgent()
        payload = RightsValidationRequest(
            content_id="test-content",
            usage_type=UsageType.VIEW,
            user_id="test-user",
        )
        result = await agent.run(payload)
        assert result.content_id == "test-content"
        assert result.usage_type == UsageType.VIEW


class TestTakedownAgent:
    """Tests for the TakedownAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_request(self) -> None:
        """Test that the agent returns a takedown request."""
        agent = TakedownAgent()
        payload = {
            "id": "test-id",
            "content_id": "test-content",
            "requester_id": "test-requester",
            "reason": "Test reason",
        }
        result = await agent.run(payload)
        assert result.id == "test-id"
        assert result.content_id == "test-content"

    @pytest.mark.asyncio
    async def test_process(self) -> None:
        """Test processing a takedown request."""
        agent = TakedownAgent()
        request = TakedownRequest(
            id="test-id",
            content_id="test-content",
            requester_id="test-requester",
            reason="Test reason",
        )
        process_req = TakedownProcessRequest(
            action=TakedownStatus.APPROVED,
            reviewer_id="reviewer-1",
            notes="Approved after review",
        )
        result = await agent.process(request, process_req)
        assert result.status == TakedownStatus.APPROVED
        assert result.processed_at is not None
