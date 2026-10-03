"""Bias detector agents."""

from recruitment_platform.agents.bias_detector.demographic_analyzer import (
    DemographicAnalyzer,
)
from recruitment_platform.agents.bias_detector.fairness_scorer import FairnessScorer
from recruitment_platform.agents.bias_detector.language_bias_detector import (
    LanguageBiasDetector,
)
from recruitment_platform.agents.bias_detector.pattern_detector import PatternDetector
from recruitment_platform.agents.bias_detector.recommendation import Recommendation

__all__ = [
    "DemographicAnalyzer",
    "FairnessScorer",
    "LanguageBiasDetector",
    "PatternDetector",
    "Recommendation",
]
