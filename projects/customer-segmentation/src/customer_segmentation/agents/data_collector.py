"""Data Collector Agent - Gathers customer data from CRM and analytics platforms."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from customer_segmentation.config import get_settings
from customer_segmentation.integrations.google_analytics import GoogleAnalyticsIntegration
from customer_segmentation.integrations.hubspot import HubSpotIntegration
from customer_segmentation.integrations.salesforce import SalesforceIntegration
from customer_segmentation.models import Customer

logger = structlog.get_logger(__name__)


class DataSource(Protocol):
    """Protocol for data source integrations."""

    async def fetch_customers(
        self, filters: dict[str, Any] | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]: ...

    async def fetch_customer_by_id(self, customer_id: str) -> dict[str, Any] | None: ...

    async def health_check(self) -> bool: ...


@dataclass
class CollectionResult:
    """Result of a data collection operation."""

    source: str
    customers: list[dict[str, Any]] = field(default_factory=list)
    total_fetched: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """Get the duration of the collection operation."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()


class BaseAgent:
    """Base class for all agents."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = logger.bind(agent=self.__class__.__name__)


class DataCollectorAgent(BaseAgent):
    """Agent responsible for collecting customer data from multiple sources.

    This agent orchestrates data collection from Salesforce, HubSpot,
    and Google Analytics, merging and deduplicating customer records.
    """

    def __init__(self) -> None:
        super().__init__()
        self._integrations: dict[str, DataSource] = {}
        self._initialize_integrations()

    def _initialize_integrations(self) -> None:
        """Initialize available integration connectors."""
        try:
            self._integrations["salesforce"] = SalesforceIntegration()
            self.logger.info("Salesforce integration initialized")
        except Exception as e:
            self.logger.warning("Failed to initialize Salesforce integration", error=str(e))

        try:
            self._integrations["hubspot"] = HubSpotIntegration()
            self.logger.info("HubSpot integration initialized")
        except Exception as e:
            self.logger.warning("Failed to initialize HubSpot integration", error=str(e))

        try:
            self._integrations["google_analytics"] = GoogleAnalyticsIntegration()
            self.logger.info("Google Analytics integration initialized")
        except Exception as e:
            self.logger.warning(
                "Failed to initialize Google Analytics integration", error=str(e)
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def collect_from_source(
        self,
        source: str,
        filters: dict[str, Any] | None = None,
        limit: int = 1000,
    ) -> CollectionResult:
        """Collect customer data from a single source.

        Args:
            source: The data source name (salesforce, hubspot, google_analytics).
            filters: Optional filters to apply during collection.
            limit: Maximum number of records to fetch.

        Returns:
            CollectionResult with the fetched customer data.

        Raises:
            ValueError: If the source is not supported.
        """
        if source not in self._integrations:
            raise ValueError(
                f"Unsupported data source: {source}. "
                f"Available: {list(self._integrations.keys())}"
            )

        integration = self._integrations[source]
        result = CollectionResult(source=source)

        self.logger.info("Starting data collection", source=source, limit=limit)

        try:
            customers = await integration.fetch_customers(filters=filters, limit=limit)
            result.customers = customers
            result.total_fetched = len(customers)
            result.completed_at = datetime.utcnow()

            self.logger.info(
                "Data collection completed",
                source=source,
                count=len(customers),
                duration=result.duration_seconds,
            )
        except Exception as e:
            error_msg = f"Failed to collect from {source}: {str(e)}"
            result.errors.append(error_msg)
            result.completed_at = datetime.utcnow()
            self.logger.error(error_msg, source=source)
            raise

        return result

    async def collect_all(
        self,
        filters: dict[str, Any] | None = None,
        limit_per_source: int = 1000,
    ) -> dict[str, CollectionResult]:
        """Collect customer data from all available sources concurrently.

        Args:
            filters: Optional filters to apply during collection.
            limit_per_source: Maximum records per source.

        Returns:
            Dictionary mapping source names to their CollectionResults.
        """
        tasks = {
            source: self.collect_from_source(source, filters, limit_per_source)
            for source in self._integrations
        }

        results: dict[str, CollectionResult] = {}
        for source, task in tasks.items():
            try:
                results[source] = await task
            except Exception as e:
                self.logger.error("Collection failed for source", source=source, error=str(e))
                results[source] = CollectionResult(
                    source=source,
                    errors=[str(e)],
                    completed_at=datetime.utcnow(),
                )

        return results

    def merge_customer_records(
        self, records: list[dict[str, Any]]
    ) -> list[Customer]:
        """Merge and deduplicate customer records from multiple sources.

        Uses email as the primary deduplication key, falling back to
        phone number when email is not available.

        Args:
            records: Raw customer records from various sources.

        Returns:
            List of merged Customer models.
        """
        merged: dict[str, Customer] = {}

        for record in records:
            email = record.get("email", "").lower().strip()
            phone = record.get("phone", "").strip()
            key = email or phone

            if not key:
                continue

            if key in merged:
                existing = merged[key]
                for field_name, value in record.items():
                    if value and not getattr(existing, field_name, None):
                        setattr(existing, field_name, value)
            else:
                try:
                    merged[key] = Customer(
                        id=record.get("id") or key,
                        email=record.get("email"),
                        first_name=record.get("first_name"),
                        last_name=record.get("last_name"),
                        phone=record.get("phone"),
                        company=record.get("company"),
                        industry=record.get("industry"),
                        job_title=record.get("job_title"),
                        country=record.get("country"),
                        city=record.get("city"),
                        total_revenue=record.get("total_revenue", 0.0),
                        total_orders=record.get("total_orders", 0),
                        lifetime_value=record.get("lifetime_value", 0.0),
                        metadata=record.get("metadata", {}),
                    )
                except Exception as e:
                    self.logger.warning(
                        "Failed to parse customer record",
                        error=str(e),
                        record_id=record.get("id"),
                    )

        return list(merged.values())

    async def execute(
        self,
        filters: dict[str, Any] | None = None,
        limit_per_source: int = 1000,
        merge: bool = True,
    ) -> dict[str, Any]:
        """Execute the full data collection pipeline.

        Args:
            filters: Optional filters for data collection.
            limit_per_source: Maximum records per source.
            merge: Whether to merge and deduplicate records.

        Returns:
            Dictionary with collection results and merged customers.
        """
        self.logger.info("Starting data collection pipeline")

        results = await self.collect_all(filters, limit_per_source)

        all_records: list[dict[str, Any]] = []
        for result in results.values():
            all_records.extend(result.customers)

        customers: list[Customer] = []
        if merge:
            customers = self.merge_customer_records(all_records)

        return {
            "sources": {k: v.model_dump() for k, v in results.items()},
            "total_records": len(all_records),
            "merged_customers": len(customers),
            "customers": [c.model_dump() for c in customers],
        }
