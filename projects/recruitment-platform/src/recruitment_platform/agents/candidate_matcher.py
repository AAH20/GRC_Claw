"""Candidate Matcher Agent for recruitment-platform.

Provides intelligent candidate-to-job matching using a weighted scoring algorithm
that evaluates skill overlap, experience alignment, education fit, and location
compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"


class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"


@dataclass
class Candidate:
    """Represents a job candidate."""

    id: str
    name: str
    email: str
    skills: list[str] = field(default_factory=list)
    years_experience: float = 0.0
    experience_level: ExperienceLevel = ExperienceLevel.MID
    education: EducationLevel = EducationLevel.BACHELORS
    location: str = ""
    remote_preference: bool = False
    desired_salary: int | None = None
    certifications: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    industry_experience: list[str] = field(default_factory=list)


@dataclass
class Job:
    """Represents a job posting."""

    id: str
    title: str
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_years_experience: float = 0.0
    experience_level: ExperienceLevel = ExperienceLevel.MID
    min_education: EducationLevel = EducationLevel.BACHELORS
    location: str = ""
    remote_ok: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    required_certifications: list[str] = field(default_factory=list)
    preferred_languages: list[str] = field(default_factory=list)
    industry: str = ""


@dataclass
class MatchResult:
    """Result of matching a candidate to a job."""

    candidate: Candidate
    job: Job
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    location_score: float
    salary_score: float
    certification_score: float
    breakdown: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

MOCK_CANDIDATES: list[Candidate] = [
    Candidate(
        id="cand-001",
        name="Alice Chen",
        email="alice.chen@example.com",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
        years_experience=7.5,
        experience_level=ExperienceLevel.SENIOR,
        education=EducationLevel.MASTERS,
        location="San Francisco, CA",
        remote_preference=True,
        desired_salary=165000,
        certifications=["AWS Solutions Architect", "CKA"],
        languages=["English", "Mandarin"],
        industry_experience=["fintech", "healthcare"],
    ),
    Candidate(
        id="cand-002",
        name="Bob Martinez",
        email="bob.martinez@example.com",
        skills=["JavaScript", "React", "Node.js", "MongoDB", "TypeScript"],
        years_experience=4.0,
        experience_level=ExperienceLevel.MID,
        education=EducationLevel.BACHELORS,
        location="Austin, TX",
        remote_preference=True,
        desired_salary=120000,
        certifications=["AWS Cloud Practitioner"],
        languages=["English", "Spanish"],
        industry_experience=["e-commerce"],
    ),
    Candidate(
        id="cand-003",
        name="Carol Johnson",
        email="carol.johnson@example.com",
        skills=["Python", "Django", "PostgreSQL", "Redis", "Celery", "Docker"],
        years_experience=9.0,
        experience_level=ExperienceLevel.SENIOR,
        education=EducationLevel.BACHELORS,
        location="New York, NY",
        remote_preference=False,
        desired_salary=155000,
        certifications=["PMP"],
        languages=["English"],
        industry_experience=["fintech", "logistics"],
    ),
    Candidate(
        id="cand-004",
        name="David Kim",
        email="david.kim@example.com",
        skills=["Go", "Kubernetes", "Terraform", "AWS", "gRPC", "Microservices"],
        years_experience=11.0,
        experience_level=ExperienceLevel.PRINCIPAL,
        education=EducationLevel.MASTERS,
        location="Seattle, WA",
        remote_preference=True,
        desired_salary=210000,
        certifications=["AWS Solutions Architect", "CKA", "Terraform Associate"],
        languages=["English", "Korean"],
        industry_experience=["cloud", "SaaS"],
    ),
    Candidate(
        id="cand-005",
        name="Eva Patel",
        email="eva.patel@example.com",
        skills=["Python", "Machine Learning", "TensorFlow", "SQL", "Pandas"],
        years_experience=3.5,
        experience_level=ExperienceLevel.MID,
        education=EducationLevel.MASTERS,
        location="Boston, MA",
        remote_preference=True,
        desired_salary=130000,
        certifications=["TensorFlow Developer Certificate"],
        languages=["English", "Hindi", "Gujarati"],
        industry_experience=["healthcare", "AI"],
    ),
    Candidate(
        id="cand-006",
        name="Frank O'Brien",
        email="frank.obrien@example.com",
        skills=["Java", "Spring Boot", "Kafka", "PostgreSQL", "Docker", "AWS"],
        years_experience=6.0,
        experience_level=ExperienceLevel.SENIOR,
        education=EducationLevel.BACHELORS,
        location="Chicago, IL",
        remote_preference=False,
        desired_salary=145000,
        certifications=["AWS Developer Associate"],
        languages=["English"],
        industry_experience=["fintech", "insurance"],
    ),
    Candidate(
        id="cand-007",
        name="Grace Liu",
        email="grace.liu@example.com",
        skills=["Python", "FastAPI", "React", "PostgreSQL", "GraphQL", "Docker"],
        years_experience=5.5,
        experience_level=ExperienceLevel.SENIOR,
        education=EducationLevel.BACHELORS,
        location="Remote",
        remote_preference=True,
        desired_salary=140000,
        certifications=[],
        languages=["English", "Mandarin"],
        industry_experience=["SaaS", "fintech"],
    ),
    Candidate(
        id="cand-008",
        name="Hassan Ahmed",
        email="hassan.ahmed@example.com",
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"],
        years_experience=8.0,
        experience_level=ExperienceLevel.SENIOR,
        education=EducationLevel.MASTERS,
        location="Cairo, Egypt",
        remote_preference=True,
        desired_salary=95000,
        certifications=["AWS Solutions Architect", "CKAD"],
        languages=["English", "Arabic"],
        industry_experience=["fintech", "edtech"],
    ),
]

MOCK_JOBS: dict[str, Job] = {
    "job-001": Job(
        id="job-001",
        title="Senior Backend Engineer",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        preferred_skills=["Kubernetes", "AWS", "Redis", "Celery"],
        min_years_experience=5.0,
        experience_level=ExperienceLevel.SENIOR,
        min_education=EducationLevel.BACHELORS,
        location="San Francisco, CA",
        remote_ok=True,
        salary_min=140000,
        salary_max=180000,
        required_certifications=[],
        preferred_languages=["English"],
        industry="fintech",
    ),
    "job-002": Job(
        id="job-002",
        title="Full-Stack Developer",
        required_skills=["JavaScript", "React", "Node.js", "TypeScript"],
        preferred_skills=["GraphQL", "Docker", "AWS"],
        min_years_experience=3.0,
        experience_level=ExperienceLevel.MID,
        min_education=EducationLevel.BACHELORS,
        location="Austin, TX",
        remote_ok=True,
        salary_min=100000,
        salary_max=140000,
        required_certifications=[],
        preferred_languages=["English"],
        industry="e-commerce",
    ),
    "job-003": Job(
        id="job-003",
        title="Staff Platform Engineer",
        required_skills=["Go", "Kubernetes", "Terraform", "AWS"],
        preferred_skills=["gRPC", "Microservices", "Python"],
        min_years_experience=8.0,
        experience_level=ExperienceLevel.PRINCIPAL,
        min_education=EducationLevel.MASTERS,
        location="Seattle, WA",
        remote_ok=True,
        salary_min=180000,
        salary_max=240000,
        required_certifications=["AWS Solutions Architect"],
        preferred_languages=["English"],
        industry="cloud",
    ),
    "job-004": Job(
        id="job-004",
        title="Machine Learning Engineer",
        required_skills=["Python", "Machine Learning", "TensorFlow", "SQL"],
        preferred_skills=["PyTorch", "MLOps", "Docker"],
        min_years_experience=3.0,
        experience_level=ExperienceLevel.MID,
        min_education=EducationLevel.MASTERS,
        location="Boston, MA",
        remote_ok=True,
        salary_min=120000,
        salary_max=160000,
        required_certifications=[],
        preferred_languages=["English"],
        industry="AI",
    ),
    "job-005": Job(
        id="job-005",
        title="Backend Engineer (FinTech)",
        required_skills=["Python", "Django", "PostgreSQL", "Docker"],
        preferred_skills=["FastAPI", "Redis", "Celery", "AWS"],
        min_years_experience=4.0,
        experience_level=ExperienceLevel.SENIOR,
        min_education=EducationLevel.BACHELORS,
        location="New York, NY",
        remote_ok=True,
        salary_min=130000,
        salary_max=170000,
        required_certifications=[],
        preferred_languages=["English"],
        industry="fintech",
    ),
}


# ---------------------------------------------------------------------------
# Scoring Weights
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "skills": 0.35,
    "experience": 0.20,
    "education": 0.10,
    "location": 0.10,
    "salary": 0.10,
    "certifications": 0.15,
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _normalize_skill(skill: str) -> str:
    """Normalize a skill name for comparison."""
    return skill.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def _skill_overlap(candidate_skills: list[str], job_skills: list[str]) -> float:
    """Calculate the fraction of job skills the candidate possesses."""
    if not job_skills:
        return 1.0
    normalized_candidate = {_normalize_skill(s) for s in candidate_skills}
    normalized_job = {_normalize_skill(s) for s in job_skills}
    matches = normalized_candidate & normalized_job
    return len(matches) / len(normalized_job)


def _experience_score(years: float, min_years: float, level: ExperienceLevel) -> float:
    """Score based on years of experience relative to requirement."""
    if min_years <= 0:
        return 1.0
    if years >= min_years * 1.5:
        return 1.0
    if years >= min_years:
        return 0.85
    if years >= min_years * 0.75:
        return 0.60
    if years >= min_years * 0.5:
        return 0.35
    return 0.10


def _education_score(candidate_edu: EducationLevel, min_edu: EducationLevel) -> float:
    """Score based on education level relative to requirement."""
    edu_rank: dict[EducationLevel, int] = {
        EducationLevel.HIGH_SCHOOL: 0,
        EducationLevel.ASSOCIATE: 1,
        EducationLevel.BACHELORS: 2,
        EducationLevel.MASTERS: 3,
        EducationLevel.PHD: 4,
    }
    candidate_rank = edu_rank.get(candidate_edu, 0)
    min_rank = edu_rank.get(min_edu, 0)
    if candidate_rank >= min_rank:
        return 1.0
    if candidate_rank == min_rank - 1:
        return 0.60
    return 0.20


def _location_score(candidate_location: str, job_location: str, remote_ok: bool, remote_pref: bool) -> float:
    """Score based on location compatibility."""
    cand_loc = candidate_location.strip().lower()
    job_loc = job_location.strip().lower()
    if cand_loc == "remote" or (remote_ok and remote_pref):
        return 1.0
    if cand_loc == job_loc:
        return 1.0
    # Same state/region heuristic (very rough)
    if cand_loc.split(",")[-1].strip() == job_loc.split(",")[-1].strip():
        return 0.70
    if remote_ok:
        return 0.50
    return 0.10


def _salary_score(desired: int | None, salary_min: int | None, salary_max: int | None) -> float:
    """Score based on salary alignment."""
    if desired is None or salary_min is None or salary_max is None:
        return 0.50  # Neutral when data is missing
    if salary_min <= desired <= salary_max:
        return 1.0
    if desired < salary_min:
        return 0.80  # Candidate expects less — good for employer
    if desired <= salary_max * 1.15:
        return 0.60
    if desired <= salary_max * 1.30:
        return 0.35
    return 0.10


def _certification_score(candidate_certs: list[str], required_certs: list[str]) -> float:
    """Score based on required certifications held."""
    if not required_certs:
        return 1.0
    normalized_candidate = {_normalize_skill(c) for c in candidate_certs}
    normalized_required = {_normalize_skill(c) for c in required_certs}
    matches = normalized_candidate & normalized_required
    return len(matches) / len(normalized_required)


# ---------------------------------------------------------------------------
# Core Matching Functions
# ---------------------------------------------------------------------------

def calculate_match_score(candidate: Candidate, job: Job) -> MatchResult:
    """Calculate a weighted match score between a candidate and a job.

    Uses a multi-factor weighted scoring algorithm:
    - Skills overlap (35%): Required + preferred skill coverage
    - Experience (20%): Years of experience vs. minimum
    - Education (10%): Education level vs. minimum requirement
    - Location (10%): Geographic/remote compatibility
    - Salary (10%): Desired salary vs. budget range
    - Certifications (15%): Required certifications held

    Args:
        candidate: The candidate to evaluate.
        job: The job to match against.

    Returns:
        MatchResult with overall score (0-100) and per-factor breakdown.
    """
    # Skills: 70% weight on required, 30% on preferred
    required_score = _skill_overlap(candidate.skills, job.required_skills)
    preferred_score = _skill_overlap(candidate.skills, job.preferred_skills)
    skill_score = 0.70 * required_score + 0.30 * preferred_score

    # Experience
    exp_score = _experience_score(
        candidate.years_experience,
        job.min_years_experience,
        candidate.experience_level,
    )

    # Education
    edu_score = _education_score(candidate.education, job.min_education)

    # Location
    loc_score = _location_score(
        candidate.location,
        job.location,
        job.remote_ok,
        candidate.remote_preference,
    )

    # Salary
    sal_score = _salary_score(
        candidate.desired_salary,
        job.salary_min,
        job.salary_max,
    )

    # Certifications
    cert_score = _certification_score(candidate.certifications, job.required_certifications)

    # Weighted overall score (0-100 scale)
    overall = (
        WEIGHTS["skills"] * skill_score
        + WEIGHTS["experience"] * exp_score
        + WEIGHTS["education"] * edu_score
        + WEIGHTS["location"] * loc_score
        + WEIGHTS["salary"] * sal_score
        + WEIGHTS["certifications"] * cert_score
    ) * 100.0

    breakdown = {
        "skills": round(skill_score * 100, 2),
        "experience": round(exp_score * 100, 2),
        "education": round(edu_score * 100, 2),
        "location": round(loc_score * 100, 2),
        "salary": round(sal_score * 100, 2),
        "certifications": round(cert_score * 100, 2),
    }

    return MatchResult(
        candidate=candidate,
        job=job,
        overall_score=round(overall, 2),
        skill_score=round(skill_score * 100, 2),
        experience_score=round(exp_score * 100, 2),
        education_score=round(edu_score * 100, 2),
        location_score=round(loc_score * 100, 2),
        salary_score=round(sal_score * 100, 2),
        certification_score=round(cert_score * 100, 2),
        breakdown=breakdown,
    )


def match_candidates(job_id: str, candidates: list[Candidate]) -> list[MatchResult]:
    """Match and rank candidates for a given job.

    Args:
        job_id: The ID of the job to match against.
        candidates: List of candidate profiles to evaluate.

    Returns:
        List of MatchResult sorted by overall_score descending (best match first).

    Raises:
        ValueError: If the job_id is not found in the mock job database.
    """
    if job_id not in MOCK_JOBS:
        available = ", ".join(MOCK_JOBS.keys())
        raise ValueError(f"Job '{job_id}' not found. Available jobs: {available}")

    job = MOCK_JOBS[job_id]
    results: list[MatchResult] = []

    for candidate in candidates:
        result = calculate_match_score(candidate, job)
        results.append(result)

    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Demo / CLI
# ---------------------------------------------------------------------------

def _format_result(result: MatchResult, rank: int) -> str:
    """Format a MatchResult for display."""
    lines = [
        f"  #{rank} {result.candidate.name} (ID: {result.candidate.id})",
        f"     Overall Score: {result.overall_score:.1f}/100",
        f"     Skills: {result.skill_score:.1f} | Experience: {result.experience_score:.1f} | "
        f"Education: {result.education_score:.1f}",
        f"     Location: {result.location_score:.1f} | Salary: {result.salary_score:.1f} | "
        f"Certifications: {result.certification_score:.1f}",
    ]
    return "\n".join(lines)


def main() -> None:
    """Run a demo matching all mock candidates against a sample job."""
    job_id = "job-001"
    job = MOCK_JOBS[job_id]

    print(f"Candidate Matching Results for: {job.title} ({job.id})")
    print(f"Location: {job.location} | Remote OK: {job.remote_ok}")
    print(f"Required Skills: {', '.join(job.required_skills)}")
    print(f"Preferred Skills: {', '.join(job.preferred_skills)}")
    print(f"Min Experience: {job.min_years_experience} years | Min Education: {job.min_education.value}")
    print(f"Salary Range: ${job.salary_min:,} - ${job.salary_max:,}")
    print("=" * 70)

    results = match_candidates(job_id, MOCK_CANDIDATES)

    for rank, result in enumerate(results, start=1):
        print(_format_result(result, rank))
        print()


if __name__ == "__main__":
    main()
