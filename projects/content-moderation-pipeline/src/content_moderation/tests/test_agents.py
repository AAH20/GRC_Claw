"""Agent unit tests."""

from __future__ import annotations

import pytest

from content_moderation.agents import (
    AppealHandlerAgent,
    ImageModerationAgent,
    PolicyEnforcementAgent,
    TextModerationAgent,
    VideoModerationAgent,
)
from content_moderation.models.schemas import ContentType


@pytest.mark.parametrize(
    "agent_class,expected_type",
    [
        (TextModerationAgent, ContentType.TEXT),
        (ImageModerationAgent, ContentType.IMAGE),
        (VideoModerationAgent, ContentType.VIDEO),
        (PolicyEnforcementAgent, ContentType.TEXT),
        (AppealHandlerAgent, ContentType.TEXT),
    ],
)
def test_agent_content_type(agent_class: type, expected_type: ContentType) -> None:
    """Test each agent reports correct content type."""
    agent = agent_class.__new__(agent_class)
    # Bypass __init__ to avoid needing API keys
    object.__init__(agent)
    assert agent.content_type == expected_type
