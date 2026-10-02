"""Recommendation agent for suggesting relevant content to users."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.tools import tool

from content_discovery.agents.base import BaseAgent
from content_discovery.models import Recommendation, RecommendationRequest, RecommendationResponse

if TYPE_CHECKING:
    from content_discovery.integrations.content import ContentClient
    from content_discovery.integrations.user_profile import UserProfileClient

logger = structlog.get_logger()


class RecommendationAgent(BaseAgent[RecommendationRequest, RecommendationResponse]):
    """Agent that generates content recommendations using collaborative and content-based filtering.

    Combines multiple recommendation strategies including collaborative filtering,
    content-based matching, and LLM-powered reasoning to suggest relevant content.
    """

    def __init__(
        self,
        content_client: ContentClient,
        user_profile: UserProfileClient,
        llm: Any | None = None,
    ) -> None:
        """Initialize the recommendation agent.

        Args:
            content_client: Client for content data.
            user_profile: Client for user profile data.
            llm: Optional LLM for recommendation reasoning.
        """
        self.content_client = content_client
        self.user_profile = user_profile
        super().__init__(name="recommendation", llm=llm)

    def _get_tools(self) -> list[Any]:
        """Get tools available to the recommendation agent.

        Returns:
            list[Any]: List of tool instances.
        """
        return [self._get_similar_users_tool, self._get_content_features_tool]

    @tool
    def _get_similar_users_tool(self, user_id: str, limit: int = 10) -> list[str]:
        """Find users with similar preferences.

        Args:
            user_id: Target user identifier.
            limit: Maximum number of similar users.

        Returns:
            list[str]: Similar user IDs.
        """
        return self.user_profile.get_similar_users(user_id=user_id, limit=limit)

    @tool
    def _get_content_features_tool(self, content_id: str) -> dict[str, Any]:
        """Get features and metadata for a content item.

        Args:
            content_id: Content identifier.

        Returns:
            dict[str, Any]: Content features.
        """
        return self.content_client.get_features(content_id=content_id)

    async def execute(self, input_data: RecommendationRequest) -> RecommendationResponse:
        """Generate content recommendations for a user.

        Args:
            input_data: Recommendation request with user context.

        Returns:
            RecommendationResponse: Content recommendations.
        """
        start = time.monotonic()

        # Gather recommendations from multiple strategies
        all_recommendations: list[Recommendation] = []

        # Strategy 1: Content-based recommendations
        content_based = await self._content_based_recs(input_data)
        all_recommendations.extend(content_based)

        # Strategy 2: Collaborative filtering recommendations
        collaborative = await self._collaborative_recs(input_data)
        all_recommendations.extend(collaborative)

        # Strategy 3: LLM-powered recommendations
        llm_recs = await self._llm_recs(input_data)
        all_recommendations.extend(llm_recs)

        # Deduplicate and rank
        unique_recs = self._deduplicate(all_recommendations)
        ranked = self._rank_recommendations(unique_recs, input_data)

        elapsed = (time.monotonic() - start) * 1000

        return RecommendationResponse(
            recommendations=ranked[: input_data.limit],
            user_id=input_data.user_id,
            took_ms=round(elapsed, 2),
        )

    async def _content_based_recs(
        self, request: RecommendationRequest
    ) -> list[Recommendation]:
        """Generate content-based recommendations.

        Args:
            request: Recommendation request.

        Returns:
            list[Recommendation]: Content-based recommendations.
        """
        try:
            history = await self.user_profile.get_history(user_id=request.user_id, limit=50)
            if not history:
                return []

            # Extract user preference profile
            preferred_tags: dict[str, int] = {}
            for item in history:
                for tag in item.get("tags", []):
                    preferred_tags[tag] = preferred_tags.get(tag, 0) + 1

            # Find content with similar tags
            candidates = await self.content_client.get_by_tags(
                tags=list(preferred_tags.keys()),
                limit=request.limit * 2,
            )

            recommendations = []
            for candidate in candidates:
                # Skip already seen content
                if any(h["id"] == candidate["id"] for h in history):
                    continue

                # Calculate tag overlap score
                candidate_tags = set(candidate.get("tags", []))
                preferred_set = set(preferred_tags.keys())
                overlap = len(candidate_tags & preferred_set)
                score = min(overlap / max(len(preferred_set), 1), 1.0)

                recommendations.append(
                    Recommendation(
                        id=f"cb_{candidate['id']}",
                        content_id=candidate["id"],
                        title=candidate.get("title", ""),
                        reason="Similar to content you've enjoyed",
                        score=round(score, 3),
                        metadata={"strategy": "content_based"},
                    )
                )

            return recommendations
        except Exception as exc:
            logger.error("content_based_recs_failed", error=str(exc))
            return []

    async def _collaborative_recs(
        self, request: RecommendationRequest
    ) -> list[Recommendation]:
        """Generate collaborative filtering recommendations.

        Args:
            request: Recommendation request.

        Returns:
            list[Recommendation]: Collaborative recommendations.
        """
        try:
            similar_users = await self.user_profile.get_similar_users(
                user_id=request.user_id, limit=10
            )
            if not similar_users:
                return []

            # Get content consumed by similar users
            candidate_ids: set[str] = set()
            for sim_user in similar_users:
                history = await self.user_profile.get_history(user_id=sim_user, limit=20)
                for item in history:
                    candidate_ids.add(item["id"])

            # Get content details
            recommendations = []
            for cid in list(candidate_ids)[: request.limit * 2]:
                try:
                    features = await self.content_client.get_features(content_id=cid)
                    recommendations.append(
                        Recommendation(
                            id=f"cf_{cid}",
                            content_id=cid,
                            title=features.get("title", ""),
                            reason="Popular with similar users",
                            score=0.7,
                            metadata={"strategy": "collaborative"},
                        )
                    )
                except Exception:
                    pass

            return recommendations
        except Exception as exc:
            logger.error("collaborative_recs_failed", error=str(exc))
            return []

    async def _llm_recs(self, request: RecommendationRequest) -> list[Recommendation]:
        """Generate LLM-powered recommendations.

        Args:
            request: Recommendation request.

        Returns:
            list[Recommendation]: LLM-generated recommendations.
        """
        if self.llm is None:
            return []

        try:
            history = await self.user_profile.get_history(user_id=request.user_id, limit=20)
            history_text = "\n".join(
                f"- {h.get('title', 'Unknown')} (tags: {', '.join(h.get('tags', []))})"
                for h in history
            )

            response = self.llm.invoke(
                f"Based on this user's reading history:\n{history_text}\n\n"
                f"Recommend 5 content IDs that would interest this user. "
                f"Return only the IDs, one per line."
            )

            ids = [
                line.strip()
                for line in response.content.strip().split("\n")
                if line.strip()
            ]

            recommendations = []
            for cid in ids[:5]:
                try:
                    features = await self.content_client.get_features(content_id=cid)
                    recommendations.append(
                        Recommendation(
                            id=f"llm_{cid}",
                            content_id=cid,
                            title=features.get("title", ""),
                            reason="AI-curated recommendation",
                            score=0.8,
                            metadata={"strategy": "llm"},
                        )
                    )
                except Exception:
                    pass

            return recommendations
        except Exception as exc:
            logger.error("llm_recs_failed", error=str(exc))
            return []

    def _deduplicate(self, recommendations: list[Recommendation]) -> list[Recommendation]:
        """Remove duplicate recommendations by content ID.

        Args:
            recommendations: All recommendations.

        Returns:
            list[Recommendation]: Deduplicated recommendations.
        """
        seen: dict[str, Recommendation] = {}
        for rec in recommendations:
            if rec.content_id not in seen or rec.score > seen[rec.content_id].score:
                seen[rec.content_id] = rec
        return list(seen.values())

    def _rank_recommendations(
        self, recommendations: list[Recommendation], request: RecommendationRequest
    ) -> list[Recommendation]:
        """Rank recommendations by score and diversity.

        Args:
            recommendations: Deduplicated recommendations.
            request: Original request.

        Returns:
            list[Recommendation]: Ranked recommendations.
        """
        # Sort by score descending
        recommendations.sort(key=lambda r: r.score, reverse=True)

        # Apply diversity: limit per strategy
        strategy_counts: dict[str, int] = {}
        diverse_recs: list[Recommendation] = []
        max_per_strategy = max(request.limit // 2, 3)

        for rec in recommendations:
            strategy = rec.metadata.get("strategy", "unknown")
            if strategy_counts.get(strategy, 0) < max_per_strategy:
                diverse_recs.append(rec)
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return diverse_recs
