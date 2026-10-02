"""Agent package — exports all agent classes."""

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent
from agents.research import ResearchAgent, ResearchInput, ResearchOutput
from agents.evidence import EvidenceAgent, EvidenceInput, EvidenceOutput
from agents.scoring import ScoringAgent, ScoringInput, ScoringOutput
from agents.qualification import (
    QualificationAgent,
    QualificationInput,
    QualificationOutput,
)
from agents.churn_prediction import (
    ChurnPredictionAgent,
    ChurnPredictionInput,
    ChurnPredictionOutput,
)
from agents.next_best_action import (
    NextBestActionAgent,
    NextBestActionInput,
    NextBestActionOutput,
)
from agents.insight_synthesis import (
    InsightSynthesisAgent,
    InsightSynthesisInput,
    InsightSynthesisOutput,
)

__all__ = [
    # Base
    "AgentConfig",
    "AgentContext",
    "AgentResult",
    "BaseAgent",
    # Research
    "ResearchAgent",
    "ResearchInput",
    "ResearchOutput",
    # Evidence
    "EvidenceAgent",
    "EvidenceInput",
    "EvidenceOutput",
    # Scoring
    "ScoringAgent",
    "ScoringInput",
    "ScoringOutput",
    # Qualification
    "QualificationAgent",
    "QualificationInput",
    "QualificationOutput",
    # Churn Prediction
    "ChurnPredictionAgent",
    "ChurnPredictionInput",
    "ChurnPredictionOutput",
    # Next Best Action
    "NextBestActionAgent",
    "NextBestActionInput",
    "NextBestActionOutput",
    # Insight Synthesis
    "InsightSynthesisAgent",
    "InsightSynthesisInput",
    "InsightSynthesisOutput",
]
