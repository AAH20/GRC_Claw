"""Agent implementations for bias detection using LangChain DeepAgents."""

from bias_detector.agents.demographic_analyzer import DemographicAnalyzerAgent
from bias_detector.agents.fairness_scorer import FairnessScorerAgent
from bias_detector.agents.language_bias_detector import LanguageBiasDetectorAgent
from bias_detector.agents.pattern_detector import PatternDetectorAgent
from bias_detector.agents.recommendation import RecommendationAgent

__all__ = [
    "DemographicAnalyzerAgent",
    "LanguageBiasDetectorAgent",
    "FairnessScorerAgent",
    "PatternDetectorAgent",
    "RecommendationAgent",
]
