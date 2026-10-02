"""Pydantic models for creator analytics data structures."""

from .audience import AgeGroup, Audience, AudienceDemographics, AudienceSegment, Gender
from .content import ContentMetrics, ContentPerformance, ContentType
from .engagement import EngagementMetrics, EngagementReport, EngagementType
from .growth import GrowthMetric, GrowthPrediction, GrowthScenario
from .revenue import RevenueBreakdown, RevenueReport, RevenueStream

__all__ = [
    "AgeGroup",
    "Audience",
    "AudienceDemographics",
    "AudienceSegment",
    "Gender",
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
