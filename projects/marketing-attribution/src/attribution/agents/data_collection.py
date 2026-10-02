"""Data Collection Agent - Fetches marketing data from ad platforms and analytics tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class DataSource(str, Enum):
    """Supported data sources."""

    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"
    GOOGLE_ANALYTICS = "google_analytics"


@dataclass
class RawDataPoint:
    """A single raw data point from any source."""

    source: DataSource
    timestamp: datetime
    campaign_id: str
    campaign_name: str
    ad_group_id: str | None = None
    ad_id: str | None = None
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: float = 0.0
    revenue: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionResult:
    """Result of a data collection run."""

    source: DataSource
    data_points: list[RawDataPoint]
    collected_at: datetime
    success: bool
    error_message: str | None = None


class BaseDataCollector(ABC):
    """Abstract base class for data collectors."""

    def __init__(self, source: DataSource, timeout: int = 30) -> None:
        self.source = source
        self.timeout = timeout
        self.logger = logger.bind(source=source.value)

    @abstractmethod
    async def collect(
        self, start_date: datetime, end_date: datetime
    ) -> CollectionResult:
        """Collect data for the given date range."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is accessible."""
        ...


class GoogleAdsCollector(BaseDataCollector):
    """Collector for Google Ads data."""

    BASE_URL = "https://googleads.googleapis.com/v14"

    def __init__(
        self,
        developer_token: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        login_customer_id: str,
        timeout: int = 30,
    ) -> None:
        super().__init__(DataSource.GOOGLE_ADS, timeout)
        self.developer_token = developer_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.login_customer_id = login_customer_id
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """Obtain OAuth2 access token."""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def collect(
        self, start_date: datetime, end_date: datetime
    ) -> CollectionResult:
        """Collect campaign data from Google Ads."""
        try:
            access_token = await self._get_access_token()
            data_points: list[RawDataPoint] = []

            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "developer-token": self.developer_token,
                    "login-customer-id": self.login_customer_id,
                },
            ) as client:
                query = f"""
                    SELECT
                        campaign.id,
                        campaign.name,
                        metrics.cost_micros,
                        metrics.impressions,
                        metrics.clicks,
                        metrics.conversions,
                        metrics.conversions_value
                    FROM campaign
                    WHERE segments.date BETWEEN '{start_date:%Y-%m-%d}' AND '{end_date:%Y-%m-%d}'
                """
                response = await client.post(
                    f"{self.BASE_URL}/customers/{self.login_customer_id}/googleAds:search",
                    json={"query": query},
                )
                response.raise_for_status()
                results = response.json().get("results", [])

                for row in results:
                    metrics = row.get("metrics", {})
                    campaign = row.get("campaign", {})
                    data_points.append(
                        RawDataPoint(
                            source=DataSource.GOOGLE_ADS,
                            timestamp=datetime.utcnow(),
                            campaign_id=campaign.get("id", ""),
                            campaign_name=campaign.get("name", ""),
                            spend=metrics.get("costMicros", 0) / 1_000_000,
                            impressions=metrics.get("impressions", 0),
                            clicks=metrics.get("clicks", 0),
                            conversions=metrics.get("conversions", 0),
                            revenue=metrics.get("conversionsValue", 0),
                        )
                    )

            return CollectionResult(
                source=DataSource.GOOGLE_ADS,
                data_points=data_points,
                collected_at=datetime.utcnow(),
                success=True,
            )
        except Exception as exc:
            self.logger.error("Failed to collect Google Ads data", error=str(exc))
            return CollectionResult(
                source=DataSource.GOOGLE_ADS,
                data_points=[],
                collected_at=datetime.utcnow(),
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check Google Ads API accessibility."""
        try:
            await self._get_access_token()
            return True
        except Exception:
            return False


class MetaAdsCollector(BaseDataCollector):
    """Collector for Meta (Facebook) Ads data."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        timeout: int = 30,
    ) -> None:
        super().__init__(DataSource.META_ADS, timeout)
        self.access_token = access_token
        self.ad_account_id = ad_account_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def collect(
        self, start_date: datetime, end_date: datetime
    ) -> CollectionResult:
        """Collect campaign data from Meta Ads."""
        try:
            data_points: list[RawDataPoint] = []

            async with httpx.AsyncClient(
                timeout=self.timeout,
                params={"access_token": self.access_token},
            ) as client:
                fields = "campaign_id,campaign_name,spend,impressions,clicks,actions,action_values"
                response = await client.get(
                    f"{self.BASE_URL}/act_{self.ad_account_id}/insights",
                    params={
                        "fields": fields,
                        "time_range": (
                            f"{{'since':'{start_date:%Y-%m-%d}',"
                            f"'until':'{end_date:%Y-%m-%d}'}}"
                        ),
                        "level": "campaign",
                    },
                )
                response.raise_for_status()
                data = response.json().get("data", [])

                for item in data:
                    conversions = 0.0
                    revenue = 0.0
                    for action in item.get("actions", []):
                        if action.get("action_type") in ("purchase", "lead", "conversion"):
                            conversions += float(action.get("value", 0))
                    for value in item.get("action_values", []):
                        if value.get("action_type") == "purchase":
                            revenue += float(value.get("value", 0))

                    data_points.append(
                        RawDataPoint(
                            source=DataSource.META_ADS,
                            timestamp=datetime.utcnow(),
                            campaign_id=item.get("campaign_id", ""),
                            campaign_name=item.get("campaign_name", ""),
                            spend=float(item.get("spend", 0)),
                            impressions=int(item.get("impressions", 0)),
                            clicks=int(item.get("clicks", 0)),
                            conversions=conversions,
                            revenue=revenue,
                        )
                    )

            return CollectionResult(
                source=DataSource.META_ADS,
                data_points=data_points,
                collected_at=datetime.utcnow(),
                success=True,
            )
        except Exception as exc:
            self.logger.error("Failed to collect Meta Ads data", error=str(exc))
            return CollectionResult(
                source=DataSource.META_ADS,
                data_points=[],
                collected_at=datetime.utcnow(),
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check Meta Ads API accessibility."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/act_{self.ad_account_id}",
                    params={"access_token": self.access_token, "fields": "id"},
                )
                return response.status_code == 200
        except Exception:
            return False


