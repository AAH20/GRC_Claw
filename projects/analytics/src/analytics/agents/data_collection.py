"""Data Collection Agent - Fetches raw event and campaign data from multiple sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class DataSource(StrEnum):
    """Supported data sources."""

    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"
    AMPLITUDE = "amplitude"


@dataclass
class RawEvent:
    """Represents a raw marketing event from any source."""

    event_id: str
    source: DataSource
    event_type: str
    timestamp: datetime
    user_id: str
    campaign_id: str | None = None
    channel: str | None = None
    revenue: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionResult:
    """Result of a data collection run."""

    source: DataSource
    events: list[RawEvent]
    collected_at: datetime
    total_count: int
    success: bool
    error_message: str | None = None


class BaseDataCollector(ABC):
    """Abstract base class for data collectors."""

    def __init__(self, source: DataSource, timeout: int = 60) -> None:
        self.source = source
        self.timeout = timeout
        self.logger = logger.bind(agent="data_collection", source=source.value)

    @abstractmethod
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> CollectionResult:
        """Collect events from the data source."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is reachable."""
        ...


class GoogleAnalyticsCollector(BaseDataCollector):
    """Collector for Google Analytics 4 data."""

    def __init__(self, property_id: str, credentials_path: str, timeout: int = 60) -> None:
        super().__init__(DataSource.GOOGLE_ANALYTICS, timeout)
        self.property_id = property_id
        self.credentials_path = credentials_path
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url="https://analyticsdata.googleapis.com",
                timeout=self.timeout,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> CollectionResult:
        """Collect events from Google Analytics 4."""
        self.logger.info(
            "collecting_ga_data",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        try:
            client = await self._get_client()
            # In production, this would use the GA4 Data API with proper auth
            response = await client.post(
                f"/v1beta/properties/{self.property_id}:runReport",
                json={
                    "dateRanges": [
                        {
                            "startDate": start_date.strftime("%Y-%m-%d"),
                            "endDate": end_date.strftime("%Y-%m-%d"),
                        }
                    ],
                    "dimensions": [{"name": "eventName"}, {"name": "campaign"}],
                    "metrics": [{"name": "eventCount"}, {"name": "totalRevenue"}],
                },
            )
            response.raise_for_status()
            data = response.json()

            events: list[RawEvent] = []
            for row in data.get("rows", []):
                events.append(
                    RawEvent(
                        event_id=f"ga_{row.get('dimensionValues', [{}])[0].get('value', '')}",
                        source=DataSource.GOOGLE_ANALYTICS,
                        event_type=row.get("dimensionValues", [{}])[0].get("value", "unknown"),
                        timestamp=datetime.utcnow(),
                        user_id=row.get("dimensionValues", [{}])[1].get("value", "anonymous"),
                        campaign_id=row.get("dimensionValues", [{}])[1].get("value"),
                        revenue=float(row.get("metricValues", [{}])[1].get("value", 0)),
                    )
                )

            return CollectionResult(
                source=DataSource.GOOGLE_ANALYTICS,
                events=events,
                collected_at=datetime.utcnow(),
                total_count=len(events),
                success=True,
            )
        except Exception as exc:
            self.logger.error("ga_collection_failed", error=str(exc))
            return CollectionResult(
                source=DataSource.GOOGLE_ANALYTICS,
                events=[],
                collected_at=datetime.utcnow(),
                total_count=0,
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check GA API connectivity."""
        try:
            client = await self._get_client()
            response = await client.get("/v1beta/properties")
            return response.status_code == 200
        except Exception:
            return False


class MixpanelCollector(BaseDataCollector):
    """Collector for Mixpanel event data."""

    def __init__(self, project_id: str, api_secret: str, timeout: int = 60) -> None:
        super().__init__(DataSource.MIXPANEL, timeout)
        self.project_id = project_id
        self.api_secret = api_secret
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url="https://api.mixpanel.com",
                timeout=self.timeout,
                auth=(self.api_secret, ""),
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> CollectionResult:
        """Collect events from Mixpanel."""
        self.logger.info(
            "collecting_mixpanel_data",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        try:
            client = await self._get_client()
            response = await client.get(
                "/api/2.0/export",
                params={
                    "from_date": start_date.strftime("%Y-%m-%d"),
                    "to_date": end_date.strftime("%Y-%m-%d"),
                    "event": kwargs.get("event", ""),
                },
            )
            response.raise_for_status()

            events: list[RawEvent] = []
            for line in response.text.strip().split("\n"):
                if not line:
                    continue
                import json

                data = json.loads(line)
                props = data.get("properties", {})
                events.append(
                    RawEvent(
                        event_id=data.get("event", ""),
                        source=DataSource.MIXPANEL,
                        event_type=data.get("event", "unknown"),
                        timestamp=datetime.fromtimestamp(props.get("time", 0)),
                        user_id=props.get("distinct_id", "anonymous"),
                        campaign_id=props.get("campaign_id"),
                        channel=props.get("channel"),
                        revenue=props.get("revenue", 0.0),
                        metadata=props,
                    )
                )

            return CollectionResult(
                source=DataSource.MIXPANEL,
                events=events,
                collected_at=datetime.utcnow(),
                total_count=len(events),
                success=True,
            )
        except Exception as exc:
            self.logger.error("mixpanel_collection_failed", error=str(exc))
            return CollectionResult(
                source=DataSource.MIXPANEL,
                events=[],
                collected_at=datetime.utcnow(),
                total_count=0,
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check Mixpanel API connectivity."""
        try:
            client = await self._get_client()
            response = await client.get("/api/2.0/engage")
            return response.status_code == 200
        except Exception:
            return False


class AmplitudeCollector(BaseDataCollector):
    """Collector for Amplitude event data."""

    def __init__(self, api_key: str, timeout: int = 60) -> None:
        super().__init__(DataSource.AMPLITUDE, timeout)
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url="https://api2.amplitude.com",
                timeout=self.timeout,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> CollectionResult:
        """Collect events from Amplitude."""
        self.logger.info(
            "collecting_amplitude_data",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/2/timeline",
                params={"api_key": self.api_key},
                json={
                    "start": start_date.strftime("%Y%m%d"),
                    "end": end_date.strftime("%Y%m%d"),
                },
            )
            response.raise_for_status()
            data = response.json()

            events: list[RawEvent] = []
            for event_data in data.get("events", []):
                events.append(
                    RawEvent(
                        event_id=event_data.get("event_id", ""),
                        source=DataSource.AMPLITUDE,
                        event_type=event_data.get("event_type", "unknown"),
                        timestamp=datetime.fromtimestamp(event_data.get("time", 0) / 1000),
                        user_id=event_data.get("user_id", "anonymous"),
                        campaign_id=event_data.get("campaign_id"),
                        channel=event_data.get("channel"),
                        revenue=event_data.get("revenue", 0.0),
                        metadata=event_data.get("event_properties", {}),
                    )
                )

            return CollectionResult(
                source=DataSource.AMPLITUDE,
                events=events,
                collected_at=datetime.utcnow(),
                total_count=len(events),
                success=True,
            )
        except Exception as exc:
            self.logger.error("amplitude_collection_failed", error=str(exc))
            return CollectionResult(
                source=DataSource.AMPLITUDE,
                events=[],
                collected_at=datetime.utcnow(),
                total_count=0,
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check Amplitude API connectivity."""
        try:
            client = await self._get_client()
            response = await client.get("/api/2/timeline", params={"api_key": self.api_key})
            return response.status_code == 200
        except Exception:
            return False


class DataCollectionAgent:
    """Orchestrates data collection from all configured sources."""

    def __init__(self) -> None:
        self.collectors: dict[DataSource, BaseDataCollector] = {}
        self.logger = logger.bind(agent="data_collection")

    def register_collector(self, collector: BaseDataCollector) -> None:
        """Register a data collector for a specific source."""
        self.collectors[collector.source] = collector
        self.logger.info("collector_registered", source=collector.source.value)

    async def collect_all(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        lookback_days: int = 30,
    ) -> list[CollectionResult]:
        """Collect data from all registered sources."""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=lookback_days)

        self.logger.info(
            "starting_collection",
            sources=[s.value for s in self.collectors],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        results: list[CollectionResult] = []
        for source, collector in self.collectors.items():
            try:
                result = await collector.collect(start_date, end_date)
                results.append(result)
                self.logger.info(
                    "collection_complete",
                    source=source.value,
                    count=result.total_count,
                    success=result.success,
                )
            except Exception as exc:
                self.logger.error("collection_failed", source=source.value, error=str(exc))
                results.append(
                    CollectionResult(
                        source=source,
                        events=[],
                        collected_at=datetime.utcnow(),
                        total_count=0,
                        success=False,
                        error_message=str(exc),
                    )
                )

        return results

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all registered collectors."""
        results: dict[str, bool] = {}
        for source, collector in self.collectors.items():
            try:
                results[source.value] = await collector.health_check()
            except Exception:
                results[source.value] = False
        return results
