"""Applications API endpoints for the recruitment platform."""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/applications", tags=["applications"])

# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

MOCK_APPLICATIONS = [
    {
        "id": "app_001",
        "candidate_name": "Alice Johnson",
        "candidate_email": "alice.johnson@example.com",
        "position_id": "pos_001",
        "position_title": "Senior Backend Engineer",
        "status": "applied",
        "applied_at": "2026-09-15T09:30:00Z",
        "resume_url": "https://storage.example.com/resumes/alice_johnson.pdf",
        "cover_letter": "I am excited to apply for this role...",
        "source": "linkedin",
        "years_experience": 7,
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
    },
    {
        "id": "app_002",
        "candidate_name": "Bob Martinez",
        "candidate_email": "bob.martinez@example.com",
        "position_id": "pos_002",
        "position_title": "Frontend Developer",
        "status": "screening",
        "applied_at": "2026-09-18T14:22:00Z",
        "resume_url": "https://storage.example.com/resumes/bob_martinez.pdf",
        "cover_letter": "With 5 years of React experience...",
        "source": "referral",
        "years_experience": 5,
        "skills": ["React", "TypeScript", "CSS", "Node.js"],
    },
    {
        "id": "app_003",
        "candidate_name": "Carol Chen",
        "candidate_email": "carol.chen@example.com",
        "position_id": "pos_001",
        "position_title": "Senior Backend Engineer",
        "status": "interview",
        "applied_at": "2026-09-10T11:00:00Z",
        "resume_url": "https://storage.example.com/resumes/carol_chen.pdf",
        "cover_letter": "As a backend engineer with 8 years...",
        "source": "company_website",
        "years_experience": 8,
        "skills": ["Python", "Go", "Kubernetes", "Microservices"],
    },
    {
        "id": "app_004",
        "candidate_name": "David Okafor",
        "candidate_email": "david.okafor@example.com",
        "position_id": "pos_003",
        "position_title": "DevOps Engineer",
        "status": "offer",
        "applied_at": "2026-08-25T08:45:00Z",
        "resume_url": "https://storage.example.com/resumes/david_okafor.pdf",
        "cover_letter": "I have extensive experience in CI/CD...",
        "source": "indeed",
        "years_experience": 6,
        "skills": ["Terraform", "Docker", "Jenkins", "AWS", "Python"],
    },
    {
        "id": "app_005",
        "candidate_name": "Eva Petrov",
        "candidate_email": "eva.petrov@example.com",
        "position_id": "pos_002",
        "position_title": "Frontend Developer",
        "status": "rejected",
        "applied_at": "2026-09-20T16:10:00Z",
        "resume_url": "https://storage.example.com/resumes/eva_petrov.pdf",
        "cover_letter": "I believe my skills align well...",
        "source": "linkedin",
        "years_experience": 3,
        "skills": ["JavaScript", "Vue.js", "HTML", "CSS"],
    },
    {
        "id": "app_006",
        "candidate_name": "Frank Liu",
        "candidate_email": "frank.liu@example.com",
        "position_id": "pos_004",
        "position_title": "Machine Learning Engineer",
        "status": "applied",
        "applied_at": "2026-10-01T10:05:00Z",
        "resume_url": "https://storage.example.com/resumes/frank_liu.pdf",
        "cover_letter": "With a PhD in ML and 4 years industry...",
        "source": "referral",
        "years_experience": 4,
        "skills": ["PyTorch", "TensorFlow", "Python", "MLOps"],
    },
    {
        "id": "app_007",
        "candidate_name": "Grace Kim",
        "candidate_email": "grace.kim@example.com",
        "position_id": "pos_001",
        "position_title": "Senior Backend Engineer",
        "status": "screening",
        "applied_at": "2026-09-22T13:30:00Z",
        "resume_url": "https://storage.example.com/resumes/grace_kim.pdf",
        "cover_letter": "I am passionate about building scalable systems...",
        "source": "company_website",
        "years_experience": 9,
        "skills": ["Python", "Django", "Redis", "Kafka", "AWS"],
    },
    {
        "id": "app_008",
        "candidate_name": "Hassan Ahmed",
        "candidate_email": "hassan.ahmed@example.com",
        "position_id": "pos_003",
        "position_title": "DevOps Engineer",
        "status": "interview",
        "applied_at": "2026-09-05T09:00:00Z",
        "resume_url": "https://storage.example.com/resumes/hassan_ahmed.pdf",
        "cover_letter": "I have been working in DevOps for 5 years...",
        "source": "indeed",
        "years_experience": 5,
        "skills": ["Ansible", "Docker", "Kubernetes", "Azure", "Bash"],
    },
    {
        "id": "app_009",
        "candidate_name": "Irene Novak",
        "candidate_email": "irene.novak@example.com",
        "position_id": "pos_004",
        "position_title": "Machine Learning Engineer",
        "status": "offer",
        "applied_at": "2026-08-28T15:20:00Z",
        "resume_url": "https://storage.example.com/resumes/irene_novak.pdf",
        "cover_letter": "My research focuses on NLP and LLMs...",
        "source": "referral",
        "years_experience": 6,
        "skills": ["Python", "PyTorch", "Hugging Face", "CUDA", "Rust"],
    },
    {
        "id": "app_010",
        "candidate_name": "James O'Brien",
        "candidate_email": "james.obrien@example.com",
        "position_id": "pos_002",
        "position_title": "Frontend Developer",
        "status": "hired",
        "applied_at": "2026-08-15T12:00:00Z",
        "resume_url": "https://storage.example.com/resumes/james_obrien.pdf",
        "cover_letter": "I have been building web apps for 6 years...",
        "source": "linkedin",
        "years_experience": 6,
        "skills": ["React", "Next.js", "TypeScript", "GraphQL", "Tailwind"],
    },
    {
        "id": "app_011",
        "candidate_name": "Katarina Silva",
        "candidate_email": "katarina.silva@example.com",
        "position_id": "pos_001",
        "position_title": "Senior Backend Engineer",
        "status": "applied",
        "applied_at": "2026-10-02T08:15:00Z",
        "resume_url": "https://storage.example.com/resumes/katarina_silva.pdf",
        "cover_letter": "I am a backend engineer with a focus on...",
        "source": "company_website",
        "years_experience": 10,
        "skills": ["Java", "Spring Boot", "PostgreSQL", "Kafka", "GCP"],
    },
    {
        "id": "app_012",
        "candidate_name": "Liam O'Connor",
        "candidate_email": "liam.oconnor@example.com",
        "position_id": "pos_003",
        "position_title": "DevOps Engineer",
        "status": "rejected",
        "applied_at": "2026-09-12T17:40:00Z",
        "resume_url": "https://storage.example.com/resumes/liam_oconnor.pdf",
        "cover_letter": "I am interested in transitioning to DevOps...",
        "source": "indeed",
        "years_experience": 2,
        "skills": ["Linux", "Bash", "Docker", "Git"],
    },
]

