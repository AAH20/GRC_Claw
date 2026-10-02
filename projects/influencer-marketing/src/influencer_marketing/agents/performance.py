"""Performance agent for tracking campaign metrics and ROI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.content import ContentPiece, ContentStatus

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a content piece or campaign."""

    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    engagement_rate: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    roas: float = 0.0
    cpm: float = 0.0
    collected_at: datetime | None = None


@dataclass
class PerformanceReport:
    """Aggregated performance report."""

    campaign_id: str
    influencer_id: str | None = None
    content_id: str | None = None
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    period_start: datetime | None = None
    period_end: datetime | None = None
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    benchmark_comparison: dict[str, float] = field(default_factory=dict)


class PerformanceAgent(BaseAgent[ContentPiece, PerformanceReport]):
    """Agent responsible for tracking campaign metrics and ROI."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="performance",
            description="Tracks campaign metrics, ROI, and engagement analytics",
            max_retries=3,
            timeout_seconds=120,
        )
        super().__init__(config)

    async def validate_input(self, input_data: ContentPiece) -> bool:
        """Validate performance tracking input."""
        if input_data.status != ContentStatus.PUBLISHED:
            self.logger.warning("Content not published yet")
            return False
        if not input_data.published_url:
            self.logger.warning("No published URL available")
            return False
        return True

    async def execute(self, input_data: ContentPiece) -> AgentResult[PerformanceReport]:
        """Execute performance tracking for a content piece."""
        self.logger.info(
            "Starting performance tracking",
            content_id=input_data.id,
            influencer_id=input_data.influencer_id,
        )

        try:
            # Collect metrics from platform APIs
            metrics = await self._collect_metrics(input_data)

            # Calculate derived metrics
            metrics = self._calculate_derived_metrics(metrics)

            # Generate insights
            insights = self._generate_insights(metrics)
            recommendations = self._generate_recommendations(metrics)

            report = PerformanceReport(
                campaign_id=input_data.campaign_id,
                influencer_id=input_data.influencer_id,
                content_id=input_data.id,
                metrics=metrics,
                period_start=input_data.published_at,
                period_end=datetime.utcnow(),
                insights=insights,
                recommendations=recommendations,
            )

            self.logger.info(
                "Performance tracking completed",
                content_id=input_data.id,
                roas=metrics.roas,
            )
            return AgentResult(success=True, data=report)

        except Exception as exc:
            self.logger.error("Performance tracking failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    async def _collect_metrics(self, content: ContentPiece) -> PerformanceMetrics:
        """Collect metrics from platform APIs."""
        # Placeholder: In production, this would call Instagram Graph API,
        # TikTok API, YouTube Data API to get actual metrics
        return PerformanceMetrics(
            impressions=0,
            reach=0,
            likes=0,
            comments=0,
            shares=0,
            saves=0,
            clicks=0,
            conversions=0,
            spend=0.0,
            revenue=0.0,
            collected_at=datetime.utcnow(),
        )

    def _calculate_derived_metrics(self, metrics: PerformanceMetrics) -> PerformanceMetrics:
        """Calculate derived metrics from raw data."""
        if metrics.impressions > 0:
            total_engagements = metrics.likes + metrics.comments + metrics.shares + metrics.saves
            metrics.engagement_rate = total_engagements / metrics.impressions
            metrics.ctr = metrics.clicks / metrics.impressions
            metrics.cpm = (metrics.spend / metrics.impressions) * 1000

        if metrics.clicks > 0:
            metrics.cpc = metrics.spend / metrics.clicks

        if metrics.spend > 0:
            metrics.roas = metrics.revenue / metrics.spend

        return metrics

    def _generate_insights(self, metrics: PerformanceMetrics) -> list[str]:
        """Generate insights from performance metrics."""
        insights: list[str] = []
        if metrics.engagement_rate > 0.05:
            insights.append("Above-average engagement rate")
        elif metrics.engagement_rate < 0.01:
            insights.append("Below-average engagement rate - consider content optimization")
        if metrics.roas > 3.0:
            insights.append("Strong ROAS - consider increasing budget")
        elif metrics.roas < 1.0:
            insights.append("Negative ROAS - review targeting and content strategy")
        return insights

    def _generate_recommendations(self, metrics: PerformanceMetrics) -> list[str]:
        """Generate optimization recommendations."""
        recs: list[str] = []
        if metrics.ctr < 0.01:
            recs.append("Improve call-to-action in content")
        if metrics.engagement_rate < 0.02:
            recs.append("Test different content formats or posting times")
        if metrics.roas < 2.0:
            recs.append("Review audience targeting and creative approach")
        return recs
