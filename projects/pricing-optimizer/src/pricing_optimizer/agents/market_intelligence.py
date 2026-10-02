"""Market Intelligence Agent.

Gathers competitor pricing, demand signals, and market trends
to inform pricing decisions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CompetitorPrice(BaseModel):
    """Represents a competitor's price for a comparable product."""

    competitor_id: str
    product_name: str
    price: float
    currency: str = "USD"
    url: str | None = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class DemandSignal(BaseModel):
    """Represents a demand indicator for a product."""

    product_id: str
    signal_type: str  # e.g., "search_trend", "sales_velocity", "seasonality"
    value: float
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketTrend(BaseModel):
    """Represents a detected market trend."""

    trend_id: str
    category: str
    direction: str  # "upward", "downward", "stable"
    magnitude: float
    description: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class MarketIntelligenceReport(BaseModel):
    """Comprehensive market intelligence report."""

    product_id: str
    competitor_prices: list[CompetitorPrice] = Field(default_factory=list)
    demand_signals: list[DemandSignal] = Field(default_factory=list)
    market_trends: list[MarketTrend] = Field(default_factory=list)
    average_competitor_price: float | None = None
    price_position: str | None = None  # "premium", "parity", "discount"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class MarketIntelligenceConfig:
    """Configuration for the Market Intelligence Agent."""

    max_competitors: int = 10
    update_interval_minutes: int = 60
    request_timeout_seconds: float = 30.0
    rate_limit_per_second: float = 2.0


