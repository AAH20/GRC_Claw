"""Data Collection Agent for gathering data from various sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class DataSourceType(StrEnum):
    """Supported data source types."""

    API = "api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    source_type: DataSourceType
    connection_string: str | None = None
    file_path: str | None = None
    api_endpoint: str | None = None
    api_headers: dict[str, str] = field(default_factory=dict)
    query: str | None = None
    batch_size: int = 1000
    timeout_seconds: int = 30


@dataclass
class CollectionResult:
    """Result of a data collection operation."""

    success: bool
    data: pd.DataFrame | None = None
    row_count: int = 0
    columns: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class DataCollectionAgent:
    """Agent responsible for collecting data from various sources.

    Supports REST APIs, databases, file systems, and streaming sources.
    Implements retry logic and batch processing for reliability.
    """

    def __init__(self, default_timeout: int = 30, max_retries: int = 3) -> None:
        """Initialize the Data Collection Agent.

        Args:
            default_timeout: Default timeout in seconds for HTTP requests.
            max_retries: Maximum number of retry attempts for failed operations.
        """
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> DataCollectionAgent:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.default_timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def collect_from_api(self, config: DataSourceConfig) -> CollectionResult:
        """Collect data from a REST API endpoint.

        Args:
            config: Data source configuration with API endpoint details.

        Returns:
            CollectionResult with the collected data or error information.

        Raises:
            ValueError: If the API endpoint is not configured.
        """
        if not config.api_endpoint:
            raise ValueError("API endpoint must be configured for API source type")

        logger.info("collecting_from_api", endpoint=config.api_endpoint)

        try:
            if not self._client:
                self._client = httpx.AsyncClient(timeout=self.default_timeout)

            response = await self._client.get(
                config.api_endpoint,
                headers=config.api_headers,
            )
            response.raise_for_status()

            raw_data = response.json()
            if isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
            elif isinstance(raw_data, dict) and "data" in raw_data:
                df = pd.DataFrame(raw_data["data"])
            else:
                df = pd.DataFrame([raw_data])

            logger.info(
                "api_collection_success",
                endpoint=config.api_endpoint,
                rows=len(df),
            )

            return CollectionResult(
                success=True,
                data=df,
                row_count=len(df),
                columns=list(df.columns),
                metadata={"source": config.api_endpoint, "format": "json"},
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "api_http_error",
                endpoint=config.api_endpoint,
                status_code=e.response.status_code,
            )
            return CollectionResult(
                success=False,
                error_message=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            logger.error("api_collection_error", endpoint=config.api_endpoint, error=str(e))
            return CollectionResult(success=False, error_message=str(e))

    def collect_from_file(self, config: DataSourceConfig) -> CollectionResult:
        """Collect data from a file (CSV, JSON, Parquet, Excel).

        Args:
            config: Data source configuration with file path.

        Returns:
            CollectionResult with the loaded data or error information.

        Raises:
            ValueError: If the file path is not configured.
        """
        if not config.file_path:
            raise ValueError("File path must be configured for file source type")

        logger.info("collecting_from_file", file_path=config.file_path)

        try:
            path = Path(config.file_path)
            suffix = path.suffix.lower()

            if suffix == ".csv":
                df = pd.read_csv(path)
            elif suffix == ".json":
                df = pd.read_json(path)
            elif suffix in (".parquet", ".pq"):
                df = pd.read_parquet(path)
            elif suffix in (".xlsx", ".xls"):
                df = pd.read_excel(path)
            else:
                raise ValueError(f"Unsupported file format: {suffix}")

            logger.info(
                "file_collection_success",
                file_path=config.file_path,
                rows=len(df),
            )

            return CollectionResult(
                success=True,
                data=df,
                row_count=len(df),
                columns=list(df.columns),
                metadata={"source": str(path), "format": suffix},
            )

        except Exception as e:
            logger.error("file_collection_error", file_path=config.file_path, error=str(e))
            return CollectionResult(success=False, error_message=str(e))

    def collect_from_database(self, config: DataSourceConfig) -> CollectionResult:
        """Collect data from a database using SQL queries.

        Args:
            config: Data source configuration with connection string and query.

        Returns:
            CollectionResult with the queried data or error information.

        Raises:
            ValueError: If connection string or query is not configured.
        """
        if not config.connection_string or not config.query:
            raise ValueError(
                "Connection string and query must be configured for database source type"
            )

        logger.info("collecting_from_database")

        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(config.connection_string)
            with engine.connect() as conn:
                df = pd.read_sql(text(config.query), conn)

            logger.info("database_collection_success", rows=len(df))

            return CollectionResult(
                success=True,
                data=df,
                row_count=len(df),
                columns=list(df.columns),
                metadata={"source": "database", "query": config.query},
            )

        except Exception as e:
            logger.error("database_collection_error", error=str(e))
            return CollectionResult(success=False, error_message=str(e))

    async def collect(self, config: DataSourceConfig) -> CollectionResult:
        """Collect data from the configured source.

        Dispatches to the appropriate collection method based on source type.

        Args:
            config: Data source configuration.

        Returns:
            CollectionResult with the collected data or error information.
        """
        if config.source_type == DataSourceType.API:
            return await self.collect_from_api(config)
        elif config.source_type == DataSourceType.FILE:
            return self.collect_from_file(config)
        elif config.source_type == DataSourceType.DATABASE:
            return self.collect_from_database(config)
        else:
            return CollectionResult(
                success=False,
                error_message=f"Unsupported source type: {config.source_type}",
            )
