"""
Assessments API Endpoints

Provides CRUD operations for candidate assessments in the recruitment platform.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/assessments", tags=["assessments"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class AssessmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    assessment_type: str = Field(..., pattern="^(technical|behavioral|cognitive|personality|coding)$")
    duration_minutes: int = Field(..., ge=5, le=480)
    passing_score: float = Field(default=70.0, ge=0, le=100)
    max_attempts: int = Field(default=1, ge=1, le=10)
    is_active: bool = True


class AssessmentCreate(AssessmentBase):
    pass


class AssessmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    assessment_type: Optional[str] = Field(None, pattern="^(technical|behavioral|cognitive|personality|coding)$")
    duration_minutes: Optional[int] = Field(None, ge=5, le=480)
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class AssessmentResponse(AssessmentBase):
    id: str
    created_at: str
    updated_at: str
    question_count: int
    average_score: Optional[float]
    total_attempts: int

    class Config:
        from_attributes = True


class PaginatedAssessmentResponse(BaseModel):
    items: list[AssessmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Mock Data Store ─────────────────────────────────────────────────────────

MOCK_ASSESSMENTS = [
    {
        "id": "assess_001",
        "title": "Python Fundamentals",
        "description": "Core Python programming concepts including data structures, OOP, and error handling.",
        "assessment_type": "technical",
        "duration_minutes": 60,
        "passing_score": 70.0,
        "max_attempts": 3,
        "is_active": True,
        "created_at": "2025-09-15T10:30:00Z",
        "updated_at": "2025-10-01T14:22:00Z",
        "question_count": 25,
        "average_score": 78.5,
        "total_attempts": 142,
    },
    {
        "id": "assess_002",
        "title": "System Design Basics",
        "description": "Evaluate understanding of distributed systems, scalability, and architectural patterns.",
        "assessment_type": "technical",
        "duration_minutes": 90,
        "passing_score": 75.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-08-20T09:00:00Z",
        "updated_at": "2025-09-28T11:45:00Z",
        "question_count": 15,
        "average_score": 65.3,
        "total_attempts": 89,
    },
    {
        "id": "assess_003",
        "title": "Behavioral Competency",
        "description": "Situational judgment and behavioral alignment with company values.",
        "assessment_type": "behavioral",
        "duration_minutes": 30,
        "passing_score": 60.0,
        "max_attempts": 1,
        "is_active": True,
        "created_at": "2025-07-10T08:00:00Z",
        "updated_at": "2025-09-15T16:30:00Z",
        "question_count": 20,
        "average_score": 82.1,
        "total_attempts": 310,
    },
    {
        "id": "assess_004",
        "title": "Cognitive Ability Test",
        "description": "Logical reasoning, numerical ability, and verbal comprehension assessment.",
        "assessment_type": "cognitive",
        "duration_minutes": 45,
        "passing_score": 65.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-06-05T12:00:00Z",
        "updated_at": "2025-08-20T10:00:00Z",
        "question_count": 40,
        "average_score": 71.8,
        "total_attempts": 520,
    },
    {
        "id": "assess_005",
        "title": "Full-Stack Coding Challenge",
        "description": "Hands-on coding assessment covering frontend and backend development tasks.",
        "assessment_type": "coding",
        "duration_minutes": 120,
        "passing_score": 70.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-09-01T14:00:00Z",
        "updated_at": "2025-10-02T09:15:00Z",
        "question_count": 8,
        "average_score": 68.9,
        "total_attempts": 67,
    },
    {
        "id": "assess_006",
        "title": "Data Structures & Algorithms",
        "description": "Advanced problem-solving with focus on time and space complexity analysis.",
        "assessment_type": "technical",
        "duration_minutes": 75,
        "passing_score": 72.0,
        "max_attempts": 3,
        "is_active": True,
        "created_at": "2025-08-15T11:00:00Z",
        "updated_at": "2025-09-20T13:30:00Z",
        "question_count": 12,
        "average_score": 63.4,
        "total_attempts": 198,
    },
    {
        "id": "assess_007",
        "title": "Leadership Personality Profile",
        "description": "Big Five personality assessment tailored for leadership roles.",
        "assessment_type": "personality",
        "duration_minutes": 25,
        "passing_score": 50.0,
        "max_attempts": 1,
        "is_active": False,
        "created_at": "2025-05-20T10:00:00Z",
        "updated_at": "2025-07-30T15:00:00Z",
        "question_count": 50,
        "average_score": 74.2,
        "total_attempts": 45,
    },
    {
        "id": "assess_008",
        "title": "JavaScript Advanced Concepts",
        "description": "Closures, prototypes, async patterns, and modern ES6+ features.",
        "assessment_type": "technical",
        "duration_minutes": 55,
        "passing_score": 70.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-09-10T09:30:00Z",
        "updated_at": "2025-10-01T08:45:00Z",
        "question_count": 30,
        "average_score": 76.0,
        "total_attempts": 112,
    },
    {
        "id": "assess_009",
        "title": "SQL & Database Design",
        "description": "Query optimization, normalization, indexing, and schema design.",
        "assessment_type": "technical",
        "duration_minutes": 50,
        "passing_score": 68.0,
        "max_attempts": 3,
        "is_active": True,
        "created_at": "2025-07-25T13:00:00Z",
        "updated_at": "2025-09-05T10:20:00Z",
        "question_count": 22,
        "average_score": 70.5,
        "total_attempts": 156,
    },
    {
        "id": "assess_010",
        "title": "DevOps & Cloud Fundamentals",
        "description": "CI/CD pipelines, containerization, IaC, and cloud service models.",
        "assessment_type": "technical",
        "duration_minutes": 65,
        "passing_score": 70.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-08-30T10:00:00Z",
        "updated_at": "2025-09-25T14:00:00Z",
        "question_count": 18,
        "average_score": 66.7,
        "total_attempts": 78,
    },
    {
        "id": "assess_011",
        "title": "Communication Skills Evaluation",
        "description": "Written and verbal communication effectiveness in professional contexts.",
        "assessment_type": "behavioral",
        "duration_minutes": 35,
        "passing_score": 60.0,
        "max_attempts": 1,
        "is_active": True,
        "created_at": "2025-06-15T08:30:00Z",
        "updated_at": "2025-08-10T11:00:00Z",
        "question_count": 15,
        "average_score": 80.3,
        "total_attempts": 234,
    },
    {
        "id": "assess_012",
        "title": "React.js Practical Assessment",
        "description": "Component lifecycle, hooks, state management, and performance optimization.",
        "assessment_type": "coding",
        "duration_minutes": 100,
        "passing_score": 72.0,
        "max_attempts": 2,
        "is_active": True,
        "created_at": "2025-09-05T15:00:00Z",
        "updated_at": "2025-10-02T12:00:00Z",
        "question_count": 6,
        "average_score": 69.8,
        "total_attempts": 54,
    },
]


# ─── Helper Functions ────────────────────────────────────────────────────────

def _get_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id() -> str:
    """Generate a new assessment ID."""
    return f"assess_{len(MOCK_ASSESSMENTS) + 1:03d}"


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedAssessmentResponse)
async def list_assessments(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    assessment_type: Optional[str] = Query(None, pattern="^(technical|behavioral|cognitive|personality|coding)$"),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by title or description"),
):
    """
    List all assessments with pagination and optional filtering.
    """
    filtered = MOCK_ASSESSMENTS.copy()

    if assessment_type:
        filtered = [a for a in filtered if a["assessment_type"] == assessment_type]

    if is_active is not None:
        filtered = [a for a in filtered if a["is_active"] == is_active]

    if search:
        search_lower = search.lower()
        filtered = [
            a for a in filtered
            if search_lower in a["title"].lower() or search_lower in (a.get("description") or "").lower()
        ]

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return PaginatedAssessmentResponse(
        items=[AssessmentResponse(**a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=AssessmentResponse, status_code=201)
async def create_assessment(assessment: AssessmentCreate):
    """
    Create a new assessment with validation.
    """
    new_id = _generate_id()
    timestamp = _get_timestamp()

    new_assessment = {
        "id": new_id,
        "title": assessment.title,
        "description": assessment.description,
        "assessment_type": assessment.assessment_type,
        "duration_minutes": assessment.duration_minutes,
        "passing_score": assessment.passing_score,
        "max_attempts": assessment.max_attempts,
        "is_active": assessment.is_active,
        "created_at": timestamp,
        "updated_at": timestamp,
        "question_count": 0,
        "average_score": None,
        "total_attempts": 0,
    }

    MOCK_ASSESSMENTS.append(new_assessment)

    return AssessmentResponse(**new_assessment)
