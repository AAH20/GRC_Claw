"""
Events API endpoints for gated communities.

Provides:
  GET  /events  — list events with pagination, filtering by date/community
  POST /events  — create a new event with validation
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/events", tags=["events"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EventCreate(BaseModel):
    """Payload for creating a new event."""

    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    community_id: int = Field(..., gt=0)
    start_date: date
    end_date: Optional[date] = None
    location: Optional[str] = Field(None, max_length=300)
    max_attendees: Optional[int] = Field(None, gt=0, le=10_000)
    is_public: bool = False

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: Optional[date], info) -> Optional[date]:
        if v is not None:
            start = info.data.get("start_date")
            if start and v < start:
                raise ValueError("end_date must be on or after start_date")
        return v


class EventResponse(BaseModel):
    """Event representation returned by the API."""

    id: int
    title: str
    description: str
    community_id: int
    start_date: date
    end_date: Optional[date] = None
    location: Optional[str] = None
    max_attendees: Optional[int] = None
    attendee_count: int = 0
    is_public: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedEvents(BaseModel):
    """Paginated list of events."""

    items: list[EventResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Mock data store (in-memory for demonstration)
# ---------------------------------------------------------------------------

_mock_events: list[dict] = []
_mock_id_counter: int = 0


def _seed_mock_data() -> None:
    """Populate the mock store with realistic sample events."""
    global _mock_id_counter

    if _mock_events:
        return

    communities = [1, 2, 3, 4, 5]
    titles = [
        "Community Town Hall",
        "Monthly Meetup: AI & Society",
        "Workshop: Building with LLMs",
        "Panel: The Future of Work",
        "Hackathon: Green Tech",
        "Book Club: Thinking, Fast and Slow",
        "Fireside Chat with Founders",
        "AMA: Open Source Governance",
        "Design Review: New Dashboard",
        "Lightning Talks Night",
        "Strategy Session Q4",
        "Onboarding Webinar",
    ]
    locations = [
        "San Francisco, CA",
        "New York, NY",
        "London, UK",
        "Berlin, DE",
        "Virtual",
        "Austin, TX",
        "Toronto, CA",
        "Singapore",
    ]

    base_date = date.today()

    for i, title in enumerate(titles):
        start = base_date + timedelta(days=i * 3 - 5)
        end = start + timedelta(days=1) if i % 3 == 0 else None
        created = datetime.combine(start, datetime.min.time()) - timedelta(days=2)

        _mock_events.append(
            {
                "id": i + 1,
                "title": title,
                "description": f"Join us for {title.lower()}. "
                f"This session brings together community members to share insights, "
                f"discuss challenges, and explore new ideas together.",
                "community_id": communities[i % len(communities)],
                "start_date": start,
                "end_date": end,
                "location": locations[i % len(locations)],
                "max_attendees": [50, 100, 200, None, 500][i % 5],
                "attendee_count": [12, 34, 78, 5, 150][i % 5],
                "is_public": i % 4 == 0,
                "created_at": created,
                "updated_at": created + timedelta(hours=2),
            }
        )

    _mock_id_counter = len(_mock_events)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=PaginatedEvents)
async def list_events(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    community_id: Optional[int] = Query(None, gt=0, description="Filter by community ID"),
    start_after: Optional[date] = Query(None, description="Filter events starting on or after this date"),
    start_before: Optional[date] = Query(None, description="Filter events starting on or before this date"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private visibility"),
) -> PaginatedEvents:
    """
    List events with pagination and optional filtering.

    Query parameters:
    - **page**: Page number (1-indexed, default 1)
    - **page_size**: Number of items per page (default 20, max 100)
    - **community_id**: Only return events for this community
    - **start_after**: Only return events starting on or after this date
    - **start_before**: Only return events starting on or before this date
    - **is_public**: Filter by visibility (true = public only, false = private only)
    """
    _seed_mock_data()

    filtered = _mock_events.copy()

    if community_id is not None:
        filtered = [e for e in filtered if e["community_id"] == community_id]

    if start_after is not None:
        filtered = [e for e in filtered if e["start_date"] >= start_after]

    if start_before is not None:
        filtered = [e for e in filtered if e["start_date"] <= start_before]

    if is_public is not None:
        filtered = [e for e in filtered if e["is_public"] == is_public]

    # Sort by start_date ascending
    filtered.sort(key=lambda e: e["start_date"])

    total = len(filtered)
    pages = (total + page_size - 1) // page_size if total else 1

    # Clamp page to valid range
    if page > pages:
        page = pages

    offset = (page - 1) * page_size
    items = filtered[offset : offset + page_size]

    return PaginatedEvents(
        items=[EventResponse(**e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate) -> EventResponse:
    """
    Create a new event.

    Validates the payload and returns the created event with a 201 status.
    Raises 422 if validation fails (handled automatically by FastAPI/Pydantic).
    """
    global _mock_id_counter

    _seed_mock_data()

    _mock_id_counter += 1
    now = datetime.utcnow()

    new_event = {
        "id": _mock_id_counter,
        "title": payload.title,
        "description": payload.description,
        "community_id": payload.community_id,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "location": payload.location,
        "max_attendees": payload.max_attendees,
        "attendee_count": 0,
        "is_public": payload.is_public,
        "created_at": now,
        "updated_at": now,
    }

    _mock_events.append(new_event)

    return EventResponse(**new_event)
