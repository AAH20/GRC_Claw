"""Analytics client for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import APIClient
from .types import AnalyticsQuery, AnalyticsReport


class AnalyticsClient:
    """Client for accessing marketing analytics."""

    def __init__(self, api_client: APIClient) -> None:
        """Initialize the analytics client.

        Args:
            api_client: The low-level API client.
        """
        self._client = api_client

    def get_report(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsReport:
        """Get an analytics report.

        Args:
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).
            metrics: List of metrics to include.
            dimensions: List of dimensions to group by.
            filters: Additional filters.

        Returns:
            The analytics report.
        """
        payload: Dict[str, Any] = {}
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if metrics:
            payload["metrics"] = metrics
        if dimensions:
            payload["dimensions"] = dimensions
        if filters:
            payload["filters"] = filters

        response = self._client.post("/analytics/report", json=payload)
        return AnalyticsReport.from_dict(response["data"])

    def get_campaign_performance(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        campaign_ids: Optional[List[str]] = None,
    ) -> AnalyticsReport:
        """Get campaign performance metrics.

        Args:
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).
            campaign_ids: Optional list of campaign IDs to filter by.

        Returns:
            The campaign performance report.
        """
        payload: Dict[str, Any] = {
            "metrics": ["impressions", "clicks", "conversions", "spend", "revenue"],
            "dimensions": ["campaign_id", "campaign_name"],
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if campaign_ids:
            payload["filters"] = {"campaign_id": campaign_ids}

        response = self._client.post("/analytics/campaigns", json=payload)
        return AnalyticsReport.from_dict(response["data"])

    def get_lead_funnel(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AnalyticsReport:
        """Get lead funnel analytics.

        Args:
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).

        Returns:
            The lead funnel report.
        """
        payload: Dict[str, Any] = {
            "metrics": ["total_leads", "qualified_leads", "converted_leads", "conversion_rate"],
            "dimensions": ["stage"],
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        response = self._client.post("/analytics/lead-funnel", json=payload)
        return AnalyticsReport.from_dict(response["data"])

    def get_channel_performance(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AnalyticsReport:
        """Get performance metrics broken down by channel.

        Args:
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).

        Returns:
            The channel performance report.
        """
        payload: Dict[str, Any] = {
            "metrics": ["impressions", "clicks", "conversions", "spend", "revenue", "roas"],
            "dimensions": ["channel"],
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        response = self._client.post("/analytics/channels", json=payload)
        return AnalyticsReport.from_dict(response["data"])

    def get_journey_analytics(
        self,
        journey_id: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AnalyticsReport:
        """Get analytics for a specific journey.

        Args:
            journey_id: The journey ID.
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).

        Returns:
            The journey analytics report.
        """
        payload: Dict[str, Any] = {
            "metrics": ["enrollments", "completions", "drop_offs", "conversion_rate"],
            "dimensions": ["step"],
            "filters": {"journey_id": journey_id},
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        response = self._client.post("/analytics/journeys", json=payload)
        return AnalyticsReport.from_dict(response["data"])
