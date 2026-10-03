"""Job Description Optimizer Agent.

Provides tools to analyze and optimize job descriptions for readability,
inclusivity, and SEO performance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class OptimizationSuggestion:
    """A single suggestion for improving a job description."""

    category: str
    severity: str  # "low", "medium", "high"
    original: str
    suggestion: str
    reason: str


@dataclass
class OptimizedDescription:
    """Result of optimizing a job description."""

    original: str
    optimized: str
    suggestions: list[OptimizationSuggestion] = field(default_factory=list)
    score_before: float = 0.0
    score_after: float = 0.0


@dataclass
class DescriptionMetrics:
    """Metrics computed from a job description."""

    readability: dict[str, Any] = field(default_factory=dict)
    inclusivity: dict[str, Any] = field(default_factory=dict)
    seo: dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

INCLUSIVE_LANGUAGE_MAP: dict[str, str] = {
    "rockstar": "skilled professional",
    "ninja": "expert",
    "guru": "specialist",
    "dominant": "leading",
    "aggressive": "ambitious",
    "competitive": "results-driven",
    "manpower": "workforce",
    "mankind": "humanity",
    "chairman": "chairperson",
    "fire": "terminate",
    "kill": "eliminate",
    "crazy": "intense",
    "insane": "high-energy",
    "lame": "inadequate",
    "dumb": "uninformed",
    "blind": "unaware",
    "deaf": "unresponsive",
    "handicapped": "person with a disability",
    "sanity check": "quick review",
    "master": "primary",
    "slave": "secondary",
    "blacklist": "blocklist",
    "whitelist": "allowlist",
    "grandfathered": "legacy",
    "guys": "team",
    "he": "they",
    "she": "they",
    "his": "their",
    "her": "their",
    "him": "them",
}

EXCLUDED_SEO_KEYWORDS: set[str] = {
    "synergy",
    "leverage",
    "paradigm",
    "disruptive",
    "cutting-edge",
    "world-class",
    "best-of-breed",
    "mission-critical",
    "thought leader",
    "game-changer",
    "move the needle",
    "low-hanging fruit",
    "circle back",
    "deep dive",
}

POWER_WORDS: set[str] = {
    "innovative",
    "collaborative",
    "inclusive",
    "diverse",
    "equitable",
    "accessible",
    "flexible",
    "remote-friendly",
    "growth-oriented",
    "impactful",
    "meaningful",
    "purpose-driven",
    "transparent",
    "supportive",
    "empowering",
}

COMMON_JD_SECTIONS: list[str] = [
    "about the role",
    "responsibilities",
    "requirements",
    "qualifications",
    "benefits",
    "compensation",
    "how to apply",
    "equal opportunity",
    "company overview",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _flesch_kincaid_grade(text: str) -> float:
    """Compute Flesch-Kincaid grade level (mock implementation)."""
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    words = len(text.split())
    syllables = _count_syllables(text)
    grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
    return round(max(grade, 0.0), 2)


def _flesch_reading_ease(text: str) -> float:
    """Compute Flesch Reading Ease score (mock implementation)."""
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    words = len(text.split())
    syllables = _count_syllables(text)
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return round(max(0.0, min(score, 100.0)), 2)


def _count_syllables(text: str) -> int:
    """Rough syllable counter for English text."""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    count = 0
    for word in text.split():
        vowels = re.findall(r"[aeiouy]+", word)
        count += max(len(vowels), 1)
    return count


def _detect_gendered_language(text: str) -> list[str]:
    """Detect potentially gendered terms in text."""
    gendered_terms: list[str] = []
    text_lower = text.lower()
    gendered_patterns = [
        r"\b(he|she|him|her|his|hers)\b",
        r"\b(man|woman|men|women)\b",
        r"\b(chairman|chairwoman|fireman|firewoman)\b",
        r"\b(mankind|manpower)\b",
        r"\b(guys|gals)\b",
    ]
    for pattern in gendered_patterns:
        matches = re.findall(pattern, text_lower)
        gendered_terms.extend(matches)
    return list(set(gendered_terms))


def _detect_exclusive_language(text: str) -> list[str]:
    """Detect non-inclusive terms in text."""
    found: list[str] = []
    text_lower = text.lower()
    for term in INCLUSIVE_LANGUAGE_MAP:
        if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
            found.append(term)
    return found


def _detect_missing_sections(text: str) -> list[str]:
    """Detect which common JD sections are missing."""
    text_lower = text.lower()
    missing: list[str] = []
    for section in COMMON_JD_SECTIONS:
        if section not in text_lower:
            missing.append(section)
    return missing


def _detect_buzzwords(text: str) -> list[str]:
    """Detect overused buzzwords that hurt SEO."""
    found: list[str] = []
    text_lower = text.lower()
    for word in EXCLUDED_SEO_KEYWORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
            found.append(word)
    return found


def _detect_power_words(text: str) -> list[str]:
    """Detect positive power words present in the text."""
    found: list[str] = []
    text_lower = text.lower()
    for word in POWER_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
            found.append(word)
    return found


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def _sentence_count(text: str) -> int:
    """Count sentences in text."""
    return max(len(re.findall(r"[.!?]+", text)), 1)


def _avg_sentence_length(text: str) -> float:
    """Compute average sentence length in words."""
    sentences = _sentence_count(text)
    words = _word_count(text)
    return round(words / sentences, 2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_description(job_description: str) -> DescriptionMetrics:
    """Analyze a job description and return readability, inclusivity, and SEO metrics.

    Args:
        job_description: The raw job description text to analyze.

    Returns:
        DescriptionMetrics with detailed scores and findings.
    """
    if not job_description or not job_description.strip():
        return DescriptionMetrics(
            readability={"error": "Empty job description"},
            inclusivity={"error": "Empty job description"},
            seo={"error": "Empty job description"},
            overall_score=0.0,
        )

    # Readability metrics
    fk_grade = _flesch_kincaid_grade(job_description)
    flesch_score = _flesch_reading_ease(job_description)
    word_count = _word_count(job_description)
    sentence_count = _sentence_count(job_description)
    avg_sent_len = _avg_sentence_length(job_description)

    readability = {
        "flesch_kincaid_grade": fk_grade,
        "flesch_reading_ease": flesch_score,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sent_len,
        "readability_level": _readability_level(flesch_score),
    }

    # Inclusivity metrics
    gendered_terms = _detect_gendered_language(job_description)
    exclusive_terms = _detect_exclusive_language(job_description)
    power_words = _detect_power_words(job_description)

    inclusivity_score = max(0.0, 100.0 - len(gendered_terms) * 10 - len(exclusive_terms) * 8)
    inclusivity_score = round(inclusivity_score + len(power_words) * 2, 2)
    inclusivity_score = min(inclusivity_score, 100.0)

    inclusivity = {
        "gendered_terms_found": gendered_terms,
        "exclusive_terms_found": exclusive_terms,
        "power_words_found": power_words,
        "inclusivity_score": inclusivity_score,
        "is_inclusive": inclusivity_score >= 70.0,
    }

    # SEO metrics
    buzzwords = _detect_buzzwords(job_description)
    missing_sections = _detect_missing_sections(job_description)

    seo_score = 100.0
    seo_score -= len(buzzwords) * 5
    seo_score -= len(missing_sections) * 3
    seo_score = max(0.0, round(seo_score, 2))

    seo = {
        "buzzwords_found": buzzwords,
        "missing_sections": missing_sections,
        "seo_score": seo_score,
        "has_good_structure": len(missing_sections) <= 2,
        "keyword_density": _estimate_keyword_density(job_description),
    }

    # Overall score
    overall = round((flesch_score * 0.3 + inclusivity_score * 0.4 + seo_score * 0.3), 2)

    return DescriptionMetrics(
        readability=readability,
        inclusivity=inclusivity,
        seo=seo,
        overall_score=overall,
    )


def optimize_description(job_description: str) -> OptimizedDescription:
    """Optimize a job description and return improved version with suggestions.

    Args:
        job_description: The raw job description text to optimize.

    Returns:
        OptimizedDescription with the improved text and list of suggestions.
    """
    if not job_description or not job_description.strip():
        return OptimizedDescription(
            original=job_description or "",
            optimized="",
            suggestions=[
                OptimizationSuggestion(
                    category="general",
                    severity="high",
                    original="",
                    suggestion="Provide a non-empty job description.",
                    reason="Cannot optimize an empty description.",
                )
            ],
            score_before=0.0,
            score_after=0.0,
        )

    suggestions: list[OptimizationSuggestion] = []
    optimized = job_description

    # 1. Replace exclusive language
    exclusive_terms = _detect_exclusive_language(job_description)
    for term in exclusive_terms:
        replacement = INCLUSIVE_LANGUAGE_MAP.get(term, term)
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        optimized = pattern.sub(replacement, optimized)
        suggestions.append(
            OptimizationSuggestion(
                category="inclusivity",
                severity="high",
                original=term,
                suggestion=replacement,
                reason=f"'{term}' may be exclusionary. Consider using '{replacement}' instead.",
            )
        )

    # 2. Replace gendered pronouns with they/them
    gendered_terms = _detect_gendered_language(job_description)
    pronoun_map = {
        "he": "they",
        "she": "they",
        "him": "them",
        "his": "their",
        "her": "their",
        "hers": "theirs",
    }
    for term in gendered_terms:
        if term.lower() in pronoun_map:
            replacement = pronoun_map[term.lower()]
            pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
            optimized = pattern.sub(replacement, optimized)
            suggestions.append(
                OptimizationSuggestion(
                    category="inclusivity",
                    severity="medium",
                    original=term,
                    suggestion=replacement,
                    reason=f"Use '{replacement}' instead of gendered '{term}' for inclusivity.",
                )
            )

    # 3. Remove buzzwords
    buzzwords = _detect_buzzwords(job_description)
    for word in buzzwords:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        optimized = pattern.sub("", optimized)
        suggestions.append(
            OptimizationSuggestion(
                category="seo",
                severity="medium",
                original=word,
                suggestion="(removed)",
                reason=f"'{word}' is an overused buzzword that reduces SEO effectiveness.",
            )
        )

    # 4. Clean up extra whitespace from removals
    optimized = re.sub(r"\s{2,}", " ", optimized)
    optimized = re.sub(r"\s+([.,;:!?])", r"\1", optimized)
    optimized = optimized.strip()

    # 5. Add missing sections as suggestions
    missing_sections = _detect_missing_sections(optimized)
    for section in missing_sections:
        suggestions.append(
            OptimizationSuggestion(
                category="structure",
                severity="low",
                original="(missing)",
                suggestion=f"Add a '{section}' section.",
                reason=f"Job descriptions with a '{section}' section perform better in search results.",
            )
        )

    # 6. Suggest adding power words if few are present
    power_words = _detect_power_words(optimized)
    if len(power_words) < 3:
        suggestions.append(
            OptimizationSuggestion(
                category="engagement",
                severity="low",
                original="",
                suggestion="Consider adding power words like 'innovative', 'collaborative', or 'inclusive'.",
                reason="Power words increase applicant engagement by up to 30%.",
            )
        )

    # Compute before/after scores
    before_metrics = analyze_description(job_description)
    after_metrics = analyze_description(optimized)

    return OptimizedDescription(
        original=job_description,
        optimized=optimized,
        suggestions=suggestions,
        score_before=before_metrics.overall_score,
        score_after=after_metrics.overall_score,
    )


def _readability_level(flesch_score: float) -> str:
    """Convert Flesch score to a human-readable level."""
    if flesch_score >= 80:
        return "easy"
    elif flesch_score >= 60:
        return "standard"
    elif flesch_score >= 40:
        return "difficult"
    else:
        return "very difficult"


def _estimate_keyword_density(text: str) -> dict[str, float]:
    """Estimate keyword density for common job-related terms."""
    text_lower = text.lower()
    words = text_lower.split()
    total = max(len(words), 1)

    keywords = [
        "experience",
        "skills",
        "team",
        "develop",
        "manage",
        "design",
        "build",
        "create",
        "lead",
        "support",
    ]

    density: dict[str, float] = {}
    for kw in keywords:
        count = sum(1 for w in words if kw in w)
        density[kw] = round(count / total * 100, 2)

    return density
