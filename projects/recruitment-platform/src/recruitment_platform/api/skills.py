"""Skills API endpoints for the recruitment platform."""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/skills", tags=["skills"])

# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

_SKILLS_DB: list[dict] = [
    {
        "id": 1,
        "name": "Python",
        "category": "technical",
        "description": "General-purpose programming with Python 3.10+",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 2,
        "certifications": ["PCAP", "PCPP1", "PCPP2"],
        "is_active": True,
        "created_at": "2025-01-15T09:30:00Z",
        "updated_at": "2025-06-20T14:22:00Z",
    },
    {
        "id": 2,
        "name": "Project Management",
        "category": "management",
        "description": "Planning, executing, and closing projects on time and budget",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 3,
        "certifications": ["PMP", "PRINCE2", "CSM"],
        "is_active": True,
        "created_at": "2025-02-10T11:00:00Z",
        "updated_at": "2025-07-01T10:15:00Z",
    },
    {
        "id": 3,
        "name": "Data Analysis",
        "category": "technical",
        "description": "Extracting insights from structured and unstructured data",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 1,
        "certifications": ["Google Data Analytics", "IBM Data Analyst"],
        "is_active": True,
        "created_at": "2025-03-05T08:45:00Z",
        "updated_at": "2025-05-18T16:30:00Z",
    },
    {
        "id": 4,
        "name": "Communication",
        "category": "soft_skill",
        "description": "Effective verbal and written communication in professional settings",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 0,
        "certifications": [],
        "is_active": True,
        "created_at": "2025-01-20T13:00:00Z",
        "updated_at": "2025-04-10T09:00:00Z",
    },
    {
        "id": 5,
        "name": "AWS Solutions Architect",
        "category": "technical",
        "description": "Designing distributed systems and architectures on AWS",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 4,
        "certifications": ["AWS SAA-C03", "AWS SAP-C02"],
        "is_active": True,
        "created_at": "2025-04-01T10:00:00Z",
        "updated_at": "2025-08-12T11:45:00Z",
    },
    {
        "id": 6,
        "name": "Leadership",
        "category": "management",
        "description": "Leading teams, driving strategy, and mentoring direct reports",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 5,
        "certifications": ["CCL Leadership", "ICF ACC"],
        "is_active": True,
        "created_at": "2025-02-28T15:30:00Z",
        "updated_at": "2025-06-05T12:00:00Z",
    },
    {
        "id": 7,
        "name": "UI/UX Design",
        "category": "creative",
        "description": "Designing intuitive user interfaces and experiences",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 2,
        "certifications": ["Google UX Design", "NN/g UX Certification"],
        "is_active": True,
        "created_at": "2025-03-15T09:00:00Z",
        "updated_at": "2025-07-22T14:00:00Z",
    },
    {
        "id": 8,
        "name": "DevOps",
        "category": "technical",
        "description": "CI/CD pipelines, infrastructure as code, and SRE practices",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 3,
        "certifications": ["CKA", "CKD", "AWS DevOps Pro"],
        "is_active": True,
        "created_at": "2025-05-10T08:00:00Z",
        "updated_at": "2025-09-01T10:30:00Z",
    },
    {
        "id": 9,
        "name": "Negotiation",
        "category": "soft_skill",
        "description": "Contract, salary, and stakeholder negotiation techniques",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 1,
        "certifications": ["Harvard PON"],
        "is_active": True,
        "created_at": "2025-06-01T11:00:00Z",
        "updated_at": "2025-08-15T09:45:00Z",
    },
    {
        "id": 10,
        "name": "Content Writing",
        "category": "creative",
        "description": "Creating compelling written content for digital and print media",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 1,
        "certifications": ["HubSpot Content Marketing"],
        "is_active": True,
        "created_at": "2025-04-20T14:00:00Z",
        "updated_at": "2025-07-10T16:00:00Z",
    },
    {
        "id": 11,
        "name": "Cybersecurity",
        "category": "technical",
        "description": "Securing systems, networks, and data from threats",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 3,
        "certifications": ["CompTIA Security+", "CISSP", "CEH"],
        "is_active": True,
        "created_at": "2025-07-01T09:30:00Z",
        "updated_at": "2025-09-10T13:15:00Z",
    },
    {
        "id": 12,
        "name": "Team Building",
        "category": "soft_skill",
        "description": "Fostering collaboration, trust, and high-performing teams",
        "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
        "years_experience_required": 2,
        "certifications": [],
        "is_active": True,
        "created_at": "2025-05-25T10:00:00Z",
        "updated_at": "2025-08-20T11:30:00Z",
    },
]

_VALID_CATEGORIES = {"technical", "soft_skill", "management", "creative", "domain_specific"}
_VALID_PROFICIENCY_LEVELS = {"beginner", "intermediate", "advanced", "expert"}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: Literal["technical", "soft_skill", "management", "creative", "domain_specific"]
    description: str = Field(..., min_length=10, max_length=1000)
    proficiency_levels: list[str] = Field(default_factory=list)
    years_experience_required: int = Field(default=0, ge=0, le=50)
    certifications: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("proficiency_levels")
    @classmethod
    def validate_proficiency_levels(cls, v: list[str]) -> list[str]:
        invalid = [lvl for lvl in v if lvl not in _VALID_PROFICIENCY_LEVELS]
        if invalid:
            raise ValueError(f"Invalid proficiency levels: {invalid}. Must be one of {_VALID_PROFICIENCY_LEVELS}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Skill name cannot be blank")
        return v.strip()


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[Literal["technical", "soft_skill", "management", "creative", "domain_specific"]] = None
    description: Optional[str] = Field(default=None, min_length=10, max_length=1000)
    proficiency_levels: Optional[list[str]] = None
    years_experience_required: Optional[int] = Field(default=None, ge=0, le=50)
    certifications: Optional[list[str]] = None
    is_active: Optional[bool] = None


class SkillResponse(SkillBase):
    id: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=SkillListResponse, summary="List skills with pagination and category filtering")
async def list_skills(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    category: Optional[Literal["technical", "soft_skill", "management", "creative", "domain_specific"]] = Query(
        default=None, description="Filter by skill category"
    ),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    search: Optional[str] = Query(default=None, min_length=1, max_length=100, description="Search by name or description"),
) -> dict:
    """Return a paginated list of skills, optionally filtered by category, status, or search term."""
    filtered = _SKILLS_DB.copy()

    if category is not None:
        filtered = [s for s in filtered if s["category"] == category]

    if is_active is not None:
        filtered = [s for s in filtered if s["is_active"] == is_active]

    if search:
        term = search.lower()
        filtered = [
            s for s in filtered
            if term in s["name"].lower() or term in s["description"].lower()
        ]

    total = len(filtered)
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="Create a new skill")
async def create_skill(payload: SkillCreate) -> dict:
    """Create a new skill entry. Returns the created skill with generated ID and timestamps."""
    # Check for duplicate name (case-insensitive)
    name_lower = payload.name.lower()
    for existing in _SKILLS_DB:
        if existing["name"].lower() == name_lower:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill with name '{payload.name}' already exists",
            )

    new_id = max((s["id"] for s in _SKILLS_DB), default=0) + 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_skill = {
        "id": new_id,
        "name": payload.name,
        "category": payload.category,
        "description": payload.description,
        "proficiency_levels": payload.proficiency_levels,
        "years_experience_required": payload.years_experience_required,
        "certifications": payload.certifications,
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }

    _SKILLS_DB.append(new_skill)
    return new_skill
