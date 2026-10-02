"""Agent module for the Conversational Marketing platform."""

from conversational_marketing.agents.analytics import AnalyticsAgent
from conversational_marketing.agents.handoff import HandoffAgent
from conversational_marketing.agents.intent_detection import IntentDetectionAgent
from conversational_marketing.agents.optimization import OptimizationAgent
from conversational_marketing.agents.response_generation import ResponseGenerationAgent

__all__ = [
    "AnalyticsAgent",
    "HandoffAgent",
    "IntentDetectionAgent",
    "OptimizationAgent",
    "ResponseGenerationAgent",
]
