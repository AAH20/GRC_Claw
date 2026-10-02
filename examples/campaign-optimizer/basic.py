"""
Basic Campaign Optimization Example
====================================

Demonstrates core campaign optimization functionality including:
- Campaign creation and configuration
- Budget allocation across channels
- Performance tracking and basic optimization
- ROI calculation and reporting

Usage:
    python basic.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Supported advertising channels."""

    SEARCH = "search"
    SOCIAL = "social"
    DISPLAY = "display"
    EMAIL = "email"
    VIDEO = "video"


class CampaignStatus(str, Enum):
    """Campaign lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class OptimizationError(Exception):
    """Raised when campaign optimization fails."""

    pass


class BudgetError(OptimizationError):
    """Raised when budget constraints are violated."""

    pass


@dataclass
class ChannelPerformance:
    """Performance metrics for a single channel."""

    channel: ChannelType
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0

    @property
    def ctr(self) -> float:
        """Click-through rate."""
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return self.spend / self.clicks if self.clicks > 0 else 0.0

    @property
    def roas(self) -> float:
        """Return on ad spend."""
        return self.revenue / self.spend if self.spend > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        """Conversion rate from clicks."""
        return self.conversions / self.clicks if self.clicks > 0 else 0.0


@dataclass
class Campaign:
    """Represents an advertising campaign."""

    name: str
    budget: float
    channels: list[ChannelType]
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime | None = None
    performance: dict[ChannelType, ChannelPerformance] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize performance tracking for each channel."""
        for channel in self.channels:
            if channel not in self.performance:
                self.performance[channel] = ChannelPerformance(channel=channel)

    @property
    def total_spend(self) -> float:
        """Total spend across all channels."""
        return sum(p.spend for p in self.performance.values())

    @property
    def total_revenue(self) -> float:
        """Total revenue across all channels."""
        return sum(p.revenue for p in self.performance.values())

    @property
    def total_conversions(self) -> int:
        """Total conversions across all channels."""
        return sum(p.conversions for p in self.performance.values())

    @property
    def remaining_budget(self) -> float:
        """Remaining budget."""
        return self.budget - self.total_spend

    @property
    def overall_roas(self) -> float:
        """Overall return on ad spend."""
        return self.total_revenue / self.total_spend if self.total_spend > 0 else 0.0


class CampaignOptimizer:
    """Basic campaign optimizer with budget reallocation."""

    def __init__(self, min_channel_budget: float = 100.0) -> None:
        """Initialize the optimizer.

        Args:
            min_channel_budget: Minimum budget to allocate to any channel.
        """
        self.min_channel_budget = min_channel_budget
        self.campaigns: dict[str, Campaign] = {}

    def create_campaign(
        self,
        name: str,
        budget: float,
        channels: list[ChannelType],
        duration_days: int = 30,
    ) -> Campaign:
        """Create a new campaign.

        Args:
            name: Campaign name.
            budget: Total budget.
            channels: List of channels to use.
            duration_days: Campaign duration in days.

        Returns:
            The created Campaign instance.

        Raises:
            BudgetError: If budget is insufficient for channels.
        """
        if budget < self.min_channel_budget * len(channels):
            raise BudgetError(
                f"Budget ${budget:.2f} is insufficient for {len(channels)} channels. "
                f"Minimum required: ${self.min_channel_budget * len(channels):.2f}"
            )

        end_date = datetime.now() + timedelta(days=duration_days)
        campaign = Campaign(
            name=name,
            budget=budget,
            channels=channels,
            end_date=end_date,
        )
        self.campaigns[name] = campaign
        logger.info("Created campaign '%s' with budget $%.2f", name, budget)
        return campaign

    def allocate_budget(self, campaign: Campaign) -> dict[ChannelType, float]:
        """Allocate budget equally across channels.

        Args:
            campaign: The campaign to allocate budget for.

        Returns:
            Dictionary mapping channels to allocated budgets.
        """
        if not campaign.channels:
            raise OptimizationError("Campaign has no channels")

        per_channel = campaign.budget / len(campaign.channels)
        allocation = {ch: per_channel for ch in campaign.channels}
        logger.info(
            "Allocated $%.2f per channel for campaign '%s'",
            per_channel,
            campaign.name,
        )
        return allocation

    def optimize(self, campaign: Campaign) -> dict[str, Any]:
        """Run basic optimization on a campaign.

        Reallocates budget from underperforming channels to top performers.

        Args:
            campaign: The campaign to optimize.

        Returns:
            Optimization results with recommendations.
        """
        if campaign.status != CampaignStatus.ACTIVE:
            raise OptimizationError(
                f"Cannot optimize campaign with status '{campaign.status.value}'"
            )

        if not campaign.performance:
            raise OptimizationError("No performance data available")

        # Calculate performance scores
        scores: dict[ChannelType, float] = {}
        for ch, perf in campaign.performance.items():
            # Simple scoring: weight ROAS and conversion rate
            scores[ch] = perf.roas * 0.6 + perf.conversion_rate * 100 * 0.4

        # Sort channels by score
        sorted_channels = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]

        # Reallocate: give more to top performers
        total_budget = campaign.budget
        allocations: dict[ChannelType, float] = {}

        # Top performer gets 50%, second gets 30%, rest share 20%
        weights = [0.5, 0.3, 0.2]
        for i, ch in enumerate(sorted_channels):
            if i < len(weights):
                allocations[ch] = total_budget * weights[i]
            else:
                allocations[ch] = total_budget * 0.05

        # Ensure minimum budget
        for ch in allocations:
            if allocations[ch] < self.min_channel_budget:
                allocations[ch] = self.min_channel_budget

        results = {
            "campaign": campaign.name,
            "timestamp": datetime.now().isoformat(),
            "scores": {ch.value: round(score, 4) for ch, score in scores.items()},
            "recommended_allocation": {
                ch.value: round(amt, 2) for ch, amt in allocations.items()
            },
            "current_roas": round(campaign.overall_roas, 4),
            "total_conversions": campaign.total_conversions,
        }

        logger.info("Optimization complete for '%s'", campaign.name)
        return results

    def get_report(self, campaign: Campaign) -> dict[str, Any]:
        """Generate a performance report for a campaign.

        Args:
            campaign: The campaign to report on.

        Returns:
            Report data dictionary.
        """
        channel_reports = {}
        for ch, perf in campaign.performance.items():
            channel_reports[ch.value] = {
                "impressions": perf.impressions,
                "clicks": perf.clicks,
                "conversions": perf.conversions,
                "spend": round(perf.spend, 2),
                "revenue": round(perf.revenue, 2),
                "ctr": round(perf.ctr, 4),
                "cpc": round(perf.cpc, 2),
                "roas": round(perf.roas, 4),
                "conversion_rate": round(perf.conversion_rate, 4),
            }

        return {
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "budget": campaign.budget,
            "total_spend": round(campaign.total_spend, 2),
            "total_revenue": round(campaign.total_revenue, 2),
            "total_conversions": campaign.total_conversions,
            "overall_roas": round(campaign.overall_roas, 4),
            "remaining_budget": round(campaign.remaining_budget, 2),
            "channels": channel_reports,
            "generated_at": datetime.now().isoformat(),
        }


