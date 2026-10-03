"""Skills Assessor Agent for the Recruitment Platform.

Provides skill gap analysis and personalized learning-path recommendations
for candidates based on required job skills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ProficiencyLevel(str, Enum):
    """Standardized proficiency scale."""

    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class GapSeverity(str, Enum):
    """How critical a skill gap is."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"


@dataclass
class Skill:
    """A single skill with a name and proficiency level."""

    name: str
    level: ProficiencyLevel = ProficiencyLevel.BEGINNER
    years_experience: float = 0.0


@dataclass
class SkillGap:
    """Represents the delta between a required skill and the candidate's level."""

    skill_name: str
    required_level: ProficiencyLevel
    current_level: ProficiencyLevel
    severity: GapSeverity
    gap_score: int  # 0–4, higher = bigger gap


@dataclass
class SkillGapAnalysis:
    """Full result of an assess_skills call."""

    candidate_id: str
    required_skills: List[Skill]
    candidate_skills: List[Skill]
    gaps: List[SkillGap]
    overall_readiness_pct: float  # 0–100
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class LearningResource:
    """A single learning resource recommendation."""

    title: str
    resource_type: str  # e.g. "course", "book", "tutorial", "project"
    url: Optional[str] = None
    estimated_hours: float = 0.0
    difficulty: ProficiencyLevel = ProficiencyLevel.BEGINNER


@dataclass
class LearningPathStep:
    """One step in a personalized learning path."""

    order: int
    skill_name: str
    target_level: ProficiencyLevel
    resources: List[LearningResource]
    estimated_weeks: float
    milestone: str


@dataclass
class LearningPath:
    """Full personalized learning path."""

    candidate_id: str
    steps: List[LearningPathStep]
    total_estimated_weeks: float
    total_estimated_hours: float


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

# Canonical proficiency ordering for gap calculation
_PROFICIENCY_ORDER: Dict[ProficiencyLevel, int] = {
    ProficiencyLevel.NOVICE: 0,
    ProficiencyLevel.BEGINNER: 1,
    ProficiencyLevel.INTERMEDIATE: 2,
    ProficiencyLevel.ADVANCED: 3,
    ProficiencyLevel.EXPERT: 4,
}

# Mock candidate skill database (keyed by candidate_id)
_MOCK_CANDIDATE_DB: Dict[str, List[Skill]] = {
    "CAND-001": [
        Skill("Python", ProficiencyLevel.ADVANCED, 5.0),
        Skill("SQL", ProficiencyLevel.INTERMEDIATE, 3.0),
        Skill("Docker", ProficiencyLevel.BEGINNER, 1.0),
        Skill("AWS", ProficiencyLevel.INTERMEDIATE, 2.5),
        Skill("Kubernetes", ProficiencyLevel.NOVICE, 0.0),
        Skill("Communication", ProficiencyLevel.ADVANCED, 6.0),
    ],
    "CAND-002": [
        Skill("JavaScript", ProficiencyLevel.EXPERT, 7.0),
        Skill("TypeScript", ProficiencyLevel.ADVANCED, 4.0),
        Skill("React", ProficiencyLevel.ADVANCED, 4.5),
        Skill("Node.js", ProficiencyLevel.INTERMEDIATE, 3.0),
        Skill("GraphQL", ProficiencyLevel.BEGINNER, 0.5),
        Skill("Testing", ProficiencyLevel.INTERMEDIATE, 2.0),
    ],
    "CAND-003": [
        Skill("Java", ProficiencyLevel.INTERMEDIATE, 3.0),
        Skill("Spring Boot", ProficiencyLevel.BEGINNER, 1.0),
        Skill("PostgreSQL", ProficiencyLevel.INTERMEDIATE, 2.5),
        Skill("Redis", ProficiencyLevel.NOVICE, 0.0),
        Skill("Kafka", ProficiencyLevel.BEGINNER, 0.5),
        Skill("Microservices", ProficiencyLevel.BEGINNER, 0.5),
    ],
}

