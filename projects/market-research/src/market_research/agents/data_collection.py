"""Data Collection Agent for gathering market data from research platforms."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class DataSource(StrEnum):
    """Supported data sources for market research."""

    STATISTA = "statista"
    IBISWORLD = "ibisworld"
    SEMRUSH = "semrush"


class DataCollectionStatus(StrEnum):
    """Status of a data collection task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class MarketDataPoint(BaseModel):
    """A single market data point collected from a source."""

    source: DataSource
    metric: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CollectionRequest(BaseModel):
    """Request to collect market data."""

    query: str
    sources: list[DataSource] = Field(default_factory=lambda: list(DataSource))
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    max_results: int = Field(default=100, ge=1, le=1000)


class CollectionResult(BaseModel):
    """Result of a data collection operation."""

    request_id: str
    status: DataCollectionStatus
    data_points: list[MarketDataPoint] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    total_sources_queried: int = 0
    total_sources_succeeded: int = 0


@dataclass
class SourceConfig:
    """Configuration for a data source."""

    name: DataSource
    enabled: bool = True
    priority: int = 1
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    _semaphore: asyncio.Semaphore | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the semaphore for rate limiting."""
        self._semaphore = asyncio.Semaphore(self.rate_limit_per_minute)


class DataCollectionAgent:
    """Agent responsible for collecting market data from various research platforms.

    This agent orchestrates data collection from Statista, IBISWorld, SEMrush,
    and other configured sources. It handles rate limiting, retries, and
    aggregation of results into a unified format.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        http_client: Any | None = None,
    ) -> None:
        """Initialize the Data Collection Agent.

        Args:
            config: Optional configuration dictionary for the agent.
            http_client: Optional HTTP client for making requests.
        """
        self.config = config or {}
        self.http_client = http_client
        self._sources: dict[DataSource, SourceConfig] = {}
        self._setup_sources()
        logger.info("data_collection_agent_initialized", sources=list(self._sources))

    def _setup_sources(self) -> None:
        """Set up data source configurations."""
        source_configs = self.config.get("sources", [s.value for s in DataSource])
        for source in DataSource:
            if source.value in source_configs:
                self._sources[source] = SourceConfig(
                    name=source,
                    enabled=True,
                    priority=self.config.get(f"{source.value}_priority", 1),
                    rate_limit_per_minute=self.config.get(
                        f"{source.value}_rate_limit", 60
                    ),
                    timeout_seconds=self.config.get(f"{source.value}_timeout", 30),
                )

    async def collect(self, request: CollectionRequest) -> CollectionResult:
        """Collect market data from configured sources.

        Args:
            request: The collection request specifying query and parameters.

        Returns:
            CollectionResult with all collected data points and status.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.query.strip():
            raise ValueError("Query must not be empty")

        request_id = f"dc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        logger.info(
            "starting_data_collection",
            request_id=request_id,
            query=request.query,
            sources=[s.value for s in request.sources],
        )

        tasks: list[asyncio.Task[list[MarketDataPoint]]] = []
        for source in request.sources:
            if source in self._sources and self._sources[source].enabled:
                task = asyncio.create_task(
                    self._collect_from_source(source, request),
                    name=f"collect_{source.value}",
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_data_points: list[MarketDataPoint] = []
        errors: list[str] = []
        succeeded = 0

        for source, result in zip(request.sources, results, strict=True):
            if isinstance(result, BaseException):
                error_msg = f"Failed to collect from {source.value}: {result}"
                logger.error("source_collection_failed", source=source.value, error=str(result))
                errors.append(error_msg)
            else:
                points: list[MarketDataPoint] = result
                all_data_points.extend(points)
                if points:
                    succeeded += 1

        status = self._determine_status(len(tasks), succeeded, len(errors))

        logger.info(
            "data_collection_completed",
            request_id=request_id,
            status=status.value,
            data_points_count=len(all_data_points),
            errors_count=len(errors),
        )

        return CollectionResult(
            request_id=request_id,
            status=status,
            data_points=all_data_points,
            errors=errors,
            total_sources_queried=len(tasks),
            total_sources_succeeded=succeeded,
        )

    async def _collect_from_source(
        self,
        source: DataSource,
        request: CollectionRequest,
    ) -> list[MarketDataPoint]:
        """Collect data from a single source.

        Args:
            source: The data source to collect from.
            request: The collection request.

        Returns:
            List of market data points from the source.
        """
        source_config = self._sources[source]
        logger.info("collecting_from_source", source=source.value, query=request.query)

        assert source_config._semaphore is not None, "Semaphore must be initialized"
        async with source_config._semaphore:
            try:
                if source == DataSource.STATISTA:
                    return await self._collect_statista(request)
                elif source == DataSource.IBISWORLD:
                    return await self._collect_ibisworld(request)
                elif source == DataSource.SEMRUSH:
                    return await self._collect_semrush(request)
                else:
                    logger.warning("unknown_source", source=source.value)
                    return []
            except Exception as exc:
                logger.error(
                    "source_collection_error",
                    source=source.value,
                    error=str(exc),
                    exc_info=True,
                )
                raise

    async def _collect_statista(self, request: CollectionRequest) -> list[MarketDataPoint]:
        """Collect data from Statista API.

        Args:
            request: The collection request.

        Returns:
            List of market data points from Statista.
        """
        # Integration with Statista API would go here
        logger.info("statista_collection_started", query=request.query)
        await asyncio.sleep(0.1)  # Simulate API call
        return [
            MarketDataPoint(
                source=DataSource.STATISTA,
                metric="market_size",
                value=1000000.0,
                unit="USD",
                confidence=0.9,
            )
        ]

    async def _collect_ibisworld(self, request: CollectionRequest) -> list[MarketDataPoint]:
        """Collect data from IBISWorld API.

        Args:
            request: The collection request.

        Returns:
            List of market data points from IBISWorld.
        """
        logger.info("ibisworld_collection_started", query=request.query)
        await asyncio.sleep(0.1)  # Simulate API call
        return [
            MarketDataPoint(
                source=DataSource.IBISWORLD,
                metric="industry_revenue",
                value=5000000.0,
                unit="USD",
                confidence=0.85,
            )
        ]

    async def _collect_semrush(self, request: CollectionRequest) -> list[MarketDataPoint]:
        """Collect data from SEMrush API.

        Args:
            request: The collection request.

        Returns:
            List of market data points from SEMrush.
        """
        logger.info("semrush_collection_started", query=request.query)
        await asyncio.sleep(0.1)  # Simulate API call
        return [
            MarketDataPoint(
                source=DataSource.SEMRUSH,
                metric="search_volume",
                value=50000.0,
                unit="searches/month",
                confidence=0.8,
            )
        ]

    def _determine_status(
        self,
        total: int,
        succeeded: int,
        errors: int,
    ) -> DataCollectionStatus:
        """Determine the overall collection status.

        Args:
            total: Total number of sources queried.
            succeeded: Number of sources that succeeded.
            errors: Number of errors encountered.

        Returns:
            The determined status.
        """
        if total == 0:
            return DataCollectionStatus.FAILED
        if succeeded == 0:
            return DataCollectionStatus.FAILED
        if errors == 0:
            return DataCollectionStatus.COMPLETED
        if succeeded > 0:
            return DataCollectionStatus.PARTIAL
        return DataCollectionStatus.FAILED

    def get_source_status(self) -> dict[str, dict[str, Any]]:
        """Get the status of all configured data sources.

        Returns:
            Dictionary mapping source names to their status info.
        """
        return {
            source.value: {
                "enabled": config.enabled,
                "priority": config.priority,
                "rate_limit": config.rate_limit_per_minute,
            }
            for source, config in self._sources.items()
        }
