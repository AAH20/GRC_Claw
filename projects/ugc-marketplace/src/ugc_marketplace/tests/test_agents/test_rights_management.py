"""Tests for rights management agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.rights_management import (
    InfringementDetectorAgent,
    LicenseDetectorAgent,
    RightsValidatorAgent,
    TakedownAgent,
    UsageTrackerAgent,
)


@pytest.mark.asyncio
async def test_infringement_detector_agent() -> None:
    """Test infringement detector agent."""
    agent = InfringementDetectorAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_license_detector_agent() -> None:
    """Test license detector agent."""
    agent = LicenseDetectorAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_rights_validator_agent() -> None:
    """Test rights validator agent."""
    agent = RightsValidatorAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_takedown_agent() -> None:
    """Test takedown agent."""
    agent = TakedownAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_usage_tracker_agent() -> None:
    """Test usage tracker agent."""
    agent = UsageTrackerAgent()
    assert agent is not None
