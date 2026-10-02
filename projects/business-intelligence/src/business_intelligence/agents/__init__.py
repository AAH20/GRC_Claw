"""Agent module for the Business Intelligence platform."""

from business_intelligence.agents.analysis import AnalysisAgent
from business_intelligence.agents.data_collection import DataCollectionAgent
from business_intelligence.agents.predictive_analytics import PredictiveAnalyticsAgent
from business_intelligence.agents.reporting import ReportingAgent
from business_intelligence.agents.visualization import VisualizationAgent

__all__ = [
    "AnalysisAgent",
    "DataCollectionAgent",
    "PredictiveAnalyticsAgent",
    "ReportingAgent",
    "VisualizationAgent",
]
