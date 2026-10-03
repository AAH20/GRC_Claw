"""Tests for content moderation agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.content_moderation import (AppealHandlerAgent,
                                                       ImageModerationAgent,
                                                       PolicyEnforcementAgent,
                                                       TextModerationAgent,
                                                       VideoModerationAgent)
from ugc_marketplace.models.schemas import ContentType


@pytest.mark.asyncio
async def test_text_moderation_agent() -> None:
    """Test text moderation agent."""
    agent = TextModerationAgent()
    assert agent.content_type == ContentType.TEXT


@pytest.mark.asyncio
async def test_image_moderation_agent() -> None:
    """Test image moderation agent."""
    agent = ImageModerationAgent()
    assert agent.content_type == ContentType.IMAGE


@pytest.mark.asyncio
async def test_video_moderation_agent() -> None:
    """Test video moderation agent."""
    agent = VideoModerationAgent()
    assert agent.content_type == ContentType.VIDEO


@pytest.mark.asyncio
async def test_policy_enforcement_agent() -> None:
    """Test policy enforcement agent."""
    agent = PolicyEnforcementAgent()
    assert agent.content_type == ContentType.TEXT


@pytest.mark.asyncio
async def test_appeal_handler_agent() -> None:
    """Test appeal handler agent."""
    agent = AppealHandlerAgent()
    assert agent.content_type == ContentType.TEXT
