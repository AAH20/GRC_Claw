"""Personalization agent for dynamic content recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class UserProfile:
    """User profile for personalization.

    Attributes:
        user_id: Unique user identifier.
        segments: User segment tags.
        preferences: User preference key-value pairs.
        visit_count: Number of visits.
        last_visit: Last visit timestamp.
    """

    user_id: str
    segments: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    visit_count: int = 0
    last_visit: datetime | None = None


@dataclass
class PersonalizationRule:
    """A personalization rule.

    Attributes:
        id: Rule identifier.
        name: Human-readable rule name.
        conditions: Conditions that must match for the rule to apply.
        content: Content to serve when conditions match.
        priority: Rule priority (higher = more important).
        enabled: Whether the rule is active.
    """

    id: str
    name: str
    conditions: dict[str, Any]
    content: dict[str, Any]
    priority: int = 0
    enabled: bool = True


@dataclass
class Recommendation:
    """A personalization recommendation.

    Attributes:
        rule_id: Source rule identifier.
        content: Recommended content.
        score: Relevance score (0.0 to 1.0).
        reason: Human-readable reason for the recommendation.
    """

    rule_id: str
    content: dict[str, Any]
    score: float
    reason: str


class PersonalizationAgent:
    """Agent for generating personalized content recommendations.

    This agent uses user profiles, behavioral data, and configurable rules
    to deliver personalized content to website visitors.
    """

    def __init__(self, max_recommendations: int = 10, cache_ttl_seconds: int = 300) -> None:
        """Initialize the Personalization agent.

        Args:
            max_recommendations: Maximum number of recommendations to return.
            cache_ttl_seconds: Cache time-to-live in seconds.
        """
        self._rules: dict[str, PersonalizationRule] = {}
        self._user_profiles: dict[str, UserProfile] = {}
        self._max_recommendations = max_recommendations
        self._cache_ttl_seconds = cache_ttl_seconds
        logger.info(
            "PersonalizationAgent initialized",
            max_recommendations=max_recommendations,
            cache_ttl=cache_ttl_seconds,
        )

    def add_rule(self, rule: PersonalizationRule) -> None:
        """Add a personalization rule.

        Args:
            rule: The rule to add.
        """
        self._rules[rule.id] = rule
        logger.info("Personalization rule added", rule_id=rule.id, name=rule.name)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a personalization rule.

        Args:
            rule_id: The rule identifier.

        Returns:
            True if rule was removed, False if not found.
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info("Personalization rule removed", rule_id=rule_id)
            return True
        return False

    def update_user_profile(self, profile: UserProfile) -> None:
        """Update or create a user profile.

        Args:
            profile: The user profile to store.
        """
        profile.last_visit = datetime.utcnow()
        self._user_profiles[profile.user_id] = profile
        logger.debug("User profile updated", user_id=profile.user_id)

    def get_user_profile(self, user_id: str) -> UserProfile | None:
        """Retrieve a user profile.

        Args:
            user_id: The user identifier.

        Returns:
            The user profile if found, None otherwise.
        """
        return self._user_profiles.get(user_id)

    def get_recommendations(
        self, user_id: str, page_url: str, context: dict[str, Any] | None = None
    ) -> list[Recommendation]:
        """Get personalized content recommendations for a user.

        Args:
            user_id: The user identifier.
            page_url: Current page URL.
            context: Additional context for personalization.

        Returns:
            List of recommendations sorted by score (descending).
        """
        profile = self._user_profiles.get(user_id)
        if not profile:
            logger.debug(
                "No user profile found, returning default recommendations",
                user_id=user_id,
            )
            return self._get_default_recommendations(page_url)

        context = context or {}
        recommendations: list[Recommendation] = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue
            score = self._evaluate_rule(rule, profile, page_url, context)
            if score > 0:
                recommendations.append(
                    Recommendation(
                        rule_id=rule.id,
                        content=rule.content,
                        score=score,
                        reason=f"Matched rule: {rule.name}",
                    )
                )

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[: self._max_recommendations]

    def _evaluate_rule(
        self,
        rule: PersonalizationRule,
        profile: UserProfile,
        page_url: str,
        context: dict[str, Any],
    ) -> float:
        """Evaluate how well a rule matches a user profile.

        Args:
            rule: The personalization rule.
            profile: The user profile.
            page_url: Current page URL.
            context: Additional context.

        Returns:
            Match score from 0.0 to 1.0.
        """
        score = 0.0
        conditions = rule.conditions

        if "segments" in conditions:
            required_segments = set(conditions["segments"])
            user_segments = set(profile.segments)
            overlap = required_segments & user_segments
            if overlap:
                score += 0.5 * (len(overlap) / len(required_segments))

        if "min_visit_count" in conditions and profile.visit_count >= conditions["min_visit_count"]:
            score += 0.3

        if "page_pattern" in conditions:
            import re

            if re.search(conditions["page_pattern"], page_url):
                score += 0.2

        return min(score, 1.0)

    def _get_default_recommendations(self, page_url: str) -> list[Recommendation]:
        """Get default recommendations for unknown users.

        Args:
            page_url: Current page URL.

        Returns:
            List of default recommendations.
        """
        return [
            Recommendation(
                rule_id="default",
                content={"type": "default", "message": "Welcome!"},
                score=0.1,
                reason="Default recommendation for new visitors",
            )
        ]