class MarketIntelligenceAgent:
    """Agent responsible for gathering and analyzing market intelligence.

    This agent collects competitor pricing data, demand signals, and
    market trends from various data sources to provide actionable
    insights for pricing optimization.
    """

    def __init__(
        self,
        config: MarketIntelligenceConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the Market Intelligence Agent.

        Args:
            config: Agent configuration. Uses defaults if not provided.
            http_client: Optional pre-configured HTTP client for external calls.
        """
        self.config = config or MarketIntelligenceConfig()
        self._http_client = http_client
        self._semaphore = asyncio.Semaphore(int(self.config.rate_limit_per_second))
        self._cache: dict[str, MarketIntelligenceReport] = {}
        self._last_update: dict[str, datetime] = {}
        logger.info(
            "market_intelligence_agent_initialized",
            max_competitors=self.config.max_competitors,
            update_interval=self.config.update_interval_minutes,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            An async HTTP client instance.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.request_timeout_seconds,
                headers={"User-Agent": "PricingOptimizer/0.1"},
            )
        return self._http_client

    async def gather_competitor_prices(
        self,
        product_id: str,
        product_name: str,
        category: str | None = None,
    ) -> list[CompetitorPrice]:
        """Gather competitor prices for a given product.

        Args:
            product_id: The internal product identifier.
            product_name: Human-readable product name for matching.
            category: Optional product category to narrow search.

        Returns:
            List of competitor prices found.

        Raises:
            ValueError: If product_id or product_name is empty.
        """
        if not product_id or not product_name:
            raise ValueError("product_id and product_name are required")

        logger.info(
            "gathering_competitor_prices",
            product_id=product_id,
            product_name=product_name,
            category=category,
        )

        # In production, this would query competitor APIs, scraping services,
        # or a market intelligence database. Here we simulate the structure.
        competitor_prices: list[CompetitorPrice] = []

        try:
            await self._get_client()
            async with self._semaphore:
                # Placeholder for actual competitor data fetching
                # Example: response = await client.get(
                #     f"https://api.marketdata.com/v1/prices",
                #     params={"product": product_name, "category": category},
                # )
                await asyncio.sleep(0.01)  # Simulate network latency
                logger.debug("competitor_data_fetched", product_id=product_id)
        except httpx.HTTPError as exc:
            logger.error(
                "competitor_data_fetch_failed",
                product_id=product_id,
                error=str(exc),
            )

        return competitor_prices

    async def analyze_demand_signals(self, product_id: str) -> list[DemandSignal]:
        """Analyze demand signals for a product.

        Args:
            product_id: The product identifier to analyze.

        Returns:
            List of demand signals with confidence scores.

        Raises:
            ValueError: If product_id is empty.
        """
        if not product_id:
            raise ValueError("product_id is required")

        logger.info("analyzing_demand_signals", product_id=product_id)

        signals: list[DemandSignal] = []

        try:
            await self._get_client()
            async with self._semaphore:
                # Placeholder: fetch from analytics platform
                await asyncio.sleep(0.01)
                logger.debug("demand_signals_fetched", product_id=product_id)
        except httpx.HTTPError as exc:
            logger.error(
                "demand_signal_fetch_failed",
                product_id=product_id,
                error=str(exc),
            )

        return signals

    async def detect_market_trends(self, category: str) -> list[MarketTrend]:
        """Detect market trends for a product category.

        Args:
            category: The product category to analyze.

        Returns:
            List of detected market trends.

        Raises:
            ValueError: If category is empty.
        """
        if not category:
            raise ValueError("category is required")

        logger.info("detecting_market_trends", category=category)

        trends: list[MarketTrend] = []

        try:
            await self._get_client()
            async with self._semaphore:
                # Placeholder: fetch from trend analysis service
                await asyncio.sleep(0.01)
                logger.debug("market_trends_detected", category=category)
        except httpx.HTTPError as exc:
            logger.error(
                "market_trend_detection_failed",
                category=category,
                error=str(exc),
            )

        return trends

    def _calculate_price_position(
        self,
        our_price: float,
        competitor_prices: list[CompetitorPrice],
    ) -> str | None:
        """Calculate our price position relative to competitors.

        Args:
            our_price: Our current price.
            competitor_prices: List of competitor prices.

        Returns:
            Price position label or None if no competitor data.
        """
        if not competitor_prices:
            return None

        avg_competitor = sum(cp.price for cp in competitor_prices) / len(competitor_prices)
        ratio = our_price / avg_competitor if avg_competitor > 0 else 1.0

        if ratio > 1.05:
            return "premium"
        if ratio < 0.95:
            return "discount"
        return "parity"

    async def generate_report(
        self,
        product_id: str,
        product_name: str,
        our_price: float,
        category: str | None = None,
    ) -> MarketIntelligenceReport:
        """Generate a comprehensive market intelligence report.

        Args:
            product_id: The product identifier.
            product_name: Human-readable product name.
            our_price: Our current price for the product.
            category: Optional product category.

        Returns:
            A complete market intelligence report.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        if not product_id or not product_name:
            raise ValueError("product_id and product_name are required")
        if our_price < 0:
            raise ValueError("our_price must be non-negative")

        logger.info(
            "generating_market_intelligence_report",
            product_id=product_id,
            product_name=product_name,
        )

        competitor_prices = await self.gather_competitor_prices(
            product_id, product_name, category
        )
        demand_signals = await self.analyze_demand_signals(product_id)
        market_trends = await self.detect_market_trends(category or "general")

        avg_competitor_price = (
            sum(cp.price for cp in competitor_prices) / len(competitor_prices)
            if competitor_prices
            else None
        )

        report = MarketIntelligenceReport(
            product_id=product_id,
            competitor_prices=competitor_prices,
            demand_signals=demand_signals,
            market_trends=market_trends,
            average_competitor_price=avg_competitor_price,
            price_position=self._calculate_price_position(our_price, competitor_prices),
        )

        self._cache[product_id] = report
        self._last_update[product_id] = datetime.utcnow()

        logger.info(
            "market_intelligence_report_generated",
            product_id=product_id,
            competitor_count=len(competitor_prices),
            signal_count=len(demand_signals),
            trend_count=len(market_trends),
        )

        return report

    def get_cached_report(self, product_id: str) -> MarketIntelligenceReport | None:
        """Retrieve a cached report if still fresh.

        Args:
            product_id: The product identifier.

        Returns:
            Cached report if available and fresh, None otherwise.
        """
        report = self._cache.get(product_id)
        if report is None:
            return None

        last_update = self._last_update.get(product_id)
        if last_update is None:
            return None

        age = datetime.utcnow() - last_update
        if age > timedelta(minutes=self.config.update_interval_minutes):
            return None

        return report

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("market_intelligence_agent_closed")
