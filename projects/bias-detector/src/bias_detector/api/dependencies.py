"""FastAPI dependencies for bias-detector."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from bias_detector.agents import (
    DemographicAnalyzerAgent,
    FairnessScorerAgent,
    LanguageBiasDetectorAgent,
    PatternDetectorAgent,
    RecommendationAgent,
)

# Singleton agent instances
_demographic_analyzer = DemographicAnalyzerAgent()
_language_bias_detector = LanguageBiasDetectorAgent()
_fairness_scorer = FairnessScorerAgent()
_pattern_detector = PatternDetectorAgent()
_recommendation_agent = RecommendationAgent()


def get_demographic_analyzer() -> DemographicAnalyzerAgent:
    """Get the demographic analyzer agent singleton.

    Returns:
        DemographicAnalyzerAgent: The singleton instance.
    """
    return _demographic_analyzer


def get_language_bias_detector() -> LanguageBiasDetectorAgent:
    """Get the language bias detector agent singleton.

    Returns:
        LanguageBiasDetectorAgent: The singleton instance.
    """
    return _language_bias_detector


def get_fairness_scorer() -> FairnessScorerAgent:
    """Get the fairness scorer agent singleton.

    Returns:
        FairnessScorerAgent: The singleton instance.
    """
    return _fairness_scorer


def get_pattern_detector() -> PatternDetectorAgent:
    """Get the pattern detector agent singleton.

    Returns:
        PatternDetectorAgent: The singleton instance.
    """
    return _pattern_detector


def get_recommendation_agent() -> RecommendationAgent:
    """Get the recommendation agent singleton.

    Returns:
        RecommendationAgent: The singleton instance.
    """
    return _recommendation_agent


DemographicAnalyzerDep = Annotated[DemographicAnalyzerAgent, Depends(get_demographic_analyzer)]
LanguageBiasDetectorDep = Annotated[LanguageBiasDetectorAgent, Depends(get_language_bias_detector)]
FairnessScorerDep = Annotated[FairnessScorerAgent, Depends(get_fairness_scorer)]
PatternDetectorDep = Annotated[PatternDetectorAgent, Depends(get_pattern_detector)]
RecommendationAgentDep = Annotated[RecommendationAgent, Depends(get_recommendation_agent)]
