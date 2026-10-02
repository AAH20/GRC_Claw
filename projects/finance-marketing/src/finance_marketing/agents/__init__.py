"""Agent module for Finance Marketing Platform."""

from finance_marketing.agents.analytics import AnalyticsAgent
from finance_marketing.agents.campaigns import CampaignAgent
from finance_marketing.agents.compliance import ComplianceAgent
from finance_marketing.agents.content import ContentAgent
from finance_marketing.agents.reporting import ReportingAgent

__all__ = [
    "AnalyticsAgent",
    "CampaignAgent",
    "ComplianceAgent",
    "ContentAgent",
    "ReportingAgent",
]
