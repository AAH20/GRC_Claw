"""Personalization agent for content discovery."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog

from ugc_marketplace.agents.content_discovery.base import BaseAgent

if TYPE_CHECKING:
    from ugc_marketplace.models.schemas import (RecommendationRequest,
                                                RecommendationResponse)

logger = structlog.get_logger(__name__)


class PersonalizationAgent(
    BaseAgent["RecommendationRequest", "RecommendationResponse"]
):
    """Agent that personalizes content recommendations for users.

    Uses user behavior, preferences, and context to generate
    personalized content suggestions.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgent for personalization.

        Returns:
            Configured DeepAgent instance.
        """
        tools = [
            self._get_user_preferences,
            self._get_content_metadata,
            self._rank_content,
        ]

        from deepagents import create_deep_agent

        agent = create_deep_agent(
            tools=tools,
            instructions=(
                "You are a content personalization specialist. Analyze user "
                "preferences and behavior to generate personalized content "
                "recommendations. Consider user history, context, and content "
                "metadata to provide relevant suggestions."
            ),
        )
        return agent

    async def execute(
        self, input_data: RecommendationRequest
    ) -> RecommendationResponse:
        """Execute personalization for a user.

        Args:
            input_data: Recommendation request with user context.

        Returns:
            Personalized recommendation response.
        """
        start_time = time.monotonic()
        result = await self._timed_execute(input_data, "execute")
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "Personalization completed",
            user_id=getattr(input_data, "user_id", "unknown"),
            elapsed_ms=elapsed_ms,
        )
        return result

    @staticmethod
    async def _get_user_preferences(user_id: str) -> dict[str, Any]:
        """Get user preferences.

        Args:
            user_id: User identifier.

        Returns:
            User preference data.
        """
        return {"user_id": user_id, "preferences": {}}

    @staticmethod
    async def _get_content_metadata(content_id: str) -> dict[str, Any]:
        """Get content metadata.

        Args:
            content_id: Content identifier.

        Returns:
            Content metadata.
        """
        return {"content_id": content_id, "metadata": {}}

    @staticmethod
    async def _rank_content(
        content_ids: list[str], preferences: dict[str, Any]
    ) -> list[str]:
        """Rank content based on preferences.

        Args:
            content_ids: List of content identifiers.
            preferences: User preferences.

        Returns:
            Ranked list of content identifiers.
        """
        return content_ids
