"""Employers API endpoints for the recruitment platform."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/employers", tags=["employers"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────


class EmployerBase(BaseModel):
    """Shared employer fields."""

    name: str = Field(..., min_length=2, max_length=120, description="Company legal name")
    slug: str = Field(
        ...,
        min_length=2,
        max_length=60,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly unique identifier",
    )
    industry: str = Field(..., min_length=2, max_length=80)
    website: Optional[str] = Field(None, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=30)
    company_size: Optional[str] = Field(
        None,
        pattern=r"^(1-10|11-50|51-200|211-500|501-1000|1001-5000|5001\+)$",
    )
    founded_year: Optional[int] = Field(None, ge=1800, le=datetime.now().year)
    description: Optional[str] = Field(None, max_length=2000)
    logo_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class EmployerCreate(EmployerBase):
    """Schema for creating a new employer."""

    pass


class EmployerUpdate(BaseModel):
    """Schema for partial employer updates."""

    name: Optional[str] = Field(None, min_length=2, max_length=120)
    industry: Optional[str] = Field(None, min_length=2, max_length=80)
    website: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    company_size: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    logo_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class Address(BaseModel):
    """Physical address of the employer headquarters."""

    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = Field(default="US", min_length=2, max_length=2)


class Employer(EmployerBase):
    """Full employer representation returned by the API."""

    id: str
    hq_address: Optional[Address] = None
    created_at: datetime
    updated_at: datetime
    total_jobs: int = 0
    total_candidates: int = 0

    class Config:
        from_attributes = True


class EmployerListResponse(BaseModel):
    """Paginated list of employers."""

    data: List[Employer]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Mock Data Store ─────────────────────────────────────────────────────────

MOCK_EMPLOYERS: List[dict] = [
    {
        "id": "emp_001",
        "name": "Acme Corporation",
        "slug": "acme-corporation",
        "industry": "Technology",
        "website": "https://acme.example.com",
        "contact_email": "hr@acme.example.com",
        "contact_phone": "+1-555-0101",
        "company_size": "501-1000",
        "founded_year": 1998,
        "description": "Leading provider of cloud-native solutions for enterprise automation.",
        "logo_url": "https://cdn.example.com/logos/acme.png",
        "is_active": True,
        "hq_address": {
            "street": "100 Innovation Drive",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "US",
        },
        "created_at": "2024-01-15T09:30:00Z",
        "updated_at": "2025-06-20T14:22:00Z",
        "total_jobs": 42,
        "total_candidates": 1287,
    },
    {
        "id": "emp_002",
        "name": "Globex Industries",
        "slug": "globex-industries",
        "industry": "Manufacturing",
        "website": "https://globex.example.com",
        "contact_email": "careers@globex.example.com",
        "contact_phone": "+1-555-0202",
        "company_size": "1001-5000",
        "founded_year": 1975,
        "description": "Global manufacturer of industrial components and precision engineering.",
        "logo_url": "https://cdn.example.com/logos/globex.png",
        "is_active": True,
        "hq_address": {
            "street": "4500 Factory Blvd",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
            "country": "US",
        },
        "created_at": "2024-02-10T11:00:00Z",
        "updated_at": "2025-05-18T10:45:00Z",
        "total_jobs": 18,
        "total_candidates": 543,
    },
    {
        "id": "emp_003",
        "name": "Initech LLC",
        "slug": "initech-llc",
        "industry": "Financial Services",
        "website": "https://initech.example.com",
        "contact_email": "talent@initech.example.com",
        "contact_phone": "+1-555-0303",
        "company_size": "211-500",
        "founded_year": 2005,
        "description": "Fintech company revolutionizing payment infrastructure for SMBs.",
        "logo_url": "https://cdn.example.com/logos/initech.png",
        "is_active": True,
        "hq_address": {
            "street": "88 Wall Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10005",
            "country": "US",
        },
        "created_at": "2024-03-05T08:15:00Z",
        "updated_at": "2025-07-01T16:30:00Z",
        "total_jobs": 27,
        "total_candidates": 892,
    },
    {
        "id": "emp_004",
        "name": "Umbrella Health",
        "slug": "umbrella-health",
        "industry": "Healthcare",
        "website": "https://umbrella.example.com",
        "contact_email": "recruiting@umbrella.example.com",
        "contact_phone": "+1-555-0404",
        "company_size": "5001+",
        "founded_year": 1988,
        "description": "Integrated healthcare network with 200+ facilities across North America.",
        "logo_url": "https://cdn.example.com/logos/umbrella.png",
        "is_active": True,
        "hq_address": {
            "street": "2200 Medical Center Pkwy",
            "city": "Houston",
            "state": "TX",
            "postal_code": "77030",
            "country": "US",
        },
        "created_at": "2024-01-28T13:45:00Z",
        "updated_at": "2025-04-12T09:00:00Z",
        "total_jobs": 63,
        "total_candidates": 2104,
    },
    {
        "id": "emp_005",
        "name": "Stark Innovations",
        "slug": "stark-innovations",
        "industry": "Aerospace & Defense",
        "website": "https://stark.example.com",
        "contact_email": "jobs@stark.example.com",
        "contact_phone": "+1-555-0505",
        "company_size": "1001-5000",
        "founded_year": 2001,
        "description": "Advanced aerospace engineering and defense technology research.",
        "logo_url": "https://cdn.example.com/logos/stark.png",
        "is_active": True,
        "hq_address": {
            "street": "1000 Aviation Way",
            "city": "Seattle",
            "state": "WA",
            "postal_code": "98109",
            "country": "US",
        },
        "created_at": "2024-04-12T10:00:00Z",
        "updated_at": "2025-03-22T11:15:00Z",
        "total_jobs": 35,
        "total_candidates": 756,
    },
    {
        "id": "emp_006",
        "name": "Wayne Enterprises",
        "slug": "wayne-enterprises",
        "industry": "Conglomerate",
        "website": "https://wayne.example.com",
        "contact_email": "hr@wayne.example.com",
        "contact_phone": "+1-555-0606",
        "company_size": "5001+",
        "founded_year": 1939,
        "description": "Diversified conglomerate with interests in technology, media, and energy.",
        "logo_url": "https://cdn.example.com/logos/wayne.png",
        "is_active": True,
        "hq_address": {
            "street": "1007 Mountain Drive",
            "city": "Gotham",
            "state": "NJ",
            "postal_code": "07101",
            "country": "US",
        },
        "created_at": "2024-02-20T14:30:00Z",
        "updated_at": "2025-06-05T08:45:00Z",
        "total_jobs": 51,
        "total_candidates": 1632,
    },
    {
        "id": "emp_007",
        "name": "Cyberdyne Systems",
        "slug": "cyberdyne-systems",
        "industry": "Artificial Intelligence",
        "website": "https://cyberdyne.example.com",
        "contact_email": "talent@cyberdyne.example.com",
        "contact_phone": "+1-555-0707",
        "company_size": "51-200",
        "founded_year": 2015,
        "description": "AI research lab focused on machine learning and autonomous systems.",
        "logo_url": "https://cdn.example.com/logos/cyberdyne.png",
        "is_active": True,
        "hq_address": {
            "street": "500 AI Boulevard",
            "city": "Austin Alto",
            "state": "CA",
            "postal_code": "94301",
            "country": "US",
        },
        "created_at": "2024-05-01T09:00:00Z",
        "updated_at": "2025-07-10T13:20:00Z",
        "total_jobs": 12,
        "total_candidates": 389,
    },
    {
        "id": "emp_008",
        "name": "Hooli Technologies",
        "slug": "hooli-technologies",
        "industry": "Technology",
        "website": "https://hooli.example.com",
        "contact_email": "careers@hooli.example.com",
        "contact_phone": "+1-555-0808",
        "company_size": "1001-5000",
        "founded_year": 2006,
        "description": "Consumer technology company building the next generation of social platforms.",
        "logo_url": "https://cdn.example.com/logos/hooli.png",
        "is_active": True,
        "hq_address": {
            "street": "1 Hooli Way",
            "city": "Palo Alto",
            "state": "CA",
            "postal_code": "94301",
            "country": "US",
        },
        "created_at": "2024-03-18T12:00:00Z",
        "updated_at": "2025-05-28T15:10:00Z",
        "total_jobs": 44,
        "total_candidates": 1420,
    },
    {
        "id": "emp_009",
        "name": "Pied Piper Solutions",
        "slug": "pied-piper-solutions",
        "industry": "Technology",
        "website": "https://piedpiper.example.com",
        "contact_email": "hello@piedpiper.example.com",
        "contact_phone": "+1-555-0909",
        "company_size": "11-50",
        "founded_year": 2014,
        "description": "Compression technology startup disrupting data infrastructure.",
        "logo_url": "https://cdn.example.com/logos/piedpiper.png",
        "is_active": True,
        "hq_address": {
            "street": "3500 Compression Ct",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94107",
            "country": "US",
        },
        "created_at": "2024-06-10T10:30:00Z",
        "updated_at": "2025-04-15T09:45:00Z",
        "total_jobs": 8,
        "total_candidates": 215,
    },
    {
        "id": "emp_010",
        "name": "Aperture Labs",
        "slug": "aperture-labs",
        "industry": "Research & Development",
        "website": "https://aperture.example.com",
        "contact_email": "science@aperture.example.com",
        "contact_phone": "+1-555-1010",
        "company_size": "211-500",
        "founded_year": 1953,
        "description": "Scientific research facility specializing in portal technology and quantum physics.",
        "logo_url": "https://cdn.example.com/logos/aperture.png",
        "is_active": True,
        "hq_address": {
            "street": "1200 Science Park",
            "city": "Eerie",
            "state": "PA",
            "postal_code": "16501",
            "country": "US",
        },
        "created_at": "2024-01-05T08:00:00Z",
        "updated_at": "2025-02-14T11:30:00Z",
        "total_jobs": 22,
        "total_candidates": 678,
    },
    {
        "id": "emp_011",
        "name": "Soylent Corp",
        "slug": "soylent-corp",
        "industry": "Food Technology",
        "website": "https://soylent.example.com",
        "contact_email": "team@soylent.example.com",
        "contact_phone": "+1-555-1111",
        "company_size": "51-200",
        "founded_year": 2013,
        "description": "Sustainable food technology company focused on alternative protein sources.",
        "logo_url": "https://cdn.example.com/logos/soylent.png",
        "is_active": True,
        "hq_address": {
            "street": "77 Nutrition Ave",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90012",
            "country": "US",
        },
        "created_at": "2024-07-22T13:00:00Z",
        "updated_at": "2025-06-30T10:00:00Z",
        "total_jobs": 15,
        "total_candidates": 412,
    },
    {
        "id": "emp_012",
        "name": "Tyrell Corporation",
        "slug": "tyrell-corporation",
        "industry": "Biotechnology",
        "website": "https://tyrell.example.com",
        "contact_email": "recruitment@tyrell.example.com",
        "contact_phone": "+1-555-1212",
        "company_size": "501-1000",
        "founded_year": 1982,
        "description": "Biotech corporation pioneering genetic engineering and synthetic biology.",
        "logo_url": "https://cdn.example.com/logos/tyrell.png",
        "is_active": True,
        "hq_address": {
            "street": "2800 Genetic Way",
            "city": "San Diego",
            "state": "CA",
            "postal_code": "92121",
            "country": "US",
        },
        "created_at": "2024-02-14T09:15:00Z",
        "updated_at": "2025-03-10T14:45:00Z",
        "total_jobs": 29,
        "total_candidates": 834,
    },
]


# ─── Helper Functions ────────────────────────────────────────────────────────


def _get_next_id() -> str:
    """Generate the next employer ID based on existing records."""
    max_num = 0
    for emp in MOCK_EMPLOYERS:
        num_part = emp["id"].replace("emp_", "")
        try:
            max_num = max(max_num, int(num_part))
        except ValueError:
            continue
    return f"emp_{max_num + 1:03d}"


def _employer_to_response(emp: dict) -> Employer:
    """Convert a mock employer dict to an Employer response model."""
    return Employer(**emp)


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=EmployerListResponse,
    summary="List employers",
    description="Retrieve a paginated list of all employers in the platform.",
)
async def list_employers(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    company_size: Optional[str] = Query(None, description="Filter by company size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
) -> EmployerListResponse:
    """
    List employers with pagination and optional filtering.

    Returns a paginated list of employers matching the provided filters.
    """
    filtered = MOCK_EMPLOYERS.copy()

    # Apply filters
    if industry:
        filtered = [e for e in filtered if e["industry"].lower() == industry.lower()]
    if company_size:
        filtered = [e for e in filtered if e["company_size"] == company_size]
    if is_active is not None:
        filtered = [e for e in filtered if e["is_active"] == is_active]
    if search:
        search_lower = search.lower()
        filtered = [
            e
            for e in filtered
            if search_lower in e["name"].lower()
            or (e.get("description") and search_lower in e["description"].lower())
        ]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Clamp page to valid range
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return EmployerListResponse(
        data=[_employer_to_response(e) for e in page_items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=Employer,
    status_code=status.HTTP_201_CREATED,
    summary="Create employer",
    description="Register a new employer on the recruitment platform.",
)
async def create_employer(employer: EmployerCreate) -> Employer:
    """
    Create a new employer with validation.

    Validates uniqueness of slug and email, then creates the employer record.
    """
    # Check for duplicate slug
    existing_slugs = {e["slug"] for e in MOCK_EMPLOYERS}
    if employer.slug in existing_slugs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An employer with slug '{employer.slug}' already exists.",
        )

    # Check for duplicate email
    existing_emails = {e["contact_email"] for e in MOCK_EMPLOYERS}
    if employer.contact_email in existing_emails:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An employer with email '{employer.contact_email}' already exists.",
        )

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_id = _get_next_id()

    new_employer = {
        "id": new_id,
        **employer.model_dump(),
        "hq_address": None,
        "created_at": now,
        "updated_at": now,
        "total_jobs": 0,
        "total_candidates": 0,
    }

    MOCK_EMPLOYERS.append(new_employer)

    return Employer(**new_employer)
