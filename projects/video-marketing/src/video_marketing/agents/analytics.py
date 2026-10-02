"""Analytics Agent.

Tracks and analyzes video performance across platforms including
views, engagement, retention, and audience insights.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(StrEnum):
    """Types of analytics metrics."""

    VIEWS = "views"
    WATCH_TIME = "watch_time"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    SUBSCRIBERS = "subscribers"
    CLICK_THROUGH_RATE = "click_through_rate"
    AVERAGE_VIEW_DURATION = "average_view_duration"
    RETENTION = "retention"
    ENGAGEMENT_RATE = "engagement_rate"
    IMPRESSIONS = "impressions"
    REVENUE = "revenue"


class TimeRange(StrEnum):
    """Analytics time ranges."""

    LAST_7_DAYS = "7d"
    LAST_28_DAYS = "28d"
    LAST_90_DAYS = "90d"
    LAST_365_DAYS = "365d"
    ALL_TIME = "all"
    CUSTOM = "custom"


@dataclass
class MetricDataPoint:
    """A single metric data point."""

    timestamp: datetime
    value: float
    metric_type: MetricType
    platform: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoAnalytics:
    """Analytics data for a single video."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    platform: str = ""
    date: datetime = field(default_factory=lambda: datetime.now(UTC))
    views: int = 0
    watch_time_minutes: float = 0.0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    impressions: int = 0
    click_through_rate: float = 0.0
    average_view_duration_seconds: float = 0.0
    retention_curve: list[float] = field(default_factory=list)
    revenue: float = 0.0
    demographics: dict[str, Any] = field(default_factory=dict)
    traffic_sources: dict[str, int] = field(default_factory=dict)
    devices: dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.views == 0:
            return 0.0
        total_engagements = self.likes + self.comments + self.shares
        return (total_engagements / self.views) * 100

    @property
    def average_view_percentage(self) -> float:
        """Calculate average view percentage (if video duration known)."""
        # This would need video duration; placeholder calculation
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "platform": self.platform,
            "date": self.date.isoformat(),
            "views": self.views,
            "watch_time_minutes": self.watch_time_minutes,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "comments": self.comments,
            "shares": self.shares,
            "subscribers_gained": self.subscribers_gained,
            "impressions": self.impressions,
            "click_through_rate": self.click_through_rate,
            "average_view_duration_seconds": self.average_view_duration_seconds,
            "engagement_rate": self.engagement_rate,
            "retention_curve": self.retention_curve,
            "revenue": self.revenue,
            "demographics": self.demographics,
            "traffic_sources": self.traffic_sources,
            "devices": self.devices,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class CampaignAnalytics:
    """Aggregated analytics for a campaign."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str = ""
    video_ids: list[str] = field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    total_views: int = 0
    total_watch_time_hours: float = 0.0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_subscribers_gained: int = 0
    total_revenue: float = 0.0
    platform_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    daily_metrics: list[dict[str, Any]] = field(default_factory=list)
    top_performing_videos: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def overall_engagement_rate(self) -> float:
        """Calculate overall campaign engagement rate."""
        if self.total_views == 0:
            return 0.0
        total_engagements = self.total_likes + self.total_comments + self.total_shares
        return (total_engagements / self.total_views) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert campaign analytics to dictionary."""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "video_count": len(self.video_ids),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_views": self.total_views,
            "total_watch_time_hours": self.total_watch_time_hours,
            "total_likes": self.total_likes,
            "total_comments": self.total_comments,
            "total_shares": self.total_shares,
            "total_subscribers_gained": self.total_subscribers_gained,
            "total_revenue": self.total_revenue,
            "overall_engagement_rate": self.overall_engagement_rate,
            "platform_breakdown": self.platform_breakdown,
            "daily_metrics": self.daily_metrics,
            "top_performing_videos": self.top_performing_videos,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AnalyticsError(Exception):
    """Raised when an analytics operation fails."""

    def __init__(self, message: str, analytics_id: str | None = None) -> None:
        super().__init__(message)
        self.analytics_id = analytics_id


