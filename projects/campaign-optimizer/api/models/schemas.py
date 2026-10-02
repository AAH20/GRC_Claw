"""Pydantic models for API request and response validation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignGoal(str, Enum):
    """Supported campaign goals."""

    AWARENESS = "awareness"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REACH = "reach"


class Channel(str, Enum):
    """Supported marketing channels."""

    SEARCH = "search"
    SOCIAL = "social"
    DISPLAY = "display"
    EMAIL = "email"
    VIDEO = "video"


class CampaignCreateRequest(BaseModel):
    """Request model for creating a new campaign."""

    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    description: str = Field(default="", max_length=2000, description="Campaign description")
    goals: list[CampaignGoal] = Field(..., min_length=1, description="Campaign goals")
    total_budget: float = Field(..., gt=0, description="Total campaign budget in USD")
    daily_budget: float = Field(..., gt=0, description="Daily budget in USD")
    channels: list[Channel] = Field(..., min_length=1, description="Marketing channels")
    duration_days: int = Field(..., ge=1, le=365, description="Campaign duration in days")
    target_audience: dict[str, Any] = Field(
        default_factory=dict, description="Target audience parameters"
    )
    brand_voice: str = Field(default="professional", description="Brand tone and style")
    key_message: str = Field(default="", description="Core marketing message")
    competitors: list[str] = Field(default_factory=list, description="Competitor names")
    industry: str = Field(default="general", description="Industry or category")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Q4 Product Launch",
                    "description": "Launch campaign for new product line",
                    "goals": ["awareness", "conversion"],
                    "total_budget": 50000,
                    "daily_budget": 1666.67,
                    "channels": ["search", "social", "display"],
                    "duration_days": 30,
                    "target_audience": {
                        "demographics": {"age_ranges": ["25-34", "35-44"]},
                        "locations": ["US", "CA"],
                    },
                    "brand_voice": "professional",
                    "key_message": "The future of productivity is here",
                    "competitors": ["competitor_a", "competitor_b"],
                    "industry": "technology",
                }
            ]
        }
    }


class CampaignUpdateRequest(BaseModel):
    """Request model for updating an existing campaign."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    goals: list[CampaignGoal] | None = None
    total_budget: float | None = Field(default=None, gt=0)
    daily_budget: float | None = Field(default=None, gt=0)
    channels: list[Channel] | None = None
    duration_days: int | None = Field(default=None, ge=1, le=365)
    target_audience: dict[str, Any] | None = None
    brand_voice: str | None = None
    key_message: str | None = None
    status: CampaignStatus | None = None


class CampaignResponse(BaseModel):
    """Response model for campaign data."""

    id: str = Field(..., description="Unique campaign identifier")
    name: str = Field(..., description="Campaign name")
    description: str = Field(default="", description="Campaign description")
    status: CampaignStatus = Field(..., description="Current campaign status")
    goals: list[CampaignGoal] = Field(..., description="Campaign goals")
    total_budget: float = Field(..., description="Total budget in USD")
    daily_budget: float = Field(..., description="Daily budget in USD")
    channels: list[Channel] = Field(..., description="Active channels")
    duration_days: int = Field(..., description="Campaign duration in days")
    target_audience: dict[str, Any] = Field(default_factory=dict)
    brand_voice: str = Field(default="professional")
    key_message: str = Field(default="")
    industry: str = Field(default="general")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Current performance metrics"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "camp_abc123",
                    "name": "Q4 Product Launch",
                    "status": "active",
                    "goals": ["awareness", "conversion"],
                    "total_budget": 50000,
                    "daily_budget": 1666.67,
                    "channels": ["search", "social"],
                    "duration_days": 30,
                    "created_at": "2024-10-01T00:00:00Z",
                    "updated_at": "2024-10-01T00:00:00Z",
                }
            ]
        }
    }


class CampaignListResponse(BaseModel):
    """Response model for listing campaigns."""

    campaigns: list[CampaignResponse] = Field(..., description="List of campaigns")
    total: int = Field(..., description="Total number of campaigns")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")


class OptimizationRequest(BaseModel):
    """Request model for triggering campaign optimization."""

    optimization_type: str = Field(
        default="full",
        description="Type of optimization: full, bidding, creative, audience, budget",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Additional optimization parameters"
    )


class OptimizationResponse(BaseModel):
    """Response model for optimization results."""

    campaign_id: str = Field(..., description="Campaign identifier")
    optimization_id: str = Field(..., description="Optimization run identifier")
    status: str = Field(..., description="Optimization status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    results: dict[str, Any] = Field(
        default_factory=dict, description="Optimization results"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable recommendations"
    )


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""

    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Current agent status")
    tools_count: int = Field(..., description="Number of available tools")
    timeout: int = Field(..., description="Agent timeout in seconds")
    max_iterations: int = Field(..., description="Maximum iterations allowed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current timestamp")
    components: dict[str, str] = Field(
        default_factory=dict, description="Component health statuses"
    )


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )
    request_id: str | None = Field(default=None, description="Request identifier")
