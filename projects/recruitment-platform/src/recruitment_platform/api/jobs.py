"""
Jobs API endpoints for the recruitment platform.

Provides:
  GET  /jobs  — list jobs with pagination and filtering
  POST /jobs  — create a new job posting with validation
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/jobs", tags=["jobs"])

# ---------------------------------------------------------------------------
# Mock data store (in-memory; replace with DB in production)
# ---------------------------------------------------------------------------

MOCK_JOBS = [
    {
        "id": 1,
        "title": "Senior Backend Engineer",
        "department": "Engineering",
        "location": "Remote",
        "status": "open",
        "description": "Design and build scalable backend services.",
        "requirements": "5+ years Python, FastAPI, PostgreSQL, Redis.",
        "salary_min": 120000,
        "salary_max": 160000,
        "posted_at": "2026-09-15T09:00:00Z",
        "closing_date": "2026-11-15",
    },
    {
        "id": 2,
        "title": "Frontend Developer",
        "department": "Engineering",
        "location": "Cairo, Egypt",
        "status": "open",
        "description": "Build responsive web interfaces with React and TypeScript.",
        "requirements": "3+ years React, TypeScript, CSS-in-JS.",
        "salary_min": 80000,
        "salary_max": 110000,
        "posted_at": "2026-09-20T10:30:00Z",
        "closing_date": "2026-10-30",
    },
    {
        "id": 3,
        "title": "Product Manager",
        "department": "Product",
        "location": "Dubai, UAE",
        "status": "open",
        "description": "Own product roadmap and coordinate cross-functional teams.",
        "requirements": "4+ years product management, Agile, strong communication.",
        "salary_min": 130000,
        "salary_max": 170000,
        "posted_at": "2026-09-10T08:00:00Z",
        "closing_date": "2026-10-25",
    },
    {
        "id": 4,
        "title": "Data Analyst",
        "department": "Data",
        "location": "Remote",
        "status": "draft",
        "description": "Analyze business data and produce actionable insights.",
        "requirements": "SQL, Python, Tableau, statistics background.",
        "salary_min": 70000,
        "salary_max": 95000,
        "posted_at": "2026-10-01T14:00:00Z",
        "closing_date": "2026-12-01",
    },
    {
        "id": 5,
        "title": "DevOps Engineer",
        "department": "Engineering",
        "location": "Riyadh, Saudi Arabia",
        "status": "open",
        "description": "Manage CI/CD pipelines, Kubernetes clusters, and cloud infra.",
        "requirements": "AWS/GCP, Terraform, Docker, Kubernetes, CI/CD.",
        "salary_min": 110000,
        "salary_max": 150000,
        "posted_at": "2026-09-25T11:00:00Z",
        "closing_date": "2026-11-10",
    },
    {
        "id": 6,
        "title": "UX Designer",
        "department": "Design",
        "location": "Remote",
        "status": "closed",
        "description": "Design user-centered interfaces and conduct usability testing.",
        "requirements": "Figma, user research, prototyping, design systems.",
        "salary_min": 75000,
        "salary_max": 100000,
        "posted_at": "2026-08-01T09:00:00Z",
        "closing_date": "2026-09-30",
    },
    {
        "id": 7,
        "title": "HR Specialist",
        "department": "Human Resources",
        "location": "Cairo, Egypt",
        "status": "open",
        "description": "Manage recruitment cycles, onboarding, and employee relations.",
        "requirements": "3+ years HR, labor law knowledge, ATS experience.",
        "salary_min": 60000,
        "salary_max": 85000,
        "posted_at": "2026-09-28T13:00:00Z",
        "closing_date": "2026-10-28",
    },
    {
        "id": 8,
        "title": "Machine Learning Engineer",
        "department": "Engineering",
        "location": "Remote",
        "status": "open",
        "description": "Build and deploy ML models for recommendation systems.",
        "requirements": "Python, PyTorch/TensorFlow, MLOps, 4+ years experience.",
        "salary_min": 140000,
        "salary_max": 190000,
        "posted_at": "2026-10-02T07:00:00Z",
        "closing_date": "2026-12-15",
    },
    {
        "id": 9,
        "title": "QA Engineer",
        "department": "Engineering",
        "location": "Dubai, UAE",
        "status": "draft",
        "description": "Develop automated test suites and ensure product quality.",
        "requirements": "Selenium, Cypress, Python/JS, CI integration.",
        "salary_min": 65000,
        "salary_max": 90000,
        "posted_at": "2026-09-22T16:00:00Z",
        "closing_date": "2026-11-20",
    },
    {
        "id": 10,
        "title": "Technical Writer",
        "department": "Product",
        "location": "Remote",
        "status": "open",
        "description": "Create clear documentation for APIs, SDKs, and user guides.",
        "requirements": "Excellent English, Markdown, API docs, Git.",
        "salary_min": 55000,
        "salary_max": 80000,
        "posted_at": "2026-09-18T12:00:00Z",
        "closing_date": "2026-10-18",
    },
    {
        "id": 11,
        "title": "Security Engineer",
        "department": "Engineering",
        "location": "Riyadh, Saudi Arabia",
        "status": "open",
        "description": "Conduct security audits, penetration testing, and incident response.",
        "requirements": "OSCP/CISSP, network security, cloud security, 5+ years.",
        "salary_min": 130000,
        "salary_max": 175000,
        "posted_at": "2026-09-12T10:00:00Z",
        "closing_date": "2026-11-30",
    },
    {
        "id": 12,
        "title": "Marketing Manager",
        "department": "Marketing",
        "location": "Cairo, Egypt",
        "status": "closed",
        "description": "Lead digital marketing campaigns and brand strategy.",
        "requirements": "5+ years marketing, SEO/SEM, analytics, team leadership.",
        "salary_min": 90000,
        "salary_max": 120000,
        "posted_at": "2026-07-15T09:00:00Z",
        "closing_date": "2026-09-15",
    },
]

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

JobStatus = Literal["draft", "open", "closed"]


class JobCreate(BaseModel):
    """Payload for creating a new job posting."""

    title: str = Field(..., min_length=3, max_length=200)
    department: str = Field(..., min_length=2, max_length=100)
    location: str = Field(..., min_length=2, max_length=150)
    status: JobStatus = "draft"
    description: str = Field(..., min_length=10, max_length=5000)
    requirements: str = Field(..., min_length=10, max_length=5000)
    salary_min: int = Field(..., ge=0, le=10_000_000)
    salary_max: int = Field(..., ge=0, le=10_000_000)
    closing_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Closing date in YYYY-MM-DD format",
    )

    @field_validator("salary_max")
    @classmethod
    def salary_range_valid(cls, v: int, info) -> int:
        """Ensure salary_max >= salary_min."""
        if "salary_min" in info.data and v < info.data["salary_min"]:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return v


class JobResponse(BaseModel):
    """Job representation returned by the API."""

    id: int
    title: str
    department: str
    location: str
    status: JobStatus
    description: str
    requirements: str
    salary_min: int
    salary_max: int
    posted_at: str
    closing_date: Optional[str] = None


class JobListResponse(BaseModel):
    """Paginated list response."""

    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(None, description="Filter by department"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
) -> dict:
    """
    List job postings with pagination and optional filtering.

    Filters are case-insensitive partial matches for department and location.
    """
    filtered = MOCK_JOBS.copy()

    if department:
        dept_lower = department.lower()
        filtered = [j for j in filtered if dept_lower in j["department"].lower()]

    if location:
        loc_lower = location.lower()
        filtered = [j for j in filtered if loc_lower in j["location"].lower()]

    if status:
        filtered = [j for j in filtered if j["status"] == status]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total else 1

    # Clamp page to valid range
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate) -> dict:
    """
    Create a new job posting.

    Returns the created job with an auto-generated ID and timestamp.
    """
    new_id = max((j["id"] for j in MOCK_JOBS), default=0) + 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_job = {
        "id": new_id,
        "title": payload.title,
        "department": payload.department,
        "location": payload.location,
        "status": payload.status,
        "description": payload.description,
        "requirements": payload.requirements,
        "salary_min": payload.salary_min,
        "salary_max": payload.salary_max,
        "posted_at": now,
        "closing_date": payload.closing_date,
    }

    MOCK_JOBS.append(new_job)

    return new_job
