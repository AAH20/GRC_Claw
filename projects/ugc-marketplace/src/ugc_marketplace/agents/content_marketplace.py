"""Content Marketplace Agent for UGC Marketplace.

Provides search and statistics capabilities for the content marketplace,
including filtering by content type, price range, rating, and availability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class ContentType(str, Enum):
    """Supported content types in the marketplace."""

    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    TEMPLATE = "template"
    PRESET = "preset"


class ContentCategory(str, Enum):
    """Content categories available in the marketplace."""

    SOCIAL_MEDIA = "social_media"
    MARKETING = "marketing"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    LIFESTYLE = "lifestyle"
    TECH = "tech"
    HEALTH = "health"
    FINANCE = "finance"


class SortOrder(str, Enum):
    """Sort order options for search results."""

    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING_DESC = "rating_desc"
    NEWEST = "newest"
    POPULARITY = "popularity"


@dataclass
class MarketplaceFilters:
    """Filters applicable to marketplace search."""

    content_types: list[ContentType] = field(default_factory=list)
    categories: list[ContentCategory] = field(default_factory=list)
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    creator_verified: Optional[bool] = None
    sort_by: SortOrder = SortOrder.RELEVANCE
    limit: int = 20
    offset: int = 0


@dataclass
class CreatorInfo:
    """Creator metadata embedded in search results."""

    creator_id: str
    display_name: str
    verified: bool
    total_sales: int
    average_rating: float
    avatar_url: str


@dataclass
class ContentItem:
    """A single content item in the marketplace."""

    item_id: str
    title: str
    description: str
    content_type: ContentType
    category: ContentCategory
    price: float
    currency: str
    rating: float
    review_count: int
    sales_count: int
    tags: list[str]
    creator: CreatorInfo
    thumbnail_url: str
    created_at: str
    updated_at: str
    is_active: bool
    license_type: str
    file_size_mb: float
    preview_url: Optional[str] = None


@dataclass
class SearchResult:
    """Paginated search result container."""

    items: list[ContentItem]
    total_count: int
    page: int
    per_page: int
    has_more: bool
    query: str
    filters_applied: MarketplaceFilters


@dataclass
class CategoryStats:
    """Per-category statistics."""

    category: ContentCategory
    item_count: int
    total_sales: int
    average_price: float
    average_rating: float


@dataclass
class MarketplaceStats:
    """Aggregate marketplace statistics."""

    total_items: int
    total_creators: int
    total_sales: int
    total_revenue: float
    average_item_price: float
    average_item_rating: float
    active_items: int
    verified_creators: int
    new_items_last_30_days: int
    sales_last_30_days: int
    revenue_last_30_days: float
    top_categories: list[CategoryStats]
    content_type_distribution: dict[str, int]
    price_range: dict[str, float]


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

_MOCK_CREATORS: dict[str, CreatorInfo] = {
    "cr_001": CreatorInfo(
        creator_id="cr_001",
        display_name="PixelCraft Studio",
        verified=True,
        total_sales=1247,
        average_rating=4.8,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_001.png",
    ),
    "cr_002": CreatorInfo(
        creator_id="cr_002",
        display_name="AudioWave Pro",
        verified=True,
        total_sales=892,
        average_rating=4.6,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_002.png",
    ),
    "cr_003": CreatorInfo(
        creator_id="cr_003",
        display_name="TextCraft AI",
        verified=False,
        total_sales=315,
        average_rating=4.2,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_003.png",
    ),
    "cr_004": CreatorInfo(
        creator_id="cr_004",
        display_name="VisualStory Media",
        verified=True,
        total_sales=2103,
        average_rating=4.9,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_004.png",
    ),
    "cr_005": CreatorInfo(
        creator_id="cr_005",
        display_name="TemplateKing",
        verified=False,
        total_sales=567,
        average_rating=4.3,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_005.png",
    ),
    "cr_006": CreatorInfo(
        creator_id="cr_006",
        display_name="SoundScape Labs",
        verified=True,
        total_sales=743,
        average_rating=4.7,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_006.png",
    ),
    "cr_007": CreatorInfo(
        creator_id="cr_007",
        display_name="EduContent Hub",
        verified=True,
        total_sales=1589,
        average_rating=4.5,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_007.png",
    ),
    "cr_008": CreatorInfo(
        creator_id="cr_008",
        display_name="FinVisuals",
        verified=False,
        total_sales=201,
        average_rating=4.1,
        avatar_url="https://cdn.ugc-marketplace.io/avatars/cr_008.png",
    ),
}

_MOCK_ITEMS: list[ContentItem] = [
    ContentItem(
        item_id="item_001",
        title="Cinematic Product Showcase Template",
        description="A premium After Effects template for product showcases with smooth transitions and modern typography.",
        content_type=ContentType.TEMPLATE,
        category=ContentCategory.MARKETING,
        price=49.99,
        currency="USD",
        rating=4.8,
        review_count=156,
        sales_count=892,
        tags=["after-effects", "product", "showcase", "cinematic"],
        creator=_MOCK_CREATORS["cr_001"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_001.jpg",
        created_at="2025-08-15T10:30:00Z",
        updated_at="2025-09-20T14:22:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=245.7,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_001.mp4",
    ),
    ContentItem(
        item_id="item_002",
        title="Lo-Fi Study Beat Collection",
        description="A curated collection of 25 lo-fi beats perfect for study streams, podcasts, and relaxation content.",
        content_type=ContentType.AUDIO,
        category=ContentCategory.ENTERTAINMENT,
        price=19.99,
        currency="USD",
        rating=4.6,
        review_count=89,
        sales_count=534,
        tags=["lo-fi", "beats", "study", "chill", "royalty-free"],
        creator=_MOCK_CREATORS["cr_002"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_002.jpg",
        created_at="2025-07-01T08:00:00Z",
        updated_at="2025-09-10T11:45:00Z",
        is_active=True,
        license_type="royalty_free",
        file_size_mb=312.4,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_002.mp3",
    ),
    ContentItem(
        item_id="item_003",
        title="Social Media Caption Pack — Q4 2025",
        description="500+ ready-to-use social media captions optimized for engagement across Instagram, TikTok, and X.",
        content_type=ContentType.TEXT,
        category=ContentCategory.SOCIAL_MEDIA,
        price=14.99,
        currency="USD",
        rating=4.2,
        review_count=45,
        sales_count=287,
        tags=["captions", "social-media", "copywriting", "instagram", "tiktok"],
        creator=_MOCK_CREATORS["cr_003"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_003.jpg",
        created_at="2025-09-01T12:00:00Z",
        updated_at="2025-09-25T09:30:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=2.1,
    ),
    ContentItem(
        item_id="item_004",
        title="Brand Identity Video Intro Pack",
        description="10 unique video intro templates for brand identity projects. 4K resolution, easy to customize.",
        content_type=ContentType.VIDEO,
        category=ContentCategory.MARKETING,
        price=79.99,
        currency="USD",
        rating=4.9,
        review_count=203,
        sales_count=1247,
        tags=["intro", "brand", "4k", "video", "logo-reveal"],
        creator=_MOCK_CREATORS["cr_004"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_004.jpg",
        created_at="2025-06-20T15:00:00Z",
        updated_at="2025-09-18T16:00:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=1024.0,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_004.mp4",
    ),
    ContentItem(
        item_id="item_005",
        title="Instagram Story Template Bundle",
        description="50 animated Instagram story templates with trending transitions and text animations.",
        content_type=ContentType.TEMPLATE,
        category=ContentCategory.SOCIAL_MEDIA,
        price=29.99,
        currency="USD",
        rating=4.3,
        review_count=67,
        sales_count=412,
        tags=["instagram", "stories", "animated", "templates"],
        creator=_MOCK_CREATORS["cr_005"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_005.jpg",
        created_at="2025-08-10T09:00:00Z",
        updated_at="2025-09-15T10:00:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=178.3,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_005.mp4",
    ),
    ContentItem(
        item_id="item_006",
        title="Ambient Sound Effects Library",
        description="200+ high-quality ambient sound effects for video production, podcasts, and game development.",
        content_type=ContentType.AUDIO,
        category=ContentCategory.ENTERTAINMENT,
        price=34.99,
        currency="USD",
        rating=4.7,
        review_count=112,
        sales_count=678,
        tags=["ambient", "sfx", "sound-effects", "production"],
        creator=_MOCK_CREATORS["cr_006"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_006.jpg",
        created_at="2025-05-15T11:00:00Z",
        updated_at="2025-09-05T13:30:00Z",
        is_active=True,
        license_type="royalty_free",
        file_size_mb=567.8,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_006.mp3",
    ),
    ContentItem(
        item_id="item_007",
        title="Online Course Slide Deck Template",
        description="Professional PowerPoint and Keynote templates for online courses. Includes 120+ unique slides.",
        content_type=ContentType.TEMPLATE,
        category=ContentCategory.EDUCATION,
        price=39.99,
        currency="USD",
        rating=4.5,
        review_count=78,
        sales_count=456,
        tags=["powerpoint", "keynote", "course", "slides", "education"],
        creator=_MOCK_CREATORS["cr_007"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_007.jpg",
        created_at="2025-07-20T14:00:00Z",
        updated_at="2025-09-12T08:45:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=89.2,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_007.pdf",
    ),
    ContentItem(
        item_id="item_008",
        title="Financial Dashboard Infographic Kit",
        description="A set of 30 customizable infographic templates for financial reports and dashboards.",
        content_type=ContentType.IMAGE,
        category=ContentCategory.FINANCE,
        price=24.99,
        currency="USD",
        rating=4.1,
        review_count=34,
        sales_count=189,
        tags=["infographic", "finance", "dashboard", "data-viz"],
        creator=_MOCK_CREATORS["cr_008"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_008.jpg",
        created_at="2025-08-25T10:00:00Z",
        updated_at="2025-09-22T15:00:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=45.6,
    ),
    ContentItem(
        item_id="item_009",
        title="Fitness Motivation Video Pack",
        description="15 high-energy workout motivation videos for fitness influencers and gym promotions.",
        content_type=ContentType.VIDEO,
        category=ContentCategory.HEALTH,
        price=59.99,
        currency="USD",
        rating=4.6,
        review_count=91,
        sales_count=523,
        tags=["fitness", "workout", "motivation", "gym", "health"],
        creator=_MOCK_CREATORS["cr_004"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_009.jpg",
        created_at="2025-06-10T09:30:00Z",
        updated_at="2025-09-08T12:00:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=2048.0,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_009.mp4",
    ),
    ContentItem(
        item_id="item_010",
        title="Tech Blog Post Template Collection",
        description="SEO-optimized blog post templates for tech writers. Includes 40 structures with meta descriptions.",
        content_type=ContentType.TEXT,
        category=ContentCategory.TECH,
        price=12.99,
        currency="USD",
        rating=4.4,
        review_count=56,
        sales_count=334,
        tags=["blog", "seo", "tech", "writing", "templates"],
        creator=_MOCK_CREATORS["cr_003"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_010.jpg",
        created_at="2025-09-05T08:00:00Z",
        updated_at="2025-09-28T10:15:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=1.8,
    ),
    ContentItem(
        item_id="item_011",
        title="Lifestyle Photography Preset Pack",
        description="60 Lightroom presets for lifestyle and travel photography. Warm tones, film looks, and more.",
        content_type=ContentType.PRESET,
        category=ContentCategory.LIFESTYLE,
        price=27.99,
        currency="USD",
        rating=4.7,
        review_count=134,
        sales_count=789,
        tags=["lightroom", "presets", "photography", "lifestyle", "travel"],
        creator=_MOCK_CREATORS["cr_001"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_011.jpg",
        created_at="2025-07-15T13:00:00Z",
        updated_at="2025-09-14T09:00:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=15.3,
    ),
    ContentItem(
        item_id="item_012",
        title="Podcast Intro Jingle Pack",
        description="12 professionally produced podcast intro jingles in various styles. Stems included.",
        content_type=ContentType.AUDIO,
        category=ContentCategory.ENTERTAINMENT,
        price=44.99,
        currency="USD",
        rating=4.8,
        review_count=167,
        sales_count=912,
        tags=["podcast", "jingle", "intro", "audio", "music"],
        creator=_MOCK_CREATORS["cr_006"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_012.jpg",
        created_at="2025-05-28T10:00:00Z",
        updated_at="2025-09-01T14:30:00Z",
        is_active=True,
        license_type="royalty_free",
        file_size_mb=189.5,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_012.mp3",
    ),
    ContentItem(
        item_id="item_013",
        title="E-commerce Product Photo Presets",
        description="45 Lightroom presets specifically designed for e-commerce product photography.",
        content_type=ContentType.PRESET,
        category=ContentCategory.MARKETING,
        price=22.99,
        currency="USD",
        rating=4.3,
        review_count=48,
        sales_count=267,
        tags=["ecommerce", "product-photography", "lightroom", "presets"],
        creator=_MOCK_CREATORS["cr_005"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_013.jpg",
        created_at="2025-08-05T11:00:00Z",
        updated_at="2025-09-19T16:45:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=12.7,
    ),
    ContentItem(
        item_id="item_014",
        title="YouTube Thumbnail Template Pack",
        description="100 click-worthy YouTube thumbnail templates. Fully customizable in Photoshop and Canva.",
        content_type=ContentType.TEMPLATE,
        category=ContentCategory.SOCIAL_MEDIA,
        price=19.99,
        currency="USD",
        rating=4.5,
        review_count=211,
        sales_count=1089,
        tags=["youtube", "thumbnail", "clickbait", "templates"],
        creator=_MOCK_CREATORS["cr_004"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_014.jpg",
        created_at="2025-06-01T08:00:00Z",
        updated_at="2025-09-11T11:20:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=67.4,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_014.jpg",
    ),
    ContentItem(
        item_id="item_015",
        title="Stock Video: City Timelapse Collection",
        description="20 stunning 4K city timelapse videos from around the world. Perfect for backgrounds and B-roll.",
        content_type=ContentType.VIDEO,
        category=ContentCategory.LIFESTYLE,
        price=39.99,
        currency="USD",
        rating=4.6,
        review_count=83,
        sales_count=445,
        tags=["timelapse", "city", "4k", "stock-video", "b-roll"],
        creator=_MOCK_CREATORS["cr_001"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_015.jpg",
        created_at="2025-07-25T15:00:00Z",
        updated_at="2025-09-16T10:00:00Z",
        is_active=True,
        license_type="royalty_free",
        file_size_mb=4096.0,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_015.mp4",
    ),
    ContentItem(
        item_id="item_016",
        title="Email Marketing Copy Swipe File",
        description="300+ proven email marketing copy templates for welcome sequences, promotions, and newsletters.",
        content_type=ContentType.TEXT,
        category=ContentCategory.MARKETING,
        price=16.99,
        currency="USD",
        rating=4.4,
        review_count=72,
        sales_count=398,
        tags=["email", "marketing", "copywriting", "swipe-file"],
        creator=_MOCK_CREATORS["cr_003"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_016.jpg",
        created_at="2025-08-18T09:00:00Z",
        updated_at="2025-09-21T13:00:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=3.2,
    ),
    ContentItem(
        item_id="item_017",
        title="Meditation Ambient Music Pack",
        description="8 hours of continuous ambient meditation music. Binaural beats and nature sounds included.",
        content_type=ContentType.AUDIO,
        category=ContentCategory.HEALTH,
        price=29.99,
        currency="USD",
        rating=4.9,
        review_count=145,
        sales_count=678,
        tags=["meditation", "ambient", "binaural", "relaxation", "wellness"],
        creator=_MOCK_CREATORS["cr_006"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_017.jpg",
        created_at="2025-06-15T12:00:00Z",
        updated_at="2025-09-03T08:30:00Z",
        is_active=True,
        license_type="royalty_free",
        file_size_mb=789.3,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_017.mp3",
    ),
    ContentItem(
        item_id="item_018",
        title="Real Estate Virtual Tour Template",
        description="Immersive virtual tour template for real estate listings. Compatible with Matterport and Kuula.",
        content_type=ContentType.TEMPLATE,
        category=ContentCategory.MARKETING,
        price=89.99,
        currency="USD",
        rating=4.7,
        review_count=59,
        sales_count=234,
        tags=["real-estate", "virtual-tour", "matterport", "kuula"],
        creator=_MOCK_CREATORS["cr_007"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_018.jpg",
        created_at="2025-08-01T10:00:00Z",
        updated_at="2025-09-17T14:00:00Z",
        is_active=True,
        license_type="commercial",
        file_size_mb=345.6,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_018.mp4",
    ),
    ContentItem(
        item_id="item_019",
        title="Crypto Trading Chart Pack",
        description="50 high-resolution crypto trading chart images for presentations and social media.",
        content_type=ContentType.IMAGE,
        category=ContentCategory.FINANCE,
        price=14.99,
        currency="USD",
        rating=4.0,
        review_count=28,
        sales_count=156,
        tags=["crypto", "trading", "charts", "finance", "bitcoin"],
        creator=_MOCK_CREATORS["cr_008"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_019.jpg",
        created_at="2025-09-10T11:00:00Z",
        updated_at="2025-09-29T09:00:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=23.4,
    ),
    ContentItem(
        item_id="item_020",
        title="Online Course: Content Creation Masterclass",
        description="A comprehensive video course covering content creation strategy, tools, and monetization.",
        content_type=ContentType.VIDEO,
        category=ContentCategory.EDUCATION,
        price=149.99,
        currency="USD",
        rating=4.8,
        review_count=312,
        sales_count=1567,
        tags=["course", "content-creation", "masterclass", "education", "video"],
        creator=_MOCK_CREATORS["cr_007"],
        thumbnail_url="https://cdn.ugc-marketplace.io/thumbs/item_020.jpg",
        created_at="2025-05-01T08:00:00Z",
        updated_at="2025-09-20T16:00:00Z",
        is_active=True,
        license_type="personal",
        file_size_mb=8192.0,
        preview_url="https://cdn.ugc-marketplace.io/previews/item_020.mp4",
    ),
]


# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------


class ContentMarketplaceAgent:
    """Agent for interacting with the UGC content marketplace.

    Provides search and statistics capabilities with realistic mock data.
    In production, this would connect to the marketplace API or database.
    """

    def __init__(self, items: Optional[list[ContentItem]] = None) -> None:
        """Initialize the agent with mock or provided items.

        Args:
            items: Optional list of ContentItem objects. Uses mock data if None.
        """
        self._items: list[ContentItem] = items if items is not None else _MOCK_ITEMS.copy()
        self._creators: dict[str, CreatorInfo] = {
            item.creator.creator_id: item.creator for item in self._items
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_marketplace(
        self,
        query: str,
        filters: Optional[MarketplaceFilters] = None,
    ) -> SearchResult:
        """Search the marketplace for content items matching the query and filters.

        Performs a case-insensitive search across item titles, descriptions, and tags.
        Applies all provided filters and returns paginated results.

        Args:
            query: The search string to match against item metadata.
            filters: Optional filters to narrow down results. Defaults to no filters.

        Returns:
            SearchResult containing matching items and pagination metadata.

        Raises:
            ValueError: If query is empty or filters contain invalid values.
        """
        if not query or not query.strip():
            raise ValueError("Search query must be a non-empty string.")

        if filters is None:
            filters = MarketplaceFilters()

        # Validate filter values
        if filters.min_price is not None and filters.min_price < 0:
            raise ValueError("min_price must be non-negative.")
        if filters.max_price is not None and filters.max_price < 0:
            raise ValueError("max_price must be non-negative.")
        if (
            filters.min_price is not None
            and filters.max_price is not None
            and filters.min_price > filters.max_price
        ):
            raise ValueError("min_price cannot be greater than max_price.")
        if filters.min_rating is not None and not (0 <= filters.min_rating <= 5):
            raise ValueError("min_rating must be between 0 and 5.")
        if filters.max_rating is not None and not (0 <= filters.max_rating <= 5):
            raise ValueError("max_rating must be between 0 and 5.")
        if filters.limit < 1:
            raise ValueError("limit must be at least 1.")
        if filters.offset < 0:
            raise ValueError("offset must be non-negative.")

        query_lower = query.strip().lower()

        # Filter items
        matched: list[ContentItem] = []
        for item in self._items:
            if not item.is_active:
                continue

            # Text search across title, description, and tags
            searchable_text = f"{item.title} {item.description} {' '.join(item.tags)}".lower()
            if query_lower not in searchable_text:
                continue

            # Apply content type filter
            if filters.content_types and item.content_type not in filters.content_types:
                continue

            # Apply category filter
            if filters.categories and item.category not in filters.categories:
                continue

            # Apply price range filter
            if filters.min_price is not None and item.price < filters.min_price:
                continue
            if filters.max_price is not None and item.price > filters.max_price:
                continue

            # Apply rating filter
            if filters.min_rating is not None and item.rating < filters.min_rating:
                continue
            if filters.max_rating is not None and item.rating > filters.max_rating:
                continue

            # Apply tags filter (item must have at least one matching tag)
            if filters.tags:
                item_tags_lower = {t.lower() for t in item.tags}
                filter_tags_lower = {t.lower() for t in filters.tags}
                if not item_tags_lower.intersection(filter_tags_lower):
                    continue

            # Apply creator verified filter
            if filters.creator_verified is not None:
                if item.creator.verified != filters.creator_verified:
                    continue

            matched.append(item)

        # Sort results
        matched = self._sort_items(matched, filters.sort_by)

        # Paginate
        total_count = len(matched)
        start = filters.offset
        end = start + filters.limit
        paginated_items = matched[start:end]
        page = (start // filters.limit) + 1 if filters.limit > 0 else 1
        has_more = end < total_count

        return SearchResult(
            items=paginated_items,
            total_count=total_count,
            page=page,
            per_page=filters.limit,
            has_more=has_more,
            query=query,
            filters_applied=filters,
        )

    def get_marketplace_stats(self) -> MarketplaceStats:
        """Compute and return aggregate marketplace statistics.

        Calculates totals, averages, distributions, and top categories
        from the current marketplace inventory.

        Returns:
            MarketplaceStats with comprehensive marketplace metrics.
        """
        active_items = [item for item in self._items if item.is_active]
        total_items = len(active_items)
        total_creators = len(self._creators)

        total_sales = sum(item.sales_count for item in active_items)
        total_revenue = sum(item.price * item.sales_count for item in active_items)

        average_item_price = (
            sum(item.price for item in active_items) / total_items if total_items > 0 else 0.0
        )
        average_item_rating = (
            sum(item.rating for item in active_items) / total_items if total_items > 0 else 0.0
        )

        verified_creators = sum(1 for c in self._creators.values() if c.verified)

        # Simulate "last 30 days" metrics (using a deterministic subset)
        new_items_last_30_days = sum(
            1 for item in active_items if item.created_at >= "2025-09-01"
        )
        sales_last_30_days = sum(
            item.sales_count // 4 for item in active_items
        )  # Approximate quarterly sales
        revenue_last_30_days = sum(
            (item.price * item.sales_count) / 4 for item in active_items
        )

        # Category stats
        category_map: dict[ContentCategory, list[ContentItem]] = {}
        for item in active_items:
            category_map.setdefault(item.category, []).append(item)

        top_categories: list[CategoryStats] = []
        for category, items in category_map.items():
            cat_sales = sum(i.sales_count for i in items)
            cat_avg_price = sum(i.price for i in items) / len(items) if items else 0.0
            cat_avg_rating = sum(i.rating for i in items) / len(items) if items else 0.0
            top_categories.append(
                CategoryStats(
                    category=category,
                    item_count=len(items),
                    total_sales=cat_sales,
                    average_price=round(cat_avg_price, 2),
                    average_rating=round(cat_avg_rating, 2),
                )
            )
        top_categories.sort(key=lambda c: c.total_sales, reverse=True)

        # Content type distribution
        content_type_distribution: dict[str, int] = {}
        for item in active_items:
            ct = item.content_type.value
            content_type_distribution[ct] = content_type_distribution.get(ct, 0) + 1

        # Price range
        prices = [item.price for item in active_items]
        price_range = {
            "min": round(min(prices), 2) if prices else 0.0,
            "max": round(max(prices), 2) if prices else 0.0,
        }

        return MarketplaceStats(
            total_items=total_items,
            total_creators=total_creators,
            total_sales=total_sales,
            total_revenue=round(total_revenue, 2),
            average_item_price=round(average_item_price, 2),
            average_item_rating=round(average_item_rating, 2),
            active_items=total_items,
            verified_creators=verified_creators,
            new_items_last_30_days=new_items_last_30_days,
            sales_last_30_days=sales_last_30_days,
            revenue_last_30_days=round(revenue_last_30_days, 2),
            top_categories=top_categories,
            content_type_distribution=content_type_distribution,
            price_range=price_range,
        )

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _sort_items(
        self, items: list[ContentItem], sort_by: SortOrder
    ) -> list[ContentItem]:
        """Sort items by the specified criteria.

        Args:
            items: List of items to sort.
            sort_by: The sort order to apply.

        Returns:
            Sorted list of items.
        """
        if sort_by == SortOrder.PRICE_ASC:
            return sorted(items, key=lambda i: i.price)
        elif sort_by == SortOrder.PRICE_DESC:
            return sorted(items, key=lambda i: i.price, reverse=True)
        elif sort_by == SortOrder.RATING_DESC:
            return sorted(items, key=lambda i: i.rating, reverse=True)
        elif sort_by == SortOrder.NEWEST:
            return sorted(items, key=lambda i: i.created_at, reverse=True)
        elif sort_by == SortOrder.POPULARITY:
            return sorted(items, key=lambda i: i.sales_count, reverse=True)
        else:  # RELEVANCE — default sort by rating then sales
            return sorted(
                items, key=lambda i: (i.rating, i.sales_count), reverse=True
            )


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def search_marketplace(
    query: str, filters: Optional[MarketplaceFilters] = None
) -> SearchResult:
    """Convenience function to search the marketplace.

    Creates a default ContentMarketplaceAgent and performs the search.

    Args:
        query: The search string.
        filters: Optional search filters.

    Returns:
        SearchResult with matching items.
    """
    agent = ContentMarketplaceAgent()
    return agent.search_marketplace(query, filters)


def get_marketplace_stats() -> MarketplaceStats:
    """Convenience function to get marketplace statistics.

    Creates a default ContentMarketplaceAgent and returns stats.

    Returns:
        MarketplaceStats with aggregate metrics.
    """
    agent = ContentMarketplaceAgent()
    return agent.get_marketplace_stats()