class AnalyticsAgent:
    """Agent responsible for tracking and analyzing video performance.

    Collects metrics from multiple platforms, aggregates data,
    and provides insights and reporting.
    """

    def __init__(self, storage_backend: Any | None = None) -> None:
        """Initialize the Analytics Agent.

        Args:
            storage_backend: Optional storage backend for persistence.
        """
        self._storage = storage_backend
        self._video_analytics: dict[str, VideoAnalytics] = {}
        self._campaign_analytics: dict[str, CampaignAnalytics] = {}
        self._metric_history: dict[str, list[MetricDataPoint]] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def record_video_analytics(self, analytics: VideoAnalytics) -> VideoAnalytics:
        """Record analytics for a video.

        Args:
            analytics: The video analytics data.

        Returns:
            The recorded VideoAnalytics.

        Raises:
            AnalyticsError: If recording fails.
        """
        if not analytics.video_id:
            raise AnalyticsError("Video ID is required")

        key = f"{analytics.video_id}:{analytics.platform}"
        self._video_analytics[key] = analytics
        self._logger.info(
            "Video analytics recorded",
            extra={
                "video_id": analytics.video_id,
                "platform": analytics.platform,
                "views": analytics.views,
            },
        )
        return analytics

    async def get_video_analytics(
        self,
        video_id: str,
        platform: str = "",
    ) -> VideoAnalytics:
        """Get analytics for a video.

        Args:
            video_id: The video ID.
            platform: Platform filter (empty for aggregate).

        Returns:
            VideoAnalytics object.

        Raises:
            AnalyticsError: If not found.
        """
        key = f"{video_id}:{platform}"
        if key not in self._video_analytics:
            raise AnalyticsError(
                f"Analytics not found for video '{video_id}' on platform '{platform}'",
                analytics_id=key,
            )
        return self._video_analytics[key]

    async def record_metric(
        self,
        video_id: str,
        metric_type: MetricType,
        value: float,
        platform: str = "",
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MetricDataPoint:
        """Record a single metric data point.

        Args:
            video_id: The video ID.
            metric_type: Type of metric.
            value: Metric value.
            platform: Platform source.
            timestamp: Metric timestamp (defaults to now).
            metadata: Additional metadata.

        Returns:
            The recorded MetricDataPoint.
        """
        point = MetricDataPoint(
            timestamp=timestamp or datetime.now(UTC),
            value=value,
            metric_type=metric_type,
            platform=platform,
            metadata=metadata or {},
        )

        key = f"{video_id}:{platform}"
        if key not in self._metric_history:
            self._metric_history[key] = []
        self._metric_history[key].append(point)

        self._logger.debug(
            "Metric recorded",
            extra={
                "video_id": video_id,
                "metric_type": metric_type.value,
                "value": value,
            },
        )
        return point

    async def get_metrics(
        self,
        video_id: str,
        metric_type: MetricType | None = None,
        platform: str = "",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[MetricDataPoint]:
        """Get metric history with optional filters.

        Args:
            video_id: The video ID.
            metric_type: Filter by metric type.
            platform: Filter by platform.
            start_date: Filter by start date.
            end_date: Filter by end date.

        Returns:
            List of MetricDataPoint objects.
        """
        key = f"{video_id}:{platform}"
        metrics = self._metric_history.get(key, [])

        if metric_type is not None:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        if start_date is not None:
            metrics = [m for m in metrics if m.timestamp >= start_date]
        if end_date is not None:
            metrics = [m for m in metrics if m.timestamp <= end_date]

        return sorted(metrics, key=lambda m: m.timestamp)

    async def aggregate_campaign(
        self,
        campaign_id: str,
        video_ids: list[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> CampaignAnalytics:
        """Aggregate analytics for a campaign.

        Args:
            campaign_id: The campaign ID.
            video_ids: List of video IDs in the campaign.
            start_date: Campaign start date.
            end_date: Campaign end date.

        Returns:
            Aggregated CampaignAnalytics.

        Raises:
            AnalyticsError: If aggregation fails.
        """
        if not video_ids:
            raise AnalyticsError("At least one video ID is required for campaign aggregation")

        campaign = CampaignAnalytics(
            campaign_id=campaign_id,
            video_ids=video_ids,
            start_date=start_date,
            end_date=end_date,
        )

        platform_stats: dict[str, dict[str, Any]] = {}

        for video_id in video_ids:
            for key, analytics in self._video_analytics.items():
                if not key.startswith(f"{video_id}:"):
                    continue

                platform = analytics.platform or "aggregate"
                campaign.total_views += analytics.views
                campaign.total_watch_time_hours += analytics.watch_time_minutes / 60
                campaign.total_likes += analytics.likes
                campaign.total_comments += analytics.comments
                campaign.total_shares += analytics.shares
                campaign.total_subscribers_gained += analytics.subscribers_gained
                campaign.total_revenue += analytics.revenue

                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "shares": 0,
                        "watch_time_hours": 0.0,
                    }

                platform_stats[platform]["views"] += analytics.views
                platform_stats[platform]["likes"] += analytics.likes
                platform_stats[platform]["comments"] += analytics.comments
                platform_stats[platform]["shares"] += analytics.shares
                platform_stats[platform]["watch_time_hours"] += analytics.watch_time_minutes / 60

        campaign.platform_breakdown = platform_stats
        self._campaign_analytics[campaign.id] = campaign

        self._logger.info(
            "Campaign analytics aggregated",
            extra={
                "campaign_id": campaign_id,
                "video_count": len(video_ids),
                "total_views": campaign.total_views,
            },
        )
        return campaign

    async def get_campaign_analytics(self, campaign_id: str) -> CampaignAnalytics:
        """Get analytics for a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            CampaignAnalytics object.

        Raises:
            AnalyticsError: If not found.
        """
        for analytics in self._campaign_analytics.values():
            if analytics.campaign_id == campaign_id:
                return analytics
        raise AnalyticsError(
            f"Campaign analytics not found for '{campaign_id}'",
            analytics_id=campaign_id,
        )

    async def generate_report(
        self,
        video_id: str,
        time_range: TimeRange = TimeRange.LAST_28_DAYS,
    ) -> dict[str, Any]:
        """Generate an analytics report for a video.

        Args:
            video_id: The video ID.
            time_range: Time range for the report.

        Returns:
            Report dictionary with metrics and insights.
        """
        self._logger.info(
            "Generating analytics report",
            extra={"video_id": video_id, "time_range": time_range.value},
        )

        # Gather all metrics for the video
        all_metrics: list[MetricDataPoint] = []
        for key, metrics in self._metric_history.items():
            if key.startswith(f"{video_id}:"):
                all_metrics.extend(metrics)

        # Calculate summary statistics
        views_metrics = [m for m in all_metrics if m.metric_type == MetricType.VIEWS]
        engagement_metrics = [
            m for m in all_metrics
            if m.metric_type in (MetricType.LIKES, MetricType.COMMENTS, MetricType.SHARES)
        ]

        total_views = sum(m.value for m in views_metrics)
        total_engagements = sum(m.value for m in engagement_metrics)

        report = {
            "video_id": video_id,
            "time_range": time_range.value,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_views": int(total_views),
                "total_engagements": int(total_engagements),
                "engagement_rate": (
                    total_engagements / total_views * 100
                ) if total_views > 0 else 0,
            },
            "metrics_by_type": {},
            "insights": [],
            "recommendations": [],
        }

        # Group metrics by type
        for metric_type in MetricType:
            type_metrics = [m for m in all_metrics if m.metric_type == metric_type]
            if type_metrics:
                report["metrics_by_type"][metric_type.value] = {
                    "count": len(type_metrics),
                    "total": sum(m.value for m in type_metrics),
                    "average": sum(m.value for m in type_metrics) / len(type_metrics),
                    "latest": type_metrics[-1].value if type_metrics else 0,
                }

        # Generate insights
        if total_views > 0:
            if report["summary"]["engagement_rate"] > 5:
                report["insights"].append("Above-average engagement rate")
                report["recommendations"].append("Consider creating similar content")
            elif report["summary"]["engagement_rate"] < 1:
                report["insights"].append("Below-average engagement rate")
                report["recommendations"].append("Review content strategy and audience targeting")

        return report

    async def compare_videos(
        self,
        video_ids: list[str],
        metric_type: MetricType = MetricType.VIEWS,
    ) -> dict[str, Any]:
        """Compare multiple videos on a specific metric.

        Args:
            video_ids: List of video IDs to compare.
            metric_type: Metric to compare.

        Returns:
            Comparison dictionary.
        """
        comparison: dict[str, Any] = {
            "metric": metric_type.value,
            "videos": [],
        }

        for video_id in video_ids:
            try:
                analytics = await self.get_video_analytics(video_id)
                value = getattr(analytics, metric_type.value, 0)
                comparison["videos"].append(
                    {
                        "video_id": video_id,
                        "value": value,
                        "platform": analytics.platform,
                    }
                )
            except AnalyticsError:
                comparison["videos"].append(
                    {
                        "video_id": video_id,
                        "value": 0,
                        "platform": "unknown",
                        "error": "Analytics not found",
                    }
                )

        # Sort by value descending
        comparison["videos"].sort(key=lambda v: v["value"], reverse=True)
        return comparison
