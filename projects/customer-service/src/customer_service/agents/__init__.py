"""Agent module for Customer Service AI Platform."""

from customer_service.agents.customer_success import CustomerSuccessAgent
from customer_service.agents.escalation import EscalationAgent
from customer_service.agents.resolution import ResolutionAgent
from customer_service.agents.sentiment_analysis import SentimentAnalysisAgent
from customer_service.agents.triage import TriageAgent

__all__ = [
    "TriageAgent",
    "ResolutionAgent",
    "EscalationAgent",
    "SentimentAnalysisAgent",
    "CustomerSuccessAgent",
]