# Mock learning resource catalog (keyed by skill name)
_MOCK_RESOURCE_CATALOG: Dict[str, List[LearningResource]] = {
    "Python": [
        LearningResource("Python Crash Course", "book", "https://nostarch.com/pythoncrashcourse2e", 40, ProficiencyLevel.BEGINNER),
        LearningResource("Advanced Python Mastery", "course", "https://example.com/advanced-python", 30, ProficiencyLevel.ADVANCED),
        LearningResource("Real Python Tutorials", "tutorial", "https://realpython.com", 20, ProficiencyLevel.INTERMEDIATE),
    ],
    "SQL": [
        LearningResource("SQLBolt Interactive", "tutorial", "https://sqlbolt.com", 10, ProficiencyLevel.BEGINNER),
        LearningResource("Mode SQL Tutorial", "tutorial", "https://mode.com/sql-tutorial", 15, ProficiencyLevel.INTERMEDIATE),
        LearningResource("SQL Performance Explained", "book", "https://example.com/sql-perf", 25, ProficiencyLevel.ADVANCED),
    ],
    "Docker": [
        LearningResource("Docker Getting Started", "tutorial", "https://docs.docker.com/get-started", 8, ProficiencyLevel.BEGINNER),
        LearningResource("Docker Deep Dive", "book", "https://example.com/docker-deep-dive", 20, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Docker Mastery Course", "course", "https://example.com/docker-mastery", 25, ProficiencyLevel.ADVANCED),
    ],
    "AWS": [
        LearningResource("AWS Cloud Practitioner Essentials", "course", "https://example.com/aws-cloud-practitioner", 20, ProficiencyLevel.BEGINNER),
        LearningResource("AWS Solutions Architect Associate", "course", "https://example.com/aws-saa", 40, ProficiencyLevel.INTERMEDIATE),
        LearningResource("AWS Well-Architected", "tutorial", "https://example.com/aws-well-architected", 15, ProficiencyLevel.ADVANCED),
    ],
    "Kubernetes": [
        LearningResource("Kubernetes Basics", "tutorial", "https://kubernetes.io/docs/tutorials/kubernetes-basics", 10, ProficiencyLevel.BEGINNER),
        LearningResource("Kubernetes Up & Running", "book", "https://example.com/k8s-up-running", 30, ProficiencyLevel.INTERMEDIATE),
        LearningResource("CKA Certification Prep", "course", "https://example.com/cka-prep", 50, ProficiencyLevel.ADVANCED),
    ],
    "Communication": [
        LearningResource("Crucial Conversations", "book", "https://example.com/crucial-conversations", 12, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Toastmasters Pathways", "course", "https://example.com/toastmasters", 20, ProficiencyLevel.BEGINNER),
    ],
    "JavaScript": [
        LearningResource("Eloquent JavaScript", "book", "https://eloquentjavascript.net", 35, ProficiencyLevel.BEGINNER),
        LearningResource("You Don't Know JS", "book", "https://github.com/getify/You-Dont-Know-JS", 30, ProficiencyLevel.INTERMEDIATE),
        LearningResource("JavaScript: The Hard Parts", "course", "https://example.com/js-hard-parts", 15, ProficiencyLevel.ADVANCED),
    ],
    "TypeScript": [
        LearningResource("TypeScript Handbook", "tutorial", "https://www.typescriptlang.org/docs/handbook", 10, ProficiencyLevel.BEGINNER),
        LearningResource("Effective TypeScript", "book", "https://example.com/effective-ts", 20, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Advanced TypeScript Patterns", "course", "https://example.com/adv-ts", 25, ProficiencyLevel.ADVANCED),
    ],
    "React": [
        LearningResource("React Official Tutorial", "tutorial", "https://react.dev/learn", 15, ProficiencyLevel.BEGINNER),
        LearningResource("Epic React", "course", "https://example.com/epic-react", 40, ProficiencyLevel.ADVANCED),
        LearningResource("React Patterns", "book", "https://example.com/react-patterns", 20, ProficiencyLevel.INTERMEDIATE),
    ],
    "Node.js": [
        LearningResource("Node.js Design Patterns", "book", "https://example.com/node-design-patterns", 25, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Node.js Official Guide", "tutorial", "https://nodejs.org/en/docs/guides", 10, ProficiencyLevel.BEGINNER),
    ],
    "GraphQL": [
        LearningResource("GraphQL Official Tutorial", "tutorial", "https://graphql.org/learn", 8, ProficiencyLevel.BEGINNER),
        LearningResource("Production-Ready GraphQL", "book", "https://example.com/prod-graphql", 20, ProficiencyLevel.INTERMEDIATE),
    ],
    "Testing": [
        LearningResource("Testing JavaScript", "course", "https://example.com/testing-js", 20, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Test-Driven Development by Example", "book", "https://example.com/tdd-by-example", 15, ProficiencyLevel.BEGINNER),
    ],
    "Java": [
        LearningResource("Head First Java", "book", "https://example.com/head-first-java", 30, ProficiencyLevel.BEGINNER),
        LearningResource("Effective Java", "book", "https://example.com/effective-java", 25, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Java Concurrency in Practice", "book", "https://example.com/jcip", 30, ProficiencyLevel.ADVANCED),
    ],
    "Spring Boot": [
        LearningResource("Spring Boot Guides", "tutorial", "https://spring.io/guides", 10, ProficiencyLevel.BEGINNER),
        LearningResource("Spring Boot in Action", "book", "https://example.com/spring-boot-action", 20, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Spring Microservices", "course", "https://example.com/spring-microservices", 35, ProficiencyLevel.ADVANCED),
    ],
    "PostgreSQL": [
        LearningResource("PostgreSQL Tutorial", "tutorial", "https://www.postgresqltutorial.com", 12, ProficiencyLevel.BEGINNER),
        LearningResource("Mastering PostgreSQL", "book", "https://example.com/mastering-pg", 25, ProficiencyLevel.INTERMEDIATE),
    ],
    "Redis": [
        LearningResource("Redis University", "course", "https://example.com/redis-univ", 15, ProficiencyLevel.BEGINNER),
        LearningResource("Redis in Action", "book", "https://example.com/redis-in-action", 20, ProficiencyLevel.INTERMEDIATE),
    ],
    "Kafka": [
        LearningResource("Kafka: The Definitive Guide", "book", "https://example.com/kafka-guide", 25, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Confluent Kafka Tutorials", "tutorial", "https://developer.confluent.io", 15, ProficiencyLevel.BEGINNER),
    ],
    "Microservices": [
        LearningResource("Building Microservices", "book", "https://example.com/building-microservices", 20, ProficiencyLevel.INTERMEDIATE),
        LearningResource("Microservices Patterns", "book", "https://example.com/microservices-patterns", 30, ProficiencyLevel.ADVANCED),
    ],
}

# Default resources for skills not in the catalog
_DEFAULT_RESOURCES: List[LearningResource] = [
    LearningResource("Official Documentation", "tutorial", None, 10, ProficiencyLevel.BEGINNER),
    LearningResource("Community Best Practices Guide", "book", None, 15, ProficiencyLevel.INTERMEDIATE),
    LearningResource("Hands-on Project Walkthrough", "project", None, 20, ProficiencyLevel.INTERMEDIATE),
]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _severity_from_gap(gap_score: int) -> GapSeverity:
    """Map a numeric gap score to a severity level."""
    if gap_score <= 0:
        return GapSeverity.NONE
    if gap_score == 1:
        return GapSeverity.MINOR
    if gap_score == 2:
        return GapSeverity.MODERATE
    return GapSeverity.CRITICAL


def _get_candidate_skills(candidate_id: str) -> List[Skill]:
    """Retrieve candidate skills from the mock database."""
    return _MOCK_CANDIDATE_DB.get(candidate_id, [])


def _get_resources_for_skill(skill_name: str) -> List[LearningResource]:
    """Look up learning resources for a given skill."""
    return _MOCK_RESOURCE_CATALOG.get(skill_name, _DEFAULT_RESOURCES)


def _estimate_weeks(gap_score: int, current_level: ProficiencyLevel) -> float:
    """Rough estimate of weeks needed to close a gap."""
    base_weeks = {1: 2.0, 2: 4.0, 3: 8.0, 4: 12.0}
    multiplier = 1.0 if current_level == ProficiencyLevel.NOVICE else 0.75
    return base_weeks.get(gap_score, 4.0) * multiplier


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_skills(
    candidate_id: str,
    required_skills: List[Skill],
) -> SkillGapAnalysis:
    """Assess a candidate's skills against a set of required skills.

    Args:
        candidate_id: Unique identifier for the candidate.
        required_skills: List of Skill objects representing the job requirements.

    Returns:
        SkillGapAnalysis with gap details, readiness score, strengths, and weaknesses.
    """
    candidate_skills = _get_candidate_skills(candidate_id)
    candidate_skill_map: Dict[str, Skill] = {s.name: s for s in candidate_skills}

    gaps: List[SkillGap] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    total_gap_score = 0
    max_possible_gap = len(required_skills) * 4  # max gap_score per skill is 4

    for req_skill in required_skills:
        cand_skill = candidate_skill_map.get(req_skill.name)

        if cand_skill is None:
            # Candidate has no record of this skill — treat as NOVICE
            current_level = ProficiencyLevel.NOVICE
        else:
            current_level = cand_skill.level

        req_val = _PROFICIENCY_ORDER[req_skill.level]
        cur_val = _PROFICIENCY_ORDER[current_level]
        gap_score = max(0, req_val - cur_val)
        severity = _severity_from_gap(gap_score)

        gap = SkillGap(
            skill_name=req_skill.name,
            required_level=req_skill.level,
            current_level=current_level,
            severity=severity,
            gap_score=gap_score,
        )
        gaps.append(gap)
        total_gap_score += gap_score

        if gap_score == 0:
            strengths.append(req_skill.name)
        else:
            weaknesses.append(req_skill.name)

    # Readiness: 100% when no gaps, scales down with total gap
    if max_possible_gap == 0:
        readiness = 100.0
    else:
        readiness = round(max(0.0, (1 - total_gap_score / max_possible_gap) * 100), 1)

    return SkillGapAnalysis(
        candidate_id=candidate_id,
        required_skills=required_skills,
        candidate_skills=candidate_skills,
        gaps=gaps,
        overall_readiness_pct=readiness,
        strengths=strengths,
        weaknesses=weaknesses,
    )


def recommend_learning_path(skill_gaps: List[SkillGap]) -> LearningPath:
    """Generate a personalized learning path from a list of skill gaps.

    Args:
        skill_gaps: List of SkillGap objects (typically from assess_skills).

    Returns:
        LearningPath with ordered steps, resources, and time estimates.
    """
    # Filter out gaps with no severity and sort by severity (largest first)
    actionable_gaps = [g for g in skill_gaps if g.severity != GapSeverity.NONE]
    actionable_gaps.sort(key=lambda g: g.gap_score, reverse=True)

    steps: List[LearningPathStep] = []
    total_weeks = 0.0
    total_hours = 0.0

    for order, gap in enumerate(actionable_gaps, start=1):
        resources = _get_resources_for_skill(gap.skill_name)
        est_weeks = _estimate_weeks(gap.gap_score, gap.current_level)
        est_hours = sum(r.estimated_hours for r in resources[:2])  # top 2 resources

        step = LearningPathStep(
            order=order,
            skill_name=gap.skill_name,
            target_level=gap.required_level,
            resources=resources,
            estimated_weeks=est_weeks,
            milestone=f"Reach {gap.required_level.value} in {gap.skill_name}",
        )
        steps.append(step)
        total_weeks += est_weeks
        total_hours += est_hours

    return LearningPath(
        candidate_id="",  # caller can set this if needed
        steps=steps,
        total_estimated_weeks=round(total_weeks, 1),
        total_estimated_hours=round(total_hours, 1),
    )


# ---------------------------------------------------------------------------
# Convenience / Demo
# ---------------------------------------------------------------------------


def _demo() -> None:
    """Quick smoke-test when run as a script."""
    required = [
        Skill("Python", ProficiencyLevel.ADVANCED),
        Skill("SQL", ProficiencyLevel.ADVANCED),
        Skill("Docker", ProficiencyLevel.INTERMEDIATE),
        Skill("AWS", ProficiencyLevel.ADVANCED),
        Skill("Kubernetes", ProficiencyLevel.INTERMEDIATE),
        Skill("Communication", ProficiencyLevel.ADVANCED),
    ]

    analysis = assess_skills("CAND-001", required)
    print(f"Candidate: {analysis.candidate_id}")
    print(f"Readiness: {analysis.overall_readiness_pct}%")
    print(f"Strengths: {analysis.strengths}")
    print(f"Weaknesses: {analysis.weaknesses}")
    for gap in analysis.gaps:
        print(f"  {gap.skill_name}: {gap.current_level.value} -> {gap.required_level.value} "
              f"({gap.severity.value}, score={gap.gap_score})")

    path = recommend_learning_path(analysis.gaps)
    print(f"\nLearning Path ({path.total_estimated_weeks} weeks, {path.total_estimated_hours} hours):")
    for step in path.steps:
        print(f"  {step.order}. {step.skill_name} -> {step.target_level.value} "
              f"({step.estimated_weeks} weeks) — {step.milestone}")


if __name__ == "__main__":
    _demo()
