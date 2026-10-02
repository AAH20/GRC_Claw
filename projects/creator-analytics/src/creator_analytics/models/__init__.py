"""Pydantic models for creator analytics data structures."""

from .audience import Audience, AudienceDemographics, AudienceSegment
from .content import ContentPerformance, ContentMetrics, ContentType
from .revenue import RevenueReport, RevenueStream, RevenueBreakdown
from .growth import GrowthPrediction, GrowthMetric, GrowthScenario
from .engagement import EngagementReport, EngagementMetrics, EngagementType

__all__ = [
    "Audience",
    "AudienceDemographics",
    "AudienceSegment",
    "ContentPerformance",
    "ContentMetrics",
    "ContentType",
    "RevenueReport",
    "RevenueStream",
    "RevenueBreakdown",
    "GrowthPrediction",
    "GrowthMetric",
    "GrowthScenario",
    "EngagementReport",
    "EngagementMetrics",
    "EngagementType",
]