def main() -> None:
    """Run the basic campaign optimization example."""
    logger.info("=" * 60)
    logger.info("Basic Campaign Optimization Example")
    logger.info("=" * 60)

    # Create optimizer
    optimizer = CampaignOptimizer(min_channel_budget=500.0)

    # Create a campaign
    campaign = optimizer.create_campaign(
        name="Summer Sale 2026",
        budget=10000.0,
        channels=[ChannelType.SEARCH, ChannelType.SOCIAL, ChannelType.DISPLAY],
        duration_days=30,
    )
    campaign.status = CampaignStatus.ACTIVE

    # Allocate budget
    allocation = optimizer.allocate_budget(campaign)
    logger.info("Initial budget allocation:")
    for ch, amount in allocation.items():
        logger.info("  %s: $%.2f", ch.value, amount)

    # Simulate performance data
    campaign.performance[ChannelType.SEARCH].spend = 3500.0
    campaign.performance[ChannelType.SEARCH].impressions = 50000
    campaign.performance[ChannelType.SEARCH].clicks = 1200
    campaign.performance[ChannelType.SEARCH].conversions = 45
    campaign.performance[ChannelType.SEARCH].revenue = 6750.0

    campaign.performance[ChannelType.SOCIAL].spend = 3000.0
    campaign.performance[ChannelType.SOCIAL].impressions = 80000
    campaign.performance[ChannelType.SOCIAL].clicks = 900
    campaign.performance[ChannelType.SOCIAL].conversions = 25
    campaign.performance[ChannelType.SOCIAL].revenue = 3750.0

    campaign.performance[ChannelType.DISPLAY].spend = 2500.0
    campaign.performance[ChannelType.DISPLAY].impressions = 120000
    campaign.performance[ChannelType.DISPLAY].clicks = 600
    campaign.performance[ChannelType.DISPLAY].conversions = 15
    campaign.performance[ChannelType.DISPLAY].revenue = 1800.0

    # Run optimization
    logger.info("\nRunning optimization...")
    results = optimizer.optimize(campaign)
    logger.info("Optimization results:")
    logger.info("  Scores: %s", results["scores"])
    logger.info("  Recommended allocation: %s", results["recommended_allocation"])
    logger.info("  Current ROAS: %.2f", results["current_roas"])

    # Generate report
    logger.info("\nCampaign Report:")
    report = optimizer.get_report(campaign)
    logger.info("  Total Spend: $%.2f", report["total_spend"])
    logger.info("  Total Revenue: $%.2f", report["total_revenue"])
    logger.info("  Total Conversions: %d", report["total_conversions"])
    logger.info("  Overall ROAS: %.2f", report["overall_roas"])
    logger.info("  Remaining Budget: $%.2f", report["remaining_budget"])

    logger.info("\n" + "=" * 60)
    logger.info("Example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
