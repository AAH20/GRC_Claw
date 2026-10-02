"""Language Bias Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
import re
from typing import Any

from deepagents import create_deep_agent

from bias_detector.agents.base import BaseBiasAgent
from bias_detector.config import get_settings
from bias_detector.models import (
    BiasSeverity,
    LanguageBiasResult,
    LanguagePattern,
)

logger = logging.getLogger(__name__)

# Common biased language patterns
GENDERED_WORDS = {
    "he": "they", "she": "they", "his": "their", "her": "their",
    "him": "them", "himself": "themselves", "herself": "themselves",
    "man": "person", "woman": "person", "men": "people", "women": "people",
    "mankind": "humankind", "manpower": "workforce", "chairman": "chairperson",
    "fireman": "firefighter", "policeman": "police officer",
    "salesman": "salesperson", "stewardess": "flight attendant",
    "waitress": "server", "actress": "actor", "male": "", "female": "",
}

AGGRESSIVE_WORDS = [
    "rockstar", "ninja", "guru", "wizard", "superhero", "dominant",
    "aggressive", "competitive", "driven", "fearless", "killer",
]

CULTURE_FIT_WORDS = [
    "culture fit", "beer Fridays", "happy hours", "ping pong",
    "work hard play hard", "young and energetic", "digital native",
]

AGE_INDICATORS = [
    "young", "energetic", "fresh", "recent graduate", "digital native",
    "millennial", "gen z", "mature", "experienced", "seasoned",
]

EXCLUSIONARY_PHRASES = [
    "native english", "english mother tongue", "clean-shaven",
    "well-groomed", "good looking", "attractive", "able-bodied",
]


class LanguageBiasDetectorAgent(BaseBiasAgent[str]):
    """Agent that detects biased language in hiring text.

    This agent scans job descriptions, feedback, and other hiring-related
    text for gendered language, aggressive terminology, culture-fit bias,
    age indicators, and exclusionary phrases.

    Attributes:
        name: Agent identifier.
        description: Agent description.
    """

    name = "language_bias_detector"
    description = "Detects biased language in hiring-related text"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Language Bias Detector Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent for language bias detection.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for language bias detection.

        Returns:
            System prompt string.
        """
        return (
            "You are a language bias detection expert. Analyze text for "
            "gendered language, aggressive terminology, culture-fit bias, "
            "age indicators, and exclusionary phrases. Provide specific "
            "suggestions for more inclusive alternatives."
        )

    async def analyze(self, data: str) -> LanguageBiasResult:
        """Analyze text for biased language patterns.

        Args:
            data: Text to analyze.

        Returns:
            LanguageBiasResult with detected patterns and recommendations.
        """
        logger.info("Starting language bias detection on %d characters", len(data))

        patterns = self._detect_patterns(data)
        bias_score = self._compute_bias_score(patterns, len(data))
        recommendations = self._generate_recommendations(patterns)

        result = LanguageBiasResult(
            patterns=patterns,
            overall_bias_score=bias_score,
            biased_phrases_count=len(patterns),
            text_analyzed=data,
            recommendations=recommendations,
        )

        logger.info(
            "Language bias detection complete: score=%.2f, patterns=%d",
            bias_score,
            len(patterns),
        )
        return result

    def _detect_patterns(self, text: str) -> list[LanguagePattern]:
        """Detect all biased language patterns in text.

        Args:
            text: Text to analyze.

        Returns:
            List of detected language patterns.
        """
        patterns: list[LanguagePattern] = []
        text_lower = text.lower()

        # Check gendered words
        for word, replacement in GENDERED_WORDS.items():
            for match in re.finditer(r"\b" + re.escape(word) + r"\b", text_lower):
                patterns.append(LanguagePattern(
                    pattern_type="gendered_word",
                    text=match.group(),
                    position=match.start(),
                    severity=(
                        BiasSeverity.HIGH
                        if word in ("he", "she", "man", "woman")
                        else BiasSeverity.MEDIUM
                    ),
                    suggestion=(
                        f"Use '{replacement}' instead"
                        if replacement
                        else "Remove gendered term"
                    ),
                    category="gender",
                ))

        # Check aggressive words
        for word in AGGRESSIVE_WORDS:
            for match in re.finditer(r"\b" + re.escape(word) + r"\b", text_lower):
                patterns.append(LanguagePattern(
                    pattern_type="aggressive_terminology",
                    text=match.group(),
                    position=match.start(),
                    severity=BiasSeverity.MEDIUM,
                    suggestion="Use neutral, skills-based language",
                    category="tone",
                ))

        # Check culture fit words
        for phrase in CULTURE_FIT_WORDS:
            for match in re.finditer(re.escape(phrase), text_lower):
                patterns.append(LanguagePattern(
                    pattern_type="culture_fit_bias",
                    text=match.group(),
                    position=match.start(),
                    severity=BiasSeverity.HIGH,
                    suggestion="Focus on values alignment and skills",
                    category="culture",
                ))

        # Check age indicators
        for phrase in AGE_INDICATORS:
            for match in re.finditer(r"\b" + re.escape(phrase) + r"\b", text_lower):
                patterns.append(LanguagePattern(
                    pattern_type="age_indicator",
                    text=match.group(),
                    position=match.start(),
                    severity=BiasSeverity.MEDIUM,
                    suggestion="Use age-neutral language focused on skills",
                    category="age",
                ))

        # Check exclusionary phrases
        for phrase in EXCLUSIONARY_PHRASES:
            for match in re.finditer(re.escape(phrase), text_lower):
                patterns.append(LanguagePattern(
                    pattern_type="exclusionary_phrase",
                    text=match.group(),
                    position=match.start(),
                    severity=BiasSeverity.CRITICAL,
                    suggestion="Remove entirely - potentially discriminatory",
                    category="exclusion",
                ))

        return patterns

    def _compute_bias_score(self, patterns: list[LanguagePattern], text_length: int) -> float:
        """Compute overall bias score from detected patterns.

        Args:
            patterns: Detected language patterns.
            text_length: Length of analyzed text.

        Returns:
            Bias score between 0 and 1.
        """
        if not patterns or text_length == 0:
            return 0.0

        severity_weights = {
            BiasSeverity.LOW: 0.1,
            BiasSeverity.MEDIUM: 0.3,
            BiasSeverity.HIGH: 0.6,
            BiasSeverity.CRITICAL: 1.0,
        }

        total_weight = sum(severity_weights[p.severity] for p in patterns)
        # Normalize by text length (per 1000 chars)
        normalized = total_weight / (text_length / 1000 + 1)
        return min(normalized, 1.0)

    def _generate_recommendations(self, patterns: list[LanguagePattern]) -> list[str]:
        """Generate recommendations based on detected patterns.

        Args:
            patterns: Detected language patterns.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []
        categories = {p.category for p in patterns}

        if "gender" in categories:
            recommendations.append(
                "Replace gendered language with gender-neutral alternatives "
                "(e.g., 'they' instead of 'he/she', 'workforce' instead of 'manpower')"
            )
        if "tone" in categories:
            recommendations.append(
                "Replace aggressive terminology with skills-based descriptions "
                "(e.g., 'experienced' instead of 'rockstar')"
            )
        if "culture" in categories:
            recommendations.append(
                "Replace culture-fit language with values-alignment and "
                "skills-based criteria"
            )
        if "age" in categories:
            recommendations.append(
                "Remove age-related indicators and focus on skills and experience requirements"
            )
        if "exclusion" in categories:
            recommendations.append(
                "Remove exclusionary phrases that may discriminate against protected groups"
            )

        if not recommendations:
            recommendations.append("No significant language bias detected - text appears inclusive")

        return recommendations