class GoogleAnalyticsCollector(BaseDataCollector):
    """Collector for Google Analytics 4 data."""

    BASE_URL = "https://analyticsdata.googleapis.com/v1beta"

    def __init__(self, property_id: str, credentials_path: str, timeout: int = 30) -> None:
        super().__init__(DataSource.GOOGLE_ANALYTICS, timeout)
        self.property_id = property_id
        self.credentials_path = credentials_path

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def collect(
        self, start_date: datetime, end_date: datetime
    ) -> CollectionResult:
        """Collect conversion data from Google Analytics 4."""
        try:
            data_points: list[RawDataPoint] = []

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.BASE_URL}/properties/{self.property_id}:runReport",
                    json={
                        "dateRanges": [
                            {
                                "startDate": start_date.strftime("%Y-%m-%d"),
                                "endDate": end_date.strftime("%Y-%m-%d"),
                            }
                        ],
                        "dimensions": [
                            {"name": "campaign"},
                            {"name": "sessionSource"},
                        ],
                        "metrics": [
                            {"name": "sessions"},
                            {"name": "conversions"},
                            {"name": "totalAdRevenue"},
                        ],
                    },
                )
                response.raise_for_status()
                rows = response.json().get("rows", [])

                for row in rows:
                    dimensions = row.get("dimensionValues", [])
                    metrics = row.get("metricValues", [])
                    data_points.append(
                        RawDataPoint(
                            source=DataSource.GOOGLE_ANALYTICS,
                            timestamp=datetime.utcnow(),
                            campaign_id=dimensions[0].get("value", "") if dimensions else "",
                            campaign_name=dimensions[0].get("value", "") if dimensions else "",
                            conversions=(
                                float(metrics[1].get("value", 0))
                                if len(metrics) > 1
                                else 0
                            ),
                            revenue=float(metrics[2].get("value", 0)) if len(metrics) > 2 else 0,
                            metadata={
                                "sessions": int(metrics[0].get("value", 0)) if metrics else 0,
                                "source": (
                                    dimensions[1].get("value", "")
                                    if len(dimensions) > 1
                                    else ""
                                ),
                            },
                        )
                    )

            return CollectionResult(
                source=DataSource.GOOGLE_ANALYTICS,
                data_points=data_points,
                collected_at=datetime.utcnow(),
                success=True,
            )
        except Exception as exc:
            self.logger.error("Failed to collect Google Analytics data", error=str(exc))
            return CollectionResult(
                source=DataSource.GOOGLE_ANALYTICS,
                data_points=[],
                collected_at=datetime.utcnow(),
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check Google Analytics API accessibility."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/properties/{self.propertyId}:runReport"
                )
                return response.status_code < 500
        except Exception:
            return False


class DataCollectionAgent:
    """Orchestrates data collection from all configured sources."""

    def __init__(self) -> None:
        self.collectors: dict[DataSource, BaseDataCollector] = {}
        self.logger = logger.bind(agent="data_collection")

    def register_collector(
        self, source: DataSource, collector: BaseDataCollector
    ) -> None:
        """Register a data collector for a source."""
        self.collectors[source] = collector
        self.logger.info("Registered collector", source=source.value)

    async def collect_all(
        self, start_date: datetime, end_date: datetime
    ) -> list[CollectionResult]:
        """Collect data from all registered sources concurrently."""
        import asyncio

        tasks = [
            collector.collect(start_date, end_date)
            for collector in self.collectors.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        collection_results: list[CollectionResult] = []
        for source, result in zip(self.collectors.keys(), results, strict=False):
            if isinstance(result, Exception):
                self.logger.error(
                    "Collection failed", source=source.value, error=str(result)
                )
                collection_results.append(
                    CollectionResult(
                        source=source,
                        data_points=[],
                        collected_at=datetime.utcnow(),
                        success=False,
                        error_message=str(result),
                    )
                )
            else:
                collection_results.append(result)

        return collection_results

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all registered collectors."""
        import asyncio

        tasks = {
            source: collector.health_check()
            for source, collector in self.collectors.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {
            source.value: result is True
            for source, result in zip(tasks.keys(), results, strict=False)
        }
