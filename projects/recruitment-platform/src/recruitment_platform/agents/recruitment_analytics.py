"""Recruitment Analytics Agent.

Provides analytics functions for recruitment metrics including
time-to-hire and cost-per-hire calculations using mock data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

@dataclass
class JobPosting:
    """Represents a job posting with relevant dates and costs."""

    job_id: str
    title: str
    department: str
    posted_date: date
    hired_date: Optional[date] = None
    recruiter_cost: float = 0.0
    job_board_cost: float = 0.0
    referral_bonus: float = 0.0
    interview_cost: float = 0.0
    onboarding_cost: float = 0.0
    other_costs: float = 0.0


# Mock database of job postings
_MOCK_JOBS: Dict[str, JobPosting] = {
    "JOB-001": JobPosting(
        job_id="JOB-001",
        title="Senior Software Engineer",
        department="Engineering",
        posted_date=date(2025, 1, 15),
        hired_date=date(2025, 3, 10),
        recruiter_cost=3500.00,
        job_board_cost=450.00,
        referral_bonus=2500.00,
        interview_cost=800.00,
        onboarding_cost=1200.00,
        other_costs=300.00,
    ),
    "JOB-002": JobPosting(
        job_id="JOB-002",
        title="Product Manager",
        department="Product",
        posted_date=date(2025, 2, 1),
        hired_date=date(2025, 4, 15),
        recruiter_cost=4200.00,
        job_board_cost=600.00,
        referral_bonus=3000.00,
        interview_cost=1100.00,
        onboarding_cost=1500.00,
        other_costs=450.00,
    ),
    "JOB-003": JobPosting(
        job_id="JOB-003",
        title="UX Designer",
        department="Design",
        posted_date=date(2025, 3, 10),
        hired_date=date(2025, 5, 5),
        recruiter_cost=2800.00,
        job_board_cost=350.00,
        referral_bonus=2000.00,
        interview_cost=600.00,
        onboarding_cost=900.00,
        other_costs=200.00,
    ),
    "JOB-004": JobPosting(
        job_id="JOB-004",
        title="Data Analyst",
        department="Analytics",
        posted_date=date(2025, 4, 1),
        hired_date=None,  # Not yet hired
        recruiter_cost=2200.00,
        job_board_cost=300.00,
        referral_bonus=0.00,
        interview_cost=400.00,
        onboarding_cost=0.00,
        other_costs=150.00,
    ),
    "JOB-005": JobPosting(
        job_id="JOB-005",
        title="DevOps Engineer",
        department="Engineering",
        posted_date=date(2025, 1, 20),
        hired_date=date(2025, 2, 28),
        recruiter_cost=3200.00,
        job_board_cost=500.00,
        referral_bonus=2500.00,
        interview_cost=750.00,
        onboarding_cost=1100.00,
        other_costs=250.00,
    ),
}


# ---------------------------------------------------------------------------
# Analytics Functions
# ---------------------------------------------------------------------------

def calculate_time_to_hire(job_id: str) -> Optional[int]:
    """Calculate the number of days from job posting to hire.

    Args:
        job_id: The unique identifier for the job posting.

    Returns:
        Number of days between posted_date and hired_date, or None if
        the job has not been filled yet or the job_id is not found.

    Raises:
        ValueError: If job_id is empty or None.
    """
    if not job_id:
        raise ValueError("job_id must be a non-empty string")

    job = _MOCK_JOBS.get(job_id)
    if job is None:
        return None

    if job.hired_date is None:
        return None

    delta: timedelta = job.hired_date - job.posted_date
    return delta.days


def calculate_cost_per_hire(job_id: str) -> Optional[float]:
    """Calculate the total recruitment cost for a filled position.

    Args:
        job_id: The unique identifier for the job posting.

    Returns:
        Total recruitment cost as a float, or None if the job has not
        been filled yet or the job_id is not found.

    Raises:
        ValueError: If job_id is empty or None.
    """
    if not job_id:
        raise ValueError("job_id must be a non-empty string")

    job = _MOCK_JOBS.get(job_id)
    if job is None:
        return None

    if job.hired_date is None:
        return None

    total_cost: float = (
        job.recruiter_cost
        + job.job_board_cost
        + job.referral_bonus
        + job.interview_cost
        + job.onboarding_cost
        + job.other_costs
    )
    return round(total_cost, 2)


# ---------------------------------------------------------------------------
# Additional Utility Functions
# ---------------------------------------------------------------------------

def get_job_details(job_id: str) -> Optional[Dict[str, object]]:
    """Get full details of a job posting.

    Args:
        job_id: The unique identifier for the job posting.

    Returns:
        Dictionary with job details, or None if not found.
    """
    job = _MOCK_JOBS.get(job_id)
    if job is None:
        return None

    return {
        "job_id": job.job_id,
        "title": job.title,
        "department": job.department,
        "posted_date": job.posted_date.isoformat(),
        "hired_date": job.hired_date.isoformat() if job.hired_date else None,
        "recruiter_cost": job.recruiter_cost,
        "job_board_cost": job.job_board_cost,
        "referral_bonus": job.referral_bonus,
        "interview_cost": job.interview_cost,
        "onboarding_cost": job.onboarding_cost,
        "other_costs": job.other_costs,
    }


def list_all_jobs() -> List[str]:
    """List all available job IDs in the mock database.

    Returns:
        List of job ID strings.
    """
    return list(_MOCK_JOBS.keys())


# ---------------------------------------------------------------------------
# Main entry point for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Recruitment Analytics Agent - Demo")
    print("=" * 60)

    for jid in list_all_jobs():
        tth = calculate_time_to_hire(jid)
        cph = calculate_cost_per_hire(jid)
        details = get_job_details(jid)
        print(f"\nJob: {jid} — {details['title']}")
        print(f"  Time to hire: {tth if tth is not None else 'Not yet hired'} days")
        print(f"  Cost per hire: ${cph if cph is not None else 'N/A'}")

    print("\n" + "=" * 60)
