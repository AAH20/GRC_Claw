"""Talent Pool API endpoints.

Provides CRUD operations for managing talent pools in the recruitment platform.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/talent-pools", tags=["talent-pools"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class TalentPoolCreate(BaseModel):
    """Schema for creating a new talent pool."""

    name: str = Field(..., min_length=1, max_length=200, description="Pool name")
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list, max_length=50)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Pool name must not be blank")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def tags_must_be_unique(cls, v: List[str]) -> List[str]:
        seen = set()
        for tag in v:
            lowered = tag.strip().lower()
            if lowered in seen:
                raise ValueError(f"Duplicate tag: {tag}")
            seen.add(lowered)
        return v


class TalentPoolResponse(BaseModel):
    """Schema for talent pool response."""

    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    candidate_count: int
    is_active: bool
    created_at: str
    updated_at: str


class PaginatedTalentPoolResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[TalentPoolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

MOCK_TALENT_POOLS: List[Dict[str, Any]] = [
    {
        "id": "tp-001",
        "name": "Senior Backend Engineers",
        "description": "Experienced backend engineers with Python, Go, or Rust expertise.",
        "tags": ["backend", "python", "go", "rust", "senior"],
        "candidate_count": 47,
        "is_active": True,
        "created_at": "2025-09-15T10:30:00Z",
        "updated_at": "2025-10-01T14:22:00Z",
    },
    {
        "id": "tp-002",
        "name": "Machine Learning Researchers",
        "description": "PhD-level researchers in NLP, computer vision, and reinforcement learning.",
        "tags": ["ml", "nlp", "computer-vision", "research"],
        "candidate_count": 23,
        "is_active": True,
        "created_at": "2025-08-20T09:00:00Z",
        "updated_at": "2025-09-28T11:45:00Z",
    },
    {
        "id": "tp-003",
        "name": "Product Design Leads",
        "description": "Design leaders with 8+ years of product design experience.",
        "tags": ["design", "product", "leadership", "ux"],
        "candidate_count": 12,
        "is_active": True,
        "created_at": "2025-07-10T16:20:00Z",
        "updated_at": "2025-09-15T08:10:00Z",
    },
    {
        "id": "tp-004",
        "name": "DevOps & SRE",
        "description": "Site reliability engineers and DevOps specialists.",
        "tags": ["devops", "sre", "kubernetes", "aws"],
        "candidate_count": 31,
        "is_active": True,
        "created_at": "2025-06-05T12:00:00Z",
        "updated_at": "2025-09-20T17:30:00Z",
    },
    {
        "id": "tp-005",
        "name": "Frontend Architects",
        "description": "Senior frontend engineers specializing in React, Vue, and modern frameworks.",
        "tags": ["frontend", "react", "vue", "typescript"],
        "candidate_count": 19,
        "is_active": False,
        "created_at": "2025-05-12T14:45:00Z",
        "updated_at": "2025-08-30T10:00:00Z",
    },
    {
        "id": "tp-006",
        "name": "Data Engineers",
        "description": "Engineers building and maintaining data pipelines and warehouses.",
        "tags": ["data", "spark", "airflow", "sql"],
        "candidate_count": 28,
        "is_active": True,
        "created_at": "2025-04-18T08:30:00Z",
        "updated_at": "2025-09-10T13:15:00Z",
    },
    {
        "id": "tp-007",
        "name": "Security Engineers",
        "description": "Application and infrastructure security specialists.",
        "tags": ["security", "appsec", "infosec", "pentesting"],
        "candidate_count": 15,
        "is_active": True,
        "created_at": "2025-03-22T11:00:00Z",
        "updated_at": "2025-09-05T09:45:00Z",
    },
    {
        "id": "tp-008",
        "name": "Mobile Engineers",
        "description": "iOS and Android developers with production app experience.",
        "tags": ["mobile", "ios", "android", "swift", "kotlin"],
        "candidate_count": 34,
        "is_active": True,
        "created_at": "2025-02-14T15:30:00Z",
        "updated_at": "2025-08-25T16:00:00Z",
    },
    {
        "id": "tp-009",
        "name": "QA Automation Engineers",
        "description": "Test automation engineers with Selenium, Cypress, or Playwright experience.",
        "tags": ["qa", "automation", "selenium", "cypress"],
        "candidate_count": 21,
        "is_active": True,
        "created_at": "2025-01-28T10:00:00Z",
        "updated_at": "2025-08-18T12:30:00Z",
    },
    {
        "id": "tp-010",
        "name": "Engineering Managers",
        "description": "Technical leaders managing teams of 5-20 engineers.",
        "tags": ["management", "leadership", "engineering"],
        "candidate_count": 8,
        "is_active": True,
        "created_at": "2025-01-10T09:15:00Z",
        "updated_at": "2025-07-22T14:00:00Z",
    },
    {
        "id": "tp-011",
        "name": "Full-Stack Developers",
        "description": "Versatile developers comfortable across the entire stack.",
        "tags": ["fullstack", "javascript", "python", "node"],
        "candidate_count": 56,
        "is_active": True,
        "created_at": "2024-12-05T13:45:00Z",
        "updated_at": "2025-09-28T10:30:00Z",
    },
    {
        "id": "tp-012",
        "name": "Cloud Architects",
        "description": "Solutions architects with multi-cloud deployment experience.",
        "tags": ["cloud", "aws", "gcp", "azure", "architecture"],
        "candidate_count": 14,
        "is_active": True,
        "created_at": "2024-11-18T11:30:00Z",
        "updated_at": "2025-08-12T09:00:00Z",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedTalentPoolResponse,
    summary="List talent pools",
    description="Retrieve a paginated list of talent pools with optional filtering.",
)
async def list_talent_pools(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Filter by name or tag"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> PaginatedTalentPoolResponse:
    """List talent pools with pagination and optional filters."""
    filtered = MOCK_TALENT_POOLS.copy()

    if search:
        search_lower = search.lower()
        filtered = [
            pool for pool in filtered
            if search_lower in pool["name"].lower()
            or any(search_lower in tag.lower() for tag in pool["tags"])
        ]

    if is_active is not None:
        filtered = [pool for pool in filtered if pool["is_active"] == is_active]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return PaginatedTalentPoolResponse(
        items=[TalentPoolResponse(**pool) for pool in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=TalentPoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a talent pool",
    description="Create a new talent pool with validation.",
)
async def create_talent_pool(payload: TalentPoolCreate) -> TalentPoolResponse:
    """Create a new talent pool."""
    # Check for duplicate names (case-insensitive)
    name_lower = payload.name.lower()
    for pool in MOCK_TALENT_POOLS:
        if pool["name"].lower() == name_lower:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A talent pool with name '{payload.name}' already exists.",
            )

    now = datetime.now(timezone.utc).isoformat()
    new_pool = {
        "id": f"tp-{str(uuid4())[:8]}",
        "name": payload.name,
        "description": payload.description,
        "tags": payload.tags,
        "candidate_count": 0,
        "is_active": payload.is_active,
        "created_at": now,
        "updated_at": now,
    }

    MOCK_TALENT_POOLS.append(new_pool)

    return TalentPoolResponse(**new_pool)
