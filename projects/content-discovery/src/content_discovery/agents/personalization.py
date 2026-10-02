"""Personalization agent for tailoring content to individual users."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.tools import tool

from content_discovery.agents.base import BaseAgent
from content_discovery.models import Recommendation, RecommendationRequest, RecommendationResponse

if TYPE_CHECKING:
    from content_discovery.integrations.user_profile import UserProfileClient

logger = structlog.get_logger()


class PersonalizationAgent(BaseAgent[RecommendationRequest, RecommendationResponse]):
    """Agent that personalizes content recommendations based on user profiles.

    Analyzes user history, preferences, and behavior patterns to deliver
    tailored content suggestions.
    """

    def __init__(self, user_profile: UserProfileClient, llm: Any | None = None) -> None:
        """Initialize the personalization agent.

        Args:
            user_profile: Client for user profile data.
            llm: Optional LLM for preference inference.
        """
        self.user_profile = user_profile
        super().__init__(name="personalization", llm=llm)

    def _get_tools(self) -> list[Any]:
        """Get tools available to the personalization agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return [self._get_user_history_tool, self._infer_preferences_tool]

    @tool
    def _get_user_history_tool(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve user's content interaction history.

        Args:
            user_id: User identifier.
            limit: Maximum history items to retrieve.

        Returns:
            list[dict[str, Any]]: User interaction history.
        """
        return self.user_profile.get_history(user_id=user_id, limit=limit)

    @tool
    def _infer_preferences_tool(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        """Infer user preferences from interaction history.

        Args:
            history: User interaction history.

        Returns:
            dict[str, Any]: Inferred preferences.
        """
        if not history:
            return {"topics": [], "content_types": [], "authors": []}

        topics: dict[str, int] = {}
        content_types: dict[str, int] = {}
        authors: dict[str, int] = {}

        for item in history:
            for tag in item.get("tags", []):
                topics[tag] = topics.get(tag, 0) + 1
            ct = item.get("content_type", "article")
            content_types[ct] = content_types.get(ct, 0) + 1
            author = item.get("author")
            if author:
                authors[author] = authors.get(author, 0) + 1

        return {
            "topics": sorted(topics, key=topics.get, reverse=True)[:10],
            "content_types": sorted(content_types, key=content_types.get, reverse=True)[:5],
            "authors": sorted(authors, key=authors.get, reverse=True)[:5],
        }

    async def execute(self, input_data: RecommendationRequest) -> RecommendationResponse:
        """Generate personalized recommendations for a user.

        Args:
            input_data: Recommendation request with user context.

        Returns:
            RecommendationResponse: Personalized content recommendations.
        """
        start = time.monotonic()

        # Get user preferences
        preferences = await self._get_user_preferences(input_data.user_id)

        # Get candidate content based on preferences
        candidates = await self._get_candidates(preferences, input_data)

        # Score and rank candidates
        scored = await self._score_candidates(candidates, preferences, input_data.context)

        # Build recommendations
        recommendations = [
            Recommendation(
                id=f"rec_{i}",
                content_id=c["id"],
                title=c.get("title", ""),
                reason=c.get("reason", "Based on your interests"),
                score=c["score"],
                metadata=c.get("metadata", {}),
            )
            for i, c in enumerate(scored[: input_data.limit])
        ]

        elapsed = (time.monotonic() - start) * 1000

        return RecommendationResponse(
            recommendations=recommendations,
            user_id=input_data.user_id,
            took_ms=round(elapsed, 2),
        )

    async def _get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """Get user preferences from profile and history.

        Args:
            user_id: User identifier.

        Returns:
            dict[str, Any]: User preferences.
        """
        try:
            history = await self.user_profile.get_history(user_id=user_id, limit=50)
            return self._infer_preferences_from_history(history)
        except Exception as exc:
            logger.error("get_preferences_failed", user_id=user_id, error=str(exc))
            return {"topics": [], "content_types": [], "authors": []}

    def _infer_preferences_from_history(
        self, history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Infer preferences from user history.

        Args:
            history: User interaction history.

        Returns:
            dict[str, Any]: Inferred preferences.
        """
        topics: dict[str, int] = {}
        content_types: dict[str, int] = {}
        authors: dict[str, int] = {}

        for item in history:
            for tag in item.get("tags", []):
                topics[tag] = topics.get(tag, 0) + 1
            ct = item.get("content_type", "article")
            content_types[ct] = content_types.get(ct, 0) + 1
            author = item.get("author")
            if author:
                authors[author] = authors.get(author, 0) + 1

        return {
            "topics": sorted(topics, key=topics.get, reverse=True)[:10],
            "content_types": sorted(content_types, key=content_types.get, reverse=True)[:5],
            "authors": sorted(authors, key=authors.get, reverse=True)[:5],
        }

    async def _get_candidates(
        self, preferences: dict[str, Any], request: RecommendationRequest
    ) -> list[dict[str, Any]]:
        """Get candidate content for recommendations.

        Args:
            preferences: User preferences.
            request: Recommendation request.

        Returns:
            list[dict[str, Any]]: Candidate content items.
        """
        try:
            return await self.user_profile.get_candidates(
                topics=preferences.get("topics", []),
                content_types=request.content_types or preferences.get("content_types", []),
                limit=request.limit * 3,
            )
        except Exception as exc:
            logger.error("get_candidates_failed", error=str(exc))
            return []

    async def _score_candidates(
        self,
        candidates: list[dict[str, Any]],
        preferences: dict[str, Any],
        context: str | None,
    ) -> list[dict[str, Any]]:
        """Score candidate content for relevance to user.

        Args:
            candidates: Candidate content items.
            preferences: User preferences.
            context: Optional context string.

        Returns:
            list[dict[str, Any]]: Scored and sorted candidates.
        """
        scored = []
        pref_topics = set(preferences.get("topics", []))
        pref_authors = set(preferences.get("authors", []))

        for candidate in candidates:
            score = 0.0
            reasons = []

            # Topic match
            candidate_tags = set(candidate.get("tags", []))
            topic_overlap = len(pref_topics & candidate_tags)
            if topic_overlap > 0:
                score += min(topic_overlap * 0.2, 0.6)
                reasons.append(f"Matches {topic_overlap} of your interests")

            # Author match
            if candidate.get("author") in pref_authors:
                score += 0.2
                reasons.append("From an author you follow")

            # Content type preference
            if candidate.get("content_type") in preferences.get("content_types", []):
                score += 0.1
                reasons.append("Preferred content type")

            # Context relevance (simplified)
            if context and self._text_similarity(context, candidate.get("title", "")) > 0.5:
                score += 0.1
                reasons.append("Relevant to your current context")

            scored.append({
                **candidate,
                "score": min(score, 1.0),
                "reason": "; ".join(reasons) if reasons else "Recommended for you",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Compute simple text similarity.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            float: Similarity score between 0 and 1.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))
