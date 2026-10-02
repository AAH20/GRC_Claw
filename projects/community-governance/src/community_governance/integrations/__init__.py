"""External service integrations for community governance."""

from __future__ import annotations

import httpx
from typing import Any

from community_governance.config.logging_config import get_logger

logger = get_logger(__name__)


class LangChainIntegration:
    """Integration with LangChain services for LLM-powered governance."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.langchain.com",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the LangChain integration.

        Args:
            api_key: LangChain API key.
            base_url: Base URL for LangChain API.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            The async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        return self._client

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the LangChain integration.

        Returns:
            Health status dictionary.
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return {
                "service": "langchain",
                "status": "healthy" if response.status_code == 200 else "degraded",
                "status_code": response.status_code,
            }
        except Exception as e:
            logger.warning(f"LangChain health check failed: {e}")
            return {
                "service": "langchain",
                "status": "unhealthy",
                "error": str(e),
            }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class NotificationIntegration:
    """Integration with notification services for governance alerts."""

    def __init__(
        self,
        webhook_url: str = "",
        api_key: str = "",
        timeout: float = 10.0,
    ) -> None:
        """Initialize the notification integration.

        Args:
            webhook_url: Webhook URL for notifications.
            api_key: API key for the notification service.
            timeout: Request timeout in seconds.
        """
        self.webhook_url = webhook_url
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            The async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        return self._client

    async def send_notification(
        self, title: str, message: str, priority: str = "normal", metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send a notification.

        Args:
            title: Notification title.
            message: Notification message.
            priority: Notification priority.
            metadata: Optional metadata.

        Returns:
            True if the notification was sent successfully.
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping notification")
            return False

        try:
            client = await self._get_client()
            payload = {
                "title": title,
                "message": message,
                "priority": priority,
                "metadata": metadata or {},
            }
            response = await client.post(self.webhook_url, json=payload)
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class MetricsIntegration:
    """Integration with Prometheus metrics."""

    def __init__(self, enabled: bool = True) -> None:
        """Initialize the metrics integration.

        Args:
            enabled: Whether metrics collection is enabled.
        """
        self.enabled = enabled
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment_counter(self, name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name.
            value: Value to increment by.
            labels: Optional metric labels.
        """
        if not self.enabled:
            return
        key = self._build_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric.

        Args:
            name: Metric name.
            value: Value to set.
            labels: Optional metric labels.
        """
        if not self.enabled:
            return
        key = self._build_key(name, labels)
        self._gauges[key] = value

    def observe_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe a histogram metric.

        Args:
            name: Metric name.
            value: Observed value.
            labels: Optional metric labels.
        """
        if not self.enabled:
            return
        key = self._build_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics.

        Returns:
            Dictionary of all metrics.
        """
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {k: v.copy() for k, v in self._histograms.items()},
        }

    def _build_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Build a metric key from name and labels.

        Args:
            name: Metric name.
            labels: Metric labels.

        Returns:
            The built key.
        """
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
