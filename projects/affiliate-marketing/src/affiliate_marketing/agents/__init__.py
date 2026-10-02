"""Agent package for the Affiliate Marketing Platform."""

from affiliate_marketing.agents.analytics import AnalyticsAgent
from affiliate_marketing.agents.optimization import OptimizationAgent
from affiliate_marketing.agents.payout import PayoutAgent
from affiliate_marketing.agents.recruitment import RecruitmentAgent
from affiliate_marketing.agents.tracking import TrackingAgent

__all__ = [
    "AnalyticsAgent",
    "OptimizationAgent",
    "PayoutAgent",
    "RecruitmentAgent",
    "TrackingAgent",
]
