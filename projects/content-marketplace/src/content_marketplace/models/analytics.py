"""Analytics models for content marketplace."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class TimeSeriesData(BaseModel):
    """Time series data point."""

    timestamp: datetime
    value: float


class AnalyticsSummary(BaseModel):
    """Summary statistics for analytics."""

    total_listings: int = 0
    active_listings: int = 0
    total_transactions: int = 0
    total_volume: float = 0.0
    average_transaction_value: float = 0.0
    conversion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    top_categories: list[dict[str, float]] = Field(default_factory=list)
    revenue_trend: list[TimeSeriesData] = Field(default_factory=list)


class MarketplaceAnalytics(BaseModel):
    """Full marketplace analytics model."""

    id: UUID = Field(default_factory=lambda: UUID(int=0))
    period_start: datetime
    period_end: datetime
    summary: AnalyticsSummary
    category_breakdown: dict[str, int] = Field(default_factory=dict)
    seller_leaderboard: list[dict[str, float]] = Field(default_factory=list)
    buyer_leaderboard: list[dict[str, float]] = Field(default_factory=list)
    pricing_insights: dict[str, float] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
