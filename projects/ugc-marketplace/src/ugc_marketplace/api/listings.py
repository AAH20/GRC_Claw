"""
Listings API endpoints for UGC Marketplace.

Provides CRUD operations for product/service listings with pagination,
filtering, and validation.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/listings", tags=["listings"])


# ─── Mock Data ───────────────────────────────────────────────────────────────

MOCK_LISTINGS = [
    {
        "id": "lst_001",
        "seller_id": "usr_101",
        "title": "Professional UGC Video Package — 10 Product Demos",
        "description": "High-quality UGC-style product demo videos shot in 4K. Includes scripting, filming, and editing. Perfect for e-commerce brands looking for authentic content.",
        "category": "video",
        "price": 450.00,
        "currency": "USD",
        "status": "active",
        "tags": ["ugc", "product-demo", "4k", "ecommerce"],
        "rating": 4.8,
        "review_count": 23,
        "created_at": "2025-09-15T10:30:00Z",
        "updated_at": "2025-10-01T14:22:00Z",
    },
    {
        "id": "lst_002",
        "seller_id": "usr_102",
        "title": "Social Media Content Bundle — 30 Days",
        "description": "30 days of scroll-stopping social media content including Reels, TikToks, and Instagram posts. Covers strategy, creation, and scheduling.",
        "category": "social_media",
        "price": 1200.00,
        "currency": "USD",
        "status": "active",
        "tags": ["social-media", "tiktok", "instagram", "reels"],
        "rating": 4.9,
        "review_count": 47,
        "created_at": "2025-08-20T09:00:00Z",
        "updated_at": "2025-09-28T11:15:00Z",
    },
    {
        "id": "lst_003",
        "seller_id": "usr_103",
        "title": "Influencer Unboxing & Review — Beauty Products",
        "description": "Authentic unboxing and review videos for beauty and skincare brands. Includes 2-minute and 5-minute versions optimized for different platforms.",
        "category": "influencer",
        "price": 275.00,
        "currency": "USD",
        "status": "active",
        "tags": ["beauty", "unboxing", "review", "skincare"],
        "rating": 4.7,
        "review_count": 31,
        "created_at": "2025-09-01T16:45:00Z",
        "updated_at": "2025-09-30T08:30:00Z",
    },
    {
        "id": "lst_004",
        "seller_id": "usr_104",
        "title": "UGC Testimonial Videos — 5 Pack",
        "description": "Customer testimonial-style videos that feel genuine and relatable. Great for landing pages, ads, and email campaigns.",
        "category": "video",
        "price": 320.00,
        "currency": "USD",
        "status": "active",
        "tags": ["testimonial", "ugc", "ads", "landing-page"],
        "rating": 4.6,
        "review_count": 18,
        "created_at": "2025-09-10T12:00:00Z",
        "updated_at": "2025-10-02T09:45:00Z",
    },
    {
        "id": "lst_005",
        "seller_id": "usr_105",
        "title": "TikTok Ad Creative — 15 Variations",
        "description": "15 unique TikTok ad creatives designed for maximum engagement. Includes hooks, CTAs, and trending audio suggestions.",
        "category": "social_media",
        "price": 600.00,
        "currency": "USD",
        "status": "active",
        "tags": ["tiktok", "ads", "creative", "variations"],
        "rating": 4.5,
        "review_count": 12,
        "created_at": "2025-08-15T14:20:00Z",
        "updated_at": "2025-09-25T17:00:00Z",
    },
    {
        "id": "lst_006",
        "seller_id": "usr_106",
        "title": "Product Photography + UGC Combo",
        "description": "Professional product photography paired with UGC-style lifestyle shots. 20 images total, delivered in 48 hours.",
        "category": "photography",
        "price": 380.00,
        "currency": "USD",
        "status": "active",
        "tags": ["photography", "product", "lifestyle", "combo"],
        "rating": 4.8,
        "review_count": 27,
        "created_at": "2025-09-05T11:30:00Z",
        "updated_at": "2025-10-01T10:00:00Z",
    },
    {
        "id": "lst_007",
        "seller_id": "usr_107",
        "title": "UGC Script Writing — 10 Scripts",
        "description": "Conversion-focused UGC scripts for ads and organic content. Written by copywriters with 5+ years of UGC experience.",
        "category": "copywriting",
        "price": 150.00,
        "currency": "USD",
        "status": "active",
        "tags": ["script", "copywriting", "ugc", "ads"],
        "rating": 4.9,
        "review_count": 35,
        "created_at": "2025-08-25T08:00:00Z",
        "updated_at": "2025-09-20T13:30:00Z",
    },
    {
        "id": "lst_008",
        "seller_id": "usr_108",
        "title": "Amazon A+ Content & UGC Videos",
        "description": "Complete Amazon listing optimization including A+ content design and UGC video integration for enhanced brand storytelling.",
        "category": "ecommerce",
        "price": 850.00,
        "currency": "USD",
        "status": "active",
        "tags": ["amazon", "a-plus", "ecommerce", "ugc"],
        "rating": 4.7,
        "review_count": 19,
        "created_at": "2025-09-12T15:00:00Z",
        "updated_at": "2025-10-02T16:00:00Z",
    },
    {
        "id": "lst_009",
        "seller_id": "usr_109",
        "title": "UGC Voiceover — 30 Second Spots",
        "description": "Professional voiceover for UGC-style ads. Multiple voice talent options available. Includes 2 revision rounds.",
        "category": "audio",
        "price": 95.00,
        "currency": "USD",
        "status": "active",
        "tags": ["voiceover", "audio", "ugc", "ads"],
        "rating": 4.4,
        "review_count": 8,
        "created_at": "2025-09-18T10:00:00Z",
        "updated_at": "2025-09-29T12:00:00Z",
    },
    {
        "id": "lst_010",
        "seller_id": "usr_110",
        "title": "UGC Content Strategy Consultation",
        "description": "1-hour strategy call to plan your UGC content pipeline. Includes competitor analysis, content calendar, and platform recommendations.",
        "category": "consulting",
        "price": 200.00,
        "currency": "USD",
        "status": "active",
        "tags": ["strategy", "consultation", "ugc", "planning"],
        "rating": 5.0,
        "review_count": 14,
        "created_at": "2025-08-30T09:30:00Z",
        "updated_at": "2025-09-27T14:00:00Z",
    },
    {
        "id": "lst_011",
        "seller_id": "usr_111",
        "title": "UGC Video Editing — 5 Videos",
        "description": "Professional editing for raw UGC footage. Includes color correction, captions, sound design, and platform-specific formatting.",
        "category": "video",
        "price": 250.00,
        "currency": "USD",
        "status": "active",
        "tags": ["editing", "video", "ugc", "post-production"],
        "rating": 4.6,
        "review_count": 22,
        "created_at": "2025-09-08T13:00:00Z",
        "updated_at": "2025-10-01T11:00:00Z",
    },
    {
        "id": "lst_012",
        "seller_id": "usr_112",
        "title": "UGC Ad Account Management — Monthly",
        "description": "Full-service UGC ad management including creative testing, audience targeting, and monthly performance reporting.",
        "category": "advertising",
        "price": 1500.00,
        "currency": "USD",
        "status": "active",
        "tags": ["ads", "management", "monthly", "ugc"],
        "rating": 4.8,
        "review_count": 16,
        "created_at": "2025-08-10T07:00:00Z",
        "updated_at": "2025-09-26T10:30:00Z",
    },
]


# ─── Pydantic Models ─────────────────────────────────────────────────────────

VALID_CATEGORIES = [
    "video",
    "social_media",
    "influencer",
    "photography",
    "copywriting",
    "ecommerce",
    "audio",
    "consulting",
    "advertising",
]


class ListingCreate(BaseModel):
    """Schema for creating a new listing."""

    seller_id: str = Field(..., min_length=1, max_length=64, description="Seller's user ID")
    title: str = Field(..., min_length=5, max_length=200, description="Listing title")
    description: str = Field(..., min_length=20, max_length=5000, description="Detailed description")
    category: str = Field(..., description="Listing category")
    price: float = Field(..., gt=0, le=100000, description="Price in USD")
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$", description="ISO 4217 currency code")
    tags: list[str] = Field(default_factory=list, max_length=10, description="Up to 10 tags")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        cleaned = [t.strip().lower() for t in v if t.strip()]
        if len(cleaned) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in cleaned:
            if len(tag) > 30:
                raise ValueError(f"Tag '{tag}' exceeds 30 character limit")
        return cleaned


class ListingResponse(BaseModel):
    """Schema for listing response."""

    id: str
    seller_id: str
    title: str
    description: str
    category: str
    price: float
    currency: str
    status: str
    tags: list[str]
    rating: float = 0.0
    review_count: int = 0
    created_at: str
    updated_at: str


class ListingListResponse(BaseModel):
    """Schema for paginated listing list response."""

    data: list[ListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=ListingListResponse, summary="List all listings")
async def list_listings(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price filter"),
    search: Optional[str] = Query(default=None, min_length=2, description="Search in title/description"),
    sort_by: str = Query(default="created_at", pattern="^(created_at|price|rating|title)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> dict:
    """
    Get a paginated, filterable list of listings.

    Supports filtering by category, price range, and text search.
    Results can be sorted by creation date, price, rating, or title.
    """
    filtered = MOCK_LISTINGS.copy()

    # Apply category filter
    if category:
        if category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}",
            )
        filtered = [l for l in filtered if l["category"] == category]

    # Apply price range filter
    if min_price is not None:
        filtered = [l for l in filtered if l["price"] >= min_price]
    if max_price is not None:
        filtered = [l for l in filtered if l["price"] <= max_price]

    # Apply text search
    if search:
        search_lower = search.lower()
        filtered = [
            l for l in filtered
            if search_lower in l["title"].lower() or search_lower in l["description"].lower()
        ]

    # Apply sorting
    reverse = sort_order == "desc"
    if sort_by == "price":
        filtered.sort(key=lambda x: x["price"], reverse=reverse)
    elif sort_by == "rating":
        filtered.sort(key=lambda x: x["rating"], reverse=reverse)
    elif sort_by == "title":
        filtered.sort(key=lambda x: x["title"].lower(), reverse=reverse)
    else:  # created_at
        filtered.sort(key=lambda x: x["created_at"], reverse=reverse)

    # Apply pagination
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
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


@router.post(
    "/",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
)
async def create_listing(payload: ListingCreate) -> dict:
    """
    Create a new listing with validation.

    Returns the newly created listing with generated ID and timestamps.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate a new listing ID
    max_id = 0
    for listing in MOCK_LISTINGS:
        try:
            num = int(listing["id"].split("_")[1])
            max_id = max(max_id, num)
        except (IndexError, ValueError):
            pass

    new_listing = {
        "id": f"lst_{max_id + 1:03d}",
        "seller_id": payload.seller_id,
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "price": payload.price,
        "currency": payload.currency,
        "status": "active",
        "tags": payload.tags,
        "rating": 0.0,
        "review_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    # In production, this would persist to the database
    MOCK_LISTINGS.append(new_listing)

    return new_listing
