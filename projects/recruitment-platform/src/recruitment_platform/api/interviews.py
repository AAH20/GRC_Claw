"""
Interviews API endpoints for the recruitment platform.

Provides:
  GET  /interviews  — list interviews with pagination, date/status filtering
  POST /interviews  — schedule a new interview with validation
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/interviews", tags=["interviews"])

# ---------------------------------------------------------------------------
# Mock data store (in-memory for demonstration)
# ---------------------------------------------------------------------------

MOCK_INTERVIEWS = [
    {
        "id": "int_001",
        "candidate_id": "cand_101",
        "candidate_name": "Alice Johnson",
        "job_id": "job_201",
        "job_title": "Senior Backend Engineer",
        "interviewer_id": "usr_301",
        "interviewer_name": "Bob Smith",
        "scheduled_at": "2026-10-05T10:00:00Z",
        "duration_minutes": 60,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Google Meet",
        "notes": "Focus on system design and Python expertise.",
    },
    {
        "id": "int_002",
        "candidate_id": "cand_102",
        "candidate_name": "Carlos Rivera",
        "job_id": "job_202",
        "job_title": "Frontend Developer",
        "interviewer_id": "usr_302",
        "interviewer_name": "Diana Lee",
        "scheduled_at": "2026-10-06T14:30:00Z",
        "duration_minutes": 45,
        "status": "completed",
        "interview_type": "technical",
        "location": "Zoom",
        "notes": "React and TypeScript deep-dive.",
    },
    {
        "id": "int_003",
        "candidate_id": "cand_103",
        "candidate_name": "Emma Chen",
        "job_id": "job_201",
        "job_title": "Senior Backend Engineer",
        "interviewer_id": "usr_303",
        "interviewer_name": "Frank Wang",
        "scheduled_at": "2026-10-07T09:00:00Z",
        "duration_minutes": 30,
        "status": "scheduled",
        "interview_type": "hr",
        "location": "Phone",
        "notes": "Culture fit and compensation discussion.",
    },
    {
        "id": "int_004",
        "candidate_id": "cand_104",
        "candidate_name": "David Okafor",
        "job_id": "job_203",
        "job_title": "DevOps Engineer",
        "interviewer_id": "usr_301",
        "interviewer_name": "Bob Smith",
        "scheduled_at": "2026-10-03T16:00:00Z",
        "duration_minutes": 60,
        "status": "cancelled",
        "interview_type": "technical",
        "location": "Microsoft Teams",
        "notes": "Candidate requested reschedule.",
    },
    {
        "id": "int_005",
        "candidate_id": "cand_105",
        "candidate_name": "Fatima Al-Hassan",
        "job_id": "job_202",
        "job_title": "Frontend Developer",
        "interviewer_id": "usr_302",
        "interviewer_name": "Diana Lee",
        "scheduled_at": "2026-10-08T11:00:00Z",
        "duration_minutes": 45,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Google Meet",
        "notes": "UI/UX sensibility and CSS architecture.",
    },
    {
        "id": "int_006",
        "candidate_id": "cand_106",
        "candidate_name": "George Petrov",
        "job_id": "job_204",
        "job_title": "Data Scientist",
        "interviewer_id": "usr_304",
        "interviewer_name": "Grace Kim",
        "scheduled_at": "2026-10-09T13:00:00Z",
        "duration_minutes": 60,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Zoom",
        "notes": "ML model evaluation and statistics.",
    },
    {
        "id": "int_007",
        "candidate_id": "cand_107",
        "candidate_name": "Hannah Schmidt",
        "job_id": "job_203",
        "job_title": "DevOps Engineer",
        "interviewer_id": "usr_303",
        "interviewer_name": "Frank Wang",
        "scheduled_at": "2026-10-10T10:30:00Z",
        "duration_minutes": 45,
        "status": "completed",
        "interview_type": "hr",
        "location": "Phone",
        "notes": "Final round — offer extended.",
    },
    {
        "id": "int_008",
        "candidate_id": "cand_108",
        "candidate_name": "Ivan Novak",
        "job_id": "job_201",
        "job_title": "Senior Backend Engineer",
        "interviewer_id": "usr_301",
        "interviewer_name": "Bob Smith",
        "scheduled_at": "2026-10-11T15:00:00Z",
        "duration_minutes": 60,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Google Meet",
        "notes": "Distributed systems and concurrency patterns.",
    },
    {
        "id": "int_009",
        "candidate_id": "cand_109",
        "candidate_name": "Julia Moreau",
        "job_id": "job_204",
        "job_title": "Data Scientist",
        "interviewer_id": "usr_304",
        "interviewer_name": "Grace Kim",
        "scheduled_at": "2026-10-12T09:30:00Z",
        "duration_minutes": 45,
        "status": "no_show",
        "interview_type": "technical",
        "location": "Zoom",
        "notes": "Candidate did not attend.",
    },
    {
        "id": "int_010",
        "candidate_id": "cand_110",
        "candidate_name": "Kevin O'Brien",
        "job_id": "job_202",
        "job_title": "Frontend Developer",
        "interviewer_id": "usr_302",
        "interviewer_name": "Diana Lee",
        "scheduled_at": "2026-10-13T14:00:00Z",
        "duration_minutes": 60,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Microsoft Teams",
        "notes": "Full-stack JavaScript assessment.",
    },
    {
        "id": "int_011",
        "candidate_id": "cand_111",
        "candidate_name": "Lina Johansson",
        "job_id": "job_203",
        "job_title": "DevOps Engineer",
        "interviewer_id": "usr_303",
        "interviewer_name": "Frank Wang",
        "scheduled_at": "2026-10-14T11:30:00Z",
        "duration_minutes": 45,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Google Meet",
        "notes": "Kubernetes and CI/CD pipeline review.",
    },
    {
        "id": "int_012",
        "candidate_id": "cand_112",
        "candidate_name": "Mohammed Ali",
        "job_id": "job_204",
        "job_title": "Data Scientist",
        "interviewer_id": "usr_304",
        "interviewer_name": "Grace Kim",
        "scheduled_at": "2026-10-15T10:00:00Z",
        "duration_minutes": 60,
        "status": "scheduled",
        "interview_type": "technical",
        "location": "Zoom",
        "notes": "A/B testing and experimentation design.",
    },
]

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class InterviewCreate(BaseModel):
    """Payload for scheduling a new interview."""

    candidate_id: str = Field(..., min_length=1, description="ID of the candidate")
    job_id: str = Field(..., min_length=1, description="ID of the job requisition")
    interviewer_id: str = Field(..., min_length=1, description="ID of the interviewer")
    scheduled_at: str = Field(..., description="ISO 8601 datetime string")
    duration_minutes: int = Field(default=60, ge=15, le=240)
    interview_type: str = Field(default="technical", regex="^(technical|hr|behavioral|phone_screen)$")
    location: str = Field(default="Google Meet", max_length=200)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v: str) -> str:
        """Ensure the datetime is parseable and in the future."""
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("scheduled_at must be a valid ISO 8601 datetime string")
        if dt < datetime.now(dt.tzinfo):
            raise ValueError("scheduled_at must be in the future")
        return v


class InterviewResponse(BaseModel):
    """Response model for a single interview."""

    id: str
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str
    interviewer_id: str
    interviewer_name: str
    scheduled_at: str
    duration_minutes: int
    status: str
    interview_type: str
    location: str
    notes: Optional[str] = None


class InterviewListResponse(BaseModel):
    """Paginated list response."""

    data: list[InterviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(
        default=None,
        regex="^(scheduled|completed|cancelled|no_show)$",
        description="Filter by interview status",
    ),
    date_from: Optional[str] = Query(
        default=None,
        description="Filter interviews on or after this date (ISO 8601)",
    ),
    date_to: Optional[str] = Query(
        default=None,
        description="Filter interviews on or before this date (ISO 8601)",
    ),
) -> dict:
    """
    List interviews with optional filtering by status and date range,
    plus pagination.
    """
    filtered = MOCK_INTERVIEWS.copy()

    # Status filter
    if status:
        filtered = [i for i in filtered if i["status"] == status]

    # Date range filter
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            filtered = [
                i for i in filtered
                if datetime.fromisoformat(i["scheduled_at"].replace("Z", "+00:00")) >= dt_from
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_from must be a valid ISO 8601 datetime string",
            )

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            filtered = [
                i for i in filtered
                if datetime.fromisoformat(i["scheduled_at"].replace("Z", "+00:00")) <= dt_to
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_to must be a valid ISO 8601 datetime string",
            )

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)

    # Clamp page to valid range
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(payload: InterviewCreate) -> dict:
    """
    Schedule a new interview.

    Validates the payload and returns the created interview object.
    """
    # Generate a new interview ID
    new_id = f"int_{len(MOCK_INTERVIEWS) + 1:03d}"

    # Look up names from mock data (in production, query the database)
    candidate_name = "Unknown Candidate"
    job_title = "Unknown Position"
    interviewer_name = "Unknown Interviewer"

    for interview in MOCK_INTERVIEWS:
        if interview["candidate_id"] == payload.candidate_id:
            candidate_name = interview["candidate_name"]
        if interview["job_id"] == payload.job_id:
            job_title = interview["job_title"]
        if interview["interviewer_id"] == payload.interviewer_id:
            interviewer_name = interview["interviewer_name"]

    new_interview = {
        "id": new_id,
        "candidate_id": payload.candidate_id,
        "candidate_name": candidate_name,
        "job_id": payload.job_id,
        "job_title": job_title,
        "interviewer_id": payload.interviewer_id,
        "interviewer_name": interviewer_name,
        "scheduled_at": payload.scheduled_at,
        "duration_minutes": payload.duration_minutes,
        "status": "scheduled",
        "interview_type": payload.interview_type,
        "location": payload.location,
        "notes": payload.notes,
    }

    # In production: persist to database here
    MOCK_INTERVIEWS.append(new_interview)

    return new_interview