VALID_STATUSES = {"applied", "screening", "interview", "offer", "hired", "rejected"}
VALID_SOURCES = {"linkedin", "indeed", "referral", "company_website", "glassdoor", "other"}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ApplicationCreate(BaseModel):
    candidate_name: str = Field(..., min_length=1, max_length=200)
    candidate_email: EmailStr
    position_id: str = Field(..., min_length=1, max_length=50)
    position_title: str = Field(..., min_length=1, max_length=200)
    resume_url: Optional[str] = Field(None, max_length=500)
    cover_letter: Optional[str] = Field(None, max_length=5000)
    source: Literal["linkedin", "indeed", "referral", "company_website", "glassdoor", "other"] = "other"
    years_experience: int = Field(0, ge=0, le=60)
    skills: list[str] = Field(default_factory=list)


class ApplicationResponse(BaseModel):
    id: str
    candidate_name: str
    candidate_email: str
    position_id: str
    position_title: str
    status: str
    applied_at: str
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    source: str
    years_experience: int
    skills: list[str]


class PaginatedApplications(BaseModel):
    items: list[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedApplications)
async def list_applications(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[Literal["applied", "screening", "interview", "offer", "hired", "rejected"]] = Query(
        None, alias="status", description="Filter by application status"
    ),
    position_id: Optional[str] = Query(None, description="Filter by position ID"),
    search: Optional[str] = Query(None, description="Search by candidate name or email"),
):
    """List applications with pagination and optional filtering."""
    filtered = MOCK_APPLICATIONS.copy()

    if status_filter:
        filtered = [a for a in filtered if a["status"] == status_filter]

    if position_id:
        filtered = [a for a in filtered if a["position_id"] == position_id]

    if search:
        search_lower = search.lower()
        filtered = [
            a for a in filtered
            if search_lower in a["candidate_name"].lower()
            or search_lower in a["candidate_email"].lower()
        ]

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return PaginatedApplications(
        items=[ApplicationResponse(**a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate):
    """Create a new job application."""
    # Check for duplicate application (same email + position)
    for app in MOCK_APPLICATIONS:
        if (
            app["candidate_email"] == payload.candidate_email
            and app["position_id"] == payload.position_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidate has already applied for this position",
            )

    new_id = f"app_{len(MOCK_APPLICATIONS) + 1:03d}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_application = {
        "id": new_id,
        "candidate_name": payload.candidate_name,
        "candidate_email": payload.candidate_email,
        "position_id": payload.position_id,
        "position_title": payload.position_title,
        "status": "applied",
        "applied_at": now,
        "resume_url": payload.resume_url,
        "cover_letter": payload.cover_letter,
        "source": payload.source,
        "years_experience": payload.years_experience,
        "skills": payload.skills,
    }

    MOCK_APPLICATIONS.append(new_application)

    return ApplicationResponse(**new_application)
