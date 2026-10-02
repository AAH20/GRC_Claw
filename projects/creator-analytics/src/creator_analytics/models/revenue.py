"""Revenue tracking Pydantic models."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class RevenueStream(str, Enum):
    """Types of revenue streams."""

    ADVERTISING = "advertising"
    SPONSORSHIPS = "sponsorships"
    MERCHANDISE = "merchandise"
    SUBSCRIPTIONS = "subscriptions"
    TIPS = "tips"
    AFFILIATE = "affiliate"
    COURSES = "courses"
    LICENSING = "licensing"
    BRAND_DEALS = "brand_deals"


class RevenueBreakdown(BaseModel):
    """Breakdown of revenue by stream."""

    stream: RevenueStream = Field(..., description="Revenue stream type")
    amount: float = Field(..., ge=0.0, description="Revenue amount")
    currency: str = Field(default="USD", description="Currency code")
    percentage_of_total: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of total revenue"
    )
    growth_rate: float = Field(..., description="Growth rate as a decimal")
    transactions: int = Field(default=0, ge=0, description="Number of transactions")
    average_transaction_value: float = Field(
        default=0.0, ge=0.0, description="Average transaction value"
    )


class RevenueReport(BaseModel):
    """Comprehensive revenue report for a creator."""

    creator_id: str = Field(..., description="Creator identifier")
    report_period_start: datetime = Field(..., description="Report period start")
    report_period_end: datetime = Field(..., description="Report period end")
    total_revenue: float = Field(..., ge=0.0, description="Total revenue")
    currency: str = Field(default="USD", description="Currency code")
    breakdown: list[RevenueBreakdown] = Field(
        default_factory=list, description="Revenue breakdown by stream"
    )
    recurring_revenue: float = Field(
        default=0.0, ge=0.0, description="Monthly recurring revenue"
    )
    one_time_revenue: float = Field(
        default=0.0, ge=0.0, description="One-time revenue"
    )
    projected_annual_revenue: float = Field(
        default=0.0, ge=0.0, description="Projected annual revenue"
    )
    revenue_per_follower: float = Field(
        default=0.0, ge=0.0, description="Revenue per follower"
    )
    top_performing_content: list[str] = Field(
        default_factory=list, description="Top performing content IDs by revenue"
    )
    insights: list[str] = Field(
        default_factory=list, description="AI-generated revenue insights"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="AI-generated recommendations"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation timestamp"
    )
