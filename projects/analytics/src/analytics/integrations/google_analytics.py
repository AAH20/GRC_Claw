"""Google Analytics 4 integration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


@dataclass
class GAConfig:
    """Configuration for Google Analytics integration."""

    property_id: str
    credentials_path: str
    api_version: str = "v1beta"
    batch_size: int = 10000
    timeout: int = 60


@dataclass
class GAMetric:
    """A single GA metric value."""

    name: str
    value: float
    dimensions: dict[str, str]


@dataclass
class GAResponse:
    """Response from a GA API call."""

    metrics: list[GAMetric]
    row_count: int
    success: bool
    error_message: str | None = None


class GoogleAnalyticsClient:
    """Client for Google Analytics 4 Data API."""

    def __init__(self, config: GAConfig) -> None:
        self.config = config
        self.logger = logger.bind(integration="google_analytics")
        self._client: httpx.AsyncClient | None = None
        self._credentials: dict[str, Any] | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=f"https://analyticsdata.googleapis.com/{self.config.api_version}",
                timeout=self.config.timeout,
            )
        return self._client

    def _load_credentials(self) -> dict[str, Any]:
        """Load service account credentials from file."""
        if self._credentials is None:
            cred_path = Path(self.config.credentials_path)
            if not cred_path.exists():
                raise FileNotFoundError(
                    f"GA credentials file not found: {self.config.credentials_path}"
                )
            self._credentials = json.loads(cred_path.read_text())
        return self._credentials

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def run_report(
        self,
        start_date: str,
        end_date: str,
        dimensions: list[str] | None = None,
        metrics: list[str] | None = None,
    ) -> GAResponse:
        """Run a GA4 report query."""
        self.logger.info(
            "running_ga_report",
            property_id=self.config.property_id,
            start_date=start_date,
            end_date=end_date,
        )

        dimensions = dimensions or ["date", "sessionDefaultChannelGroup"]
        metrics = metrics or ["totalUsers", "sessions", "conversions", "totalRevenue"]

        payload = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": d} for d in dimensions],
            "metrics": [{"name": m} for m in metrics],
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"/properties/{self.config.property_id}:runReport",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            ga_metrics: list[GAMetric] = []
            for row in data.get("rows", []):
                dim_values = {
                    d["name"]: v.get("value", "")
                    for d, v in zip(
                        data.get("dimensionHeaders", []),
                        row.get("dimensionValues", []),
                        strict=False,
                    )
                }
                for metric_header, metric_value in zip(
                    data.get("metricHeaders", []),
                    row.get("metricValues", []),
                    strict=False,
                ):
                    ga_metrics.append(
                        GAMetric(
                            name=metric_header["name"],
                            value=float(metric_value.get("value", 0)),
                            dimensions=dim_values,
                        )
                    )

            return GAResponse(
                metrics=ga_metrics,
                row_count=len(data.get("rows", [])),
                success=True,
            )
        except Exception as exc:
            self.logger.error("ga_report_failed", error=str(exc))
            return GAResponse(
                metrics=[],
                row_count=0,
                success=False,
                error_message=str(exc),
            )

    async def get_realtime_report(
        self,
        dimensions: list[str] | None = None,
        metrics: list[str] | None = None,
    ) -> GAResponse:
        """Get real-time GA4 report."""
        dimensions = dimensions or ["minutesAgo"]
        metrics = metrics or ["activeUsers", "screenPageViews"]

        payload = {
            "dimensions": [{"name": d} for d in dimensions],
            "metrics": [{"name": m} for m in metrics],
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"/properties/{self.config.property_id}:runRealtimeReport",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            ga_metrics: list[GAMetric] = []
            for row in data.get("rows", []):
                dim_values = {
                    d["name"]: v.get("value", "")
                    for d, v in zip(
                        data.get("dimensionHeaders", []),
                        row.get("dimensionValues", []),
                        strict=False,
                    )
                }
                for metric_header, metric_value in zip(
                    data.get("metricHeaders", []),
                    row.get("metricValues", []),
                    strict=False,
                ):
                    ga_metrics.append(
                        GAMetric(
                            name=metric_header["name"],
                            value=float(metric_value.get("value", 0)),
                            dimensions=dim_values,
                        )
                    )

            return GAResponse(
                metrics=ga_metrics,
                row_count=len(data.get("rows", [])),
                success=True,
            )
        except Exception as exc:
            self.logger.error("ga_realtime_report_failed", error=str(exc))
            return GAResponse(
                metrics=[],
                row_count=0,
                success=False,
                error_message=str(exc),
            )

    async def health_check(self) -> bool:
        """Check if GA API is accessible."""
        try:
            client = await self._get_client()
            response = await client.get(f"/properties/{self.config.property_id}")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
