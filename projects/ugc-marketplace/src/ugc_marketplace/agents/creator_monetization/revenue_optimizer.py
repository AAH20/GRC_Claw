"""Revenue Optimizer Agent for creator monetization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class RevenueStream(BaseModel):
    """A revenue stream configuration."""

    name: str = Field(..., description="Revenue stream name")
    type: str = Field(
        ..., description="Stream type (subscription, tips, merchandise, etc.)"
    )
    monthly_amount: Decimal = Field(default=Decimal("0"), ge=0)
    growth_rate: float = Field(default=0.0, ge=-1.0, le=10.0)


class OptimizationSuggestion(BaseModel):
    """A revenue optimization suggestion."""

    category: str = Field(..., description="Suggestion category")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    potential_impact: Decimal = Field(..., description="Estimated monthly impact")
    effort_level: str = Field(
        ..., description="Implementation effort (low, medium, high)"
    )
    priority: int = Field(default=5, ge=1, le=10)


class RevenueOptimizerAgent:
    """Agent responsible for optimizing creator revenue streams.

    Analyzes current revenue, identifies opportunities,
    and provides actionable optimization suggestions.
    """

    def __init__(self) -> None:
        """Initialize the revenue optimizer agent."""
        self._streams: dict[str, list[RevenueStream]] = {}
        self._suggestions: dict[str, list[OptimizationSuggestion]] = {}

    async def add_revenue_stream(
        self,
        creator_id: str,
        stream: RevenueStream,
    ) -> dict[str, Any]:
        """Add a revenue stream for a creator.

        Args:
            creator_id: Creator identifier.
            stream: Revenue stream configuration.

        Returns:
            Confirmation data.
        """
        if creator_id not in self._streams:
            self._streams[creator_id] = []
        self._streams[creator_id].append(stream)
        logger.info("Revenue stream added", creator_id=creator_id, stream=stream.name)
        return {
            "creator_id": creator_id,
            "stream": stream.model_dump(),
            "status": "added",
        }

    async def analyze_revenue(self, creator_id: str) -> dict[str, Any]:
        """Analyze revenue streams for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            Revenue analysis data.
        """
        streams = self._streams.get(creator_id, [])
        total_monthly = sum(s.monthly_amount for s in streams)
        by_type: dict[str, Decimal] = {}
        for s in streams:
            by_type[s.type] = by_type.get(s.type, Decimal("0")) + s.monthly_amount

        return {
            "creator_id": creator_id,
            "total_monthly_revenue": str(total_monthly),
            "stream_count": len(streams),
            "revenue_by_type": {k: str(v) for k, v in by_type.items()},
            "streams": [s.model_dump() for s in streams],
        }

    async def generate_suggestions(
        self, creator_id: str
    ) -> list[OptimizationSuggestion]:
        """Generate optimization suggestions for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            List of optimization suggestions.
        """
        streams = self._streams.get(creator_id, [])
        suggestions: list[OptimizationSuggestion] = []

        stream_types = {s.type for s in streams}

        if "subscription" not in stream_types:
            suggestions.append(
                OptimizationSuggestion(
                    category="diversification",
                    title="Add Subscription Revenue",
                    description="Consider adding a subscription tier to create predictable recurring revenue.",
                    potential_impact=Decimal("500.00"),
                    effort_level="medium",
                    priority=9,
                )
            )

        if "merchandise" not in stream_types:
            suggestions.append(
                OptimizationSuggestion(
                    category="diversification",
                    title="Launch Merchandise Store",
                    description="Selling merchandise can significantly boost revenue and strengthen brand loyalty.",
                    potential_impact=Decimal("300.00"),
                    effort_level="high",
                    priority=7,
                )
            )

        if len(streams) > 0:
            avg_growth = sum(s.growth_rate for s in streams) / len(streams)
            if avg_growth < 0.05:
                suggestions.append(
                    OptimizationSuggestion(
                        category="growth",
                        title="Increase Content Frequency",
                        description="Higher content frequency correlates with audience growth and revenue increase.",
                        potential_impact=Decimal("200.00"),
                        effort_level="low",
                        priority=8,
                    )
                )

        self._suggestions[creator_id] = suggestions
        logger.info(
            "Suggestions generated", creator_id=creator_id, count=len(suggestions)
        )
        return suggestions

    def get_suggestions(self, creator_id: str) -> list[OptimizationSuggestion]:
        """Get previously generated suggestions.

        Args:
            creator_id: Creator identifier.

        Returns:
            List of suggestions.
        """
        return self._suggestions.get(creator_id, [])
