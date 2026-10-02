"""Analytics agent for marketing performance analysis and reporting."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ReportPeriod(StrEnum):
    """Supported report periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MetricType(StrEnum):
    """Supported metric types."""

    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    CTR = "ctr"
    ROAS = "roas"
    ENGAGEMENT_RATE = "engagement_rate"


class ChannelMetrics(BaseModel):
    """Metrics for a single marketing channel.

    Attributes:
        channel: Marketing channel name.
        impressions: Total impressions.
        clicks: Total clicks.
        conversions: Total conversions.
        spend: Total spend in USD.
        revenue: Attributed revenue in USD.
    """

    channel: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0

    @property
    def ctr(self) -> float:
        """Calculate click-through rate."""
        if self.impressions == 0:
            return 0.0
        return round(self.clicks / self.impressions * 100, 2)

    @property
    def roas(self) -> float:
        """Calculate return on ad spend."""
        if self.spend == 0:
            return 0.0
        return round(self.revenue / self.spend, 2)

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.impressions == 0:
            return 0.0
        return round(self.clicks / self.impressions * 100, 2)


class AnalyticsReport(BaseModel):
    """Complete analytics report.

    Attributes:
        period: Report period.
        start_date: Report start date.
        end_date: Report end date.
        channel_metrics: Per-channel metrics.
        total_impressions: Total impressions across channels.
        total_clicks: Total clicks across channels.
        total_conversions: Total conversions across channels.
        total_spend: Total spend across channels.
        total_revenue: Total revenue across channels.
        insights: AI-generated insights.
    """

    period: ReportPeriod
    start_date: datetime
    end_date: datetime
    channel_metrics: list[ChannelMetrics] = Field(default_factory=list)
    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_spend: float = 0.0
    total_revenue: float = 0.0
    insights: list[str] = Field(default_factory=list)


class AnalyticsAgent:
    """AI agent for marketing analytics and reporting.

    Aggregates performance data across channels, calculates KPIs,
    generates insights, and produces actionable reports.
    """

    def __init__(
        self,
        meta_client: Any | None = None,
        google_ads_client: Any | None = None,
        mailchimp_client: Any | None = None,
        llm_client: Any | None = None,
    ) -> None:
        """Initialize the AnalyticsAgent.

        Args:
            meta_client: Optional Meta API client.
            google_ads_client: Optional Google Ads API client.
            mailchimp_client: Optional Mailchimp API client.
            llm_client: Optional LLM client for insight generation.
        """
        self._meta_client = meta_client
        self._google_ads_client = google_ads_client
        self._mailchimp_client = mailchimp_client
        self._llm_client = llm_client
        self._logger = logger.bind(agent="analytics")

    async def generate_report(
        self,
        period: ReportPeriod,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AnalyticsReport:
        """Generate an analytics report for the specified period.

        Args:
            period: Report period (daily, weekly, monthly).
            start_date: Report start date. Defaults to period start.
            end_date: Report end date. Defaults to now.

        Returns:
            Complete analytics report.
        """
        end_date = end_date or datetime.utcnow()
        start_date = start_date or self._default_start_date(period, end_date)

        self._logger.info(
            "Generating analytics report",
            period=period.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        channel_metrics = await self._collect_metrics(start_date, end_date)

        report = AnalyticsReport(
            period=period,
            start_date=start_date,
            end_date=end_date,
            channel_metrics=channel_metrics,
            total_impressions=sum(m.impressions for m in channel_metrics),
            total_clicks=sum(m.clicks for m in channel_metrics),
            total_conversions=sum(m.conversions for m in channel_metrics),
            total_spend=sum(m.spend for m in channel_metrics),
            total_revenue=sum(m.revenue for m in channel_metrics),
            insights=self._generate_insights(channel_metrics),
        )

        self._logger.info("Analytics report generated", period=period.value)
        return report

    async def _collect_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[ChannelMetrics]:
        """Collect metrics from all integrated channels.

        Args:
            start_date: Start of the reporting period.
            end_date: End of the reporting period.

        Returns:
            List of per-channel metrics.
        """
        metrics: list[ChannelMetrics] = []

        # Collect from Meta
        if self._meta_client:
            try:
                meta_metrics = await self._meta_client.get_metrics(start_date, end_date)
                metrics.append(
                    ChannelMetrics(
                        channel="meta",
                        impressions=meta_metrics.get("impressions", 0),
                        clicks=meta_metrics.get("clicks", 0),
                        conversions=meta_metrics.get("conversions", 0),
                        spend=meta_metrics.get("spend", 0.0),
                        revenue=meta_metrics.get("revenue", 0.0),
                    )
                )
            except Exception as exc:
                self._logger.warning("Failed to collect Meta metrics", error=str(exc))

        # Collect from Google Ads
        if self._google_ads_client:
            try:
                google_metrics = await self._google_ads_client.get_metrics(
                    start_date, end_date
                )
                metrics.append(
                    ChannelMetrics(
                        channel="google_ads",
                        impressions=google_metrics.get("impressions", 0),
                        clicks=google_metrics.get("clicks", 0),
                        conversions=google_metrics.get("conversions", 0),
                        spend=google_metrics.get("spend", 0.0),
                        revenue=google_metrics.get("revenue", 0.0),
                    )
                )
            except Exception as exc:
                self._logger.warning(
                    "Failed to collect Google Ads metrics", error=str(exc)
                )

        # Collect from Mailchimp
        if self._mailchimp_client:
            try:
                mailchimp_metrics = await self._mailchimp_client.get_metrics(
                    start_date, end_date
                )
                metrics.append(
                    ChannelMetrics(
                        channel="mailchimp",
                        impressions=mailchimp_metrics.get("sent", 0),
                        clicks=mailchimp_metrics.get("clicks", 0),
                        conversions=mailchimp_metrics.get("conversions", 0),
                        spend=mailchimp_metrics.get("spend", 0.0),
                        revenue=mailchimp_metrics.get("revenue", 0.0),
                    )
                )
            except Exception as exc:
                self._logger.warning(
                    "Failed to collect Mailchimp metrics", error=str(exc)
                )

        return metrics

    def _generate_insights(self, metrics: list[ChannelMetrics]) -> list[str]:
        """Generate actionable insights from metrics.

        Args:
            metrics: Per-channel metrics.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        if not metrics:
            return ["No data available for analysis."]

        # Find best performing channel
        best_channel = max(metrics, key=lambda m: m.roas, default=None)
        if best_channel and best_channel.roas > 0:
            insights.append(
                f"{best_channel.channel} has the highest ROAS at {best_channel.roas}x. "
                f"Consider increasing budget allocation."
            )

        # CTR analysis
        avg_ctr = sum(m.ctr for m in metrics) / len(metrics) if metrics else 0
        if avg_ctr < 1.0:
            insights.append(
                f"Average CTR is {avg_ctr:.2f}%, below the 1% benchmark. "
                f"Review ad creative and targeting."
            )

        # Conversion analysis
        total_conversions = sum(m.conversions for m in metrics)
        if total_conversions == 0:
            insights.append(
                "No conversions recorded. Verify conversion tracking is properly configured."
            )

        return insights

    def _default_start_date(
        self,
        period: ReportPeriod,
        end_date: datetime,
    ) -> datetime:
        """Calculate default start date based on period.

        Args:
            period: Report period.
            end_date: Report end date.

        Returns:
            Calculated start date.
        """
        if period == ReportPeriod.DAILY:
            return end_date - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            return end_date - timedelta(weeks=1)
        else:  # MONTHLY
            return end_date - timedelta(days=30)
