"""Optimization Agent for analyzing conversation patterns and suggesting improvements."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from conversational_marketing.config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class OptimizationSuggestion:
    """A single optimization suggestion."""

    category: str
    title: str
    description: str
    impact: str
    effort: str
    priority: int


@dataclass(frozen=True)
class OptimizationReport:
    """Report containing optimization suggestions."""

    suggestions: list[OptimizationSuggestion]
    total_conversations_analyzed: int
    metadata: dict[str, Any] = field(default_factory=dict)


class OptimizationAgent:
    """Agent responsible for analyzing conversation patterns and suggesting improvements.

    Processes conversation data to identify trends, pain points, and opportunities
    for improving the conversational marketing system.
    """

    def __init__(self) -> None:
        """Initialize the Optimization Agent."""
        self._enabled = settings.agents.optimization.enabled
        self._min_conversations = settings.agents.optimization.min_conversations_for_analysis
        self._suggestion_threshold = settings.agents.optimization.suggestion_threshold

    async def analyze(
        self,
        conversations: list[dict[str, Any]],
        metrics: dict[str, Any] | None = None,
    ) -> OptimizationReport:
        """Analyze conversations and generate optimization suggestions.

        Args:
            conversations: List of conversation data to analyze.
            metrics: Optional pre-computed metrics.

        Returns:
            OptimizationReport with actionable suggestions.

        Raises:
            ValueError: If insufficient conversations for analysis.
        """
        if not self._enabled:
            return OptimizationReport(
                suggestions=[],
                total_conversations_analyzed=0,
                metadata={"disabled": True},
            )

        if len(conversations) < self._min_conversations:
            logger.warning(
                "Insufficient conversations for optimization analysis",
                count=len(conversations),
                required=self._min_conversations,
            )
            return OptimizationReport(
                suggestions=[],
                total_conversations_analyzed=len(conversations),
                metadata={"insufficient_data": True},
            )

        suggestions: list[OptimizationSuggestion] = []

        # Analyze intent distribution
        intent_suggestions = self._analyze_intent_distribution(conversations)
        suggestions.extend(intent_suggestions)

        # Analyze response effectiveness
        effectiveness_suggestions = self._analyze_response_effectiveness(conversations)
        suggestions.extend(effectiveness_suggestions)

        # Analyze handoff patterns
        handoff_suggestions = self._analyze_handoff_patterns(conversations)
        suggestions.extend(handoff_suggestions)

        # Sort by priority
        suggestions.sort(key=lambda s: s.priority, reverse=True)

        logger.info(
            "Optimization analysis complete",
            conversations_analyzed=len(conversations),
            suggestions_generated=len(suggestions),
        )

        return OptimizationReport(
            suggestions=suggestions,
            total_conversations_analyzed=len(conversations),
            metadata={
                "analysis_timestamp": self._get_timestamp(),
                "metrics_included": metrics is not None,
            },
        )

    def _analyze_intent_distribution(
        self, conversations: list[dict[str, Any]]
    ) -> list[OptimizationSuggestion]:
        """Analyze intent distribution for optimization opportunities.

        Args:
            conversations: Conversation data.

        Returns:
            List of optimization suggestions.
        """
        from collections import Counter

        intent_counts: Counter[str] = Counter()
        for conv in conversations:
            intent = conv.get("intent", "unknown")
            intent_counts[intent] += 1

        total = len(conversations)
        suggestions: list[OptimizationSuggestion] = []

        for intent, count in intent_counts.most_common():
            ratio = count / total
            if ratio > 0.4 and intent not in ("greeting", "farewell"):
                suggestions.append(
                    OptimizationSuggestion(
                        category="intent_coverage",
                        title=f"High volume of '{intent}' intents",
                        description=(
                            f"{ratio:.0%} of conversations are classified as '{intent}'. "
                            "Consider creating specialized response templates or "
                            "dedicated flows for this intent."
                        ),
                        impact="medium",
                        effort="medium",
                        priority=8,
                    )
                )

        return suggestions

    def _analyze_response_effectiveness(
        self, conversations: list[dict[str, Any]]
    ) -> list[OptimizationSuggestion]:
        """Analyze response effectiveness metrics.

        Args:
            conversations: Conversation data.

        Returns:
            List of optimization suggestions.
        """
        suggestions: list[OptimizationSuggestion] = []

        # Check for conversations with low satisfaction
        low_satisfaction = [
            c for c in conversations
            if c.get("satisfaction_score", 1.0) < 0.5
        ]

        if len(low_satisfaction) > len(conversations) * 0.2:
            suggestions.append(
                OptimizationSuggestion(
                    category="response_quality",
                    title="High rate of low-satisfaction conversations",
                    description=(
                        f"{len(low_satisfaction)} conversations had low satisfaction. "
                        "Review response templates and consider A/B testing alternatives."
                    ),
                    impact="high",
                    effort="high",
                    priority=9,
                )
            )

        return suggestions

    def _analyze_handoff_patterns(
        self, conversations: list[dict[str, Any]]
    ) -> list[OptimizationSuggestion]:
        """Analyze handoff patterns for optimization.

        Args:
            conversations: Conversation data.

        Returns:
            List of optimization suggestions.
        """
        suggestions: list[OptimizationSuggestion] = []

        handoff_conversations = [c for c in conversations if c.get("handed_off", False)]
        handoff_rate = len(handoff_conversations) / len(conversations) if conversations else 0

        if handoff_rate > 0.3:
            suggestions.append(
                OptimizationSuggestion(
                    category="handoff_optimization",
                    title="High handoff rate detected",
                    description=(
                        f"{handoff_rate:.0%} of conversations are handed off to humans. "
                        "Consider improving agent capabilities or adjusting handoff thresholds."
                    ),
                    impact="high",
                    effort="medium",
                    priority=7,
                )
            )

        return suggestions

    @staticmethod
    def _get_timestamp() -> str:
        """Get current ISO timestamp.

        Returns:
            ISO formatted timestamp string.
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
