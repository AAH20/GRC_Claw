"""Reputation History Agent for tracking and analyzing reputation changes."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from reputation_system.agents.base import BaseAgent
from reputation_system.models.schemas import ReputationHistory


class HistoryQueryInput(BaseModel):
    """Input for reputation history queries."""

    member_id: str = Field(..., description="Member identifier")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    action_filter: Optional[str] = Field(None, description="Filter by action type")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum results")


class HistoryAnalysisInput(BaseModel):
    """Input for reputation history analysis."""

    member_id: str = Field(..., description="Member identifier")
    history_entries: List[Dict[str, Any]] = Field(..., description="History entries to analyze")


class HistoryAnalysisOutput(BaseModel):
    """Output from history analysis."""

    member_id: str
    total_entries: int
    net_change: int
    average_change: float
    most_common_action: Optional[str]
    trend: str
    insights: List[str] = Field(default_factory=list)


class ReputationHistoryAgent(BaseAgent[HistoryAnalysisInput, HistoryAnalysisOutput]):
    """Agent that tracks and analyzes reputation change history."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the reputation history agent."""
        return """You are a reputation history analysis agent. Your task is to analyze
        a member's reputation change history, identify trends, and provide insights
        into their reputation trajectory."""

    async def run(self, input_data: HistoryAnalysisInput) -> HistoryAnalysisOutput:
        """Analyze reputation history for a member.

        Args:
            input_data: History analysis input data.

        Returns:
            History analysis results with trends and insights.
        """
        entries = input_data.history_entries
        total_entries = len(entries)

        if not entries:
            return HistoryAnalysisOutput(
                member_id=input_data.member_id,
                total_entries=0,
                net_change=0,
                average_change=0.0,
                most_common_action=None,
                trend="stable",
                insights=["No history entries found"],
            )

        # Calculate net change
        net_change = sum(entry.get("score_change", 0) for entry in entries)
        average_change = net_change / total_entries

        # Find most common action
        action_counts: Dict[str, int] = {}
        for entry in entries:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        most_common_action = max(action_counts, key=lambda k: action_counts[k]) if action_counts else None

        # Determine trend
        if len(entries) >= 2:
            first_half = entries[: len(entries) // 2]
            second_half = entries[len(entries) // 2 :]
            first_avg = sum(e.get("score_change", 0) for e in first_half) / len(first_half)
            second_avg = sum(e.get("score_change", 0) for e in second_half) / len(second_half)

            if second_avg > first_avg * 1.1:
                trend = "improving"
            elif second_avg < first_avg * 0.9:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Generate insights
        insights = self._generate_insights(entries, net_change, trend)

        return HistoryAnalysisOutput(
            member_id=input_data.member_id,
            total_entries=total_entries,
            net_change=net_change,
            average_change=average_change,
            most_common_action=most_common_action,
            trend=trend,
            insights=insights,
        )

    def _generate_insights(
        self, entries: List[Dict[str, Any]], net_change: int, trend: str
    ) -> List[str]:
        """Generate insights from history data.

        Args:
            entries: History entries.
            net_change: Net score change.
            trend: Identified trend.

        Returns:
            List of insight strings.
        """
        insights: List[str] = []

        if net_change > 0:
            insights.append(f"Net positive change of {net_change} points")
        elif net_change < 0:
            insights.append(f"Net negative change of {abs(net_change)} points")
        else:
            insights.append("No net change in reputation score")

        if trend == "improving":
            insights.append("Reputation is trending upward")
        elif trend == "declining":
            insights.append("Reputation is trending downward - attention needed")

        # Check for rapid changes
        rapid_changes = [
            e for e in entries if abs(e.get("score_change", 0)) > 100
        ]
        if rapid_changes:
            insights.append(f"{len(rapid_changes)} significant reputation changes detected")

        return insights
