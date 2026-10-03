"""Edge case data generators for UGC Marketplace database seeders.

This module generates edge case data including null values, boundary values,
unicode characters, and other special cases that test the robustness of
the database schema and application logic.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from faker import Faker

faker = Faker()

from sqlalchemy.orm import Session

from ugc_marketplace.database.seeders.models import (AnalyticsEvent, AuditLog,
                                                     Content, ContentStatus,
                                                     Creator, FraudReport,
                                                     FraudReportStatus,
                                                     License, LicenseType,
                                                     Listing, PaymentStatus,
                                                     QualityScore, Transaction,
                                                     VerificationStatus)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unicode and Special Character Data
# ---------------------------------------------------------------------------
UNICODE_USERNAMES = [
    "用户_测试",
    "utilisateur_test",
    "benutzer_test",
    "사용자_테스트",
    "उपयोगकर्ता_परीक्षण",
    "مستخدم_اختبار",
    "χρήστης_δοκιμή",
    "пользователь_тест",
    "kullanıcı_test",
    "người_dùng_kiểm_tra",
]

UNICODE_DISPLAY_NAMES = [
    "José García Márquez",
    "François Müller",
    "Björn Guðmundsdóttir",
    "Александр Сергеевич Пушкин",
    "李白",
    "محمد بن راشد",
    "המלך דוד",
    "Σωκράτης",
    "Zdzisław Beksiński",
    "Žĺščť Žĺščť",
]

UNICODE_BIOS = [
    "🎨 Digital artist specializing in 3D character design. 日本語も話せます。",
    "Music producer | 音乐制作人 | Producteur de musique | 音乐制作人",
    "Photographer capturing the world 📸 | مصور | Фотограф | 摄影师",
    "Game developer 🎮 | 游戏开发者 | Desarrollador de juegos | ゲーム開発者",
    "Animator bringing characters to life ✨ | 动画师 | Animateur | アニメーター",
]

UNICODE_TITLES = [
    "Fantasy Character Pack - ファンタジーキャラクター",
    "Sci-Fi Environment Bundle - 科幻环境包",
    "Medieval Weapon Collection - 中世武器コレクション",
    "Cyberpunk UI Kit - サイバーパンクUIキット",
    "Nature Soundscape - 自然のサウンドスケープ",
    "Epic Orchestral Theme - 史诗的管弦乐主题",
    "Pixel Art Tileset - ピクセルアートタイルセット",
    "3D Vehicle Models - 3Dビークルモデル",
]

UNICODE_DESCRIPTIONS = [
    "This pack includes 50+ high-quality 3D models with PBR textures. "
    "すべてのモデルはPBRテクスチャを備えています。"
    "Perfect for game development, architectural visualization, and film production.",
    "A comprehensive collection of sci-fi sound effects. "
    "包括激光、爆炸、环境音等。"
    "Ideal for games, films, and multimedia projects.",
    "Professional-grade animation rigs for humanoid characters. "
    "プロフェッショナルグレードのリグ。"
    "Compatible with major 3D software packages.",
]

UNICODE_TAGS = [
    "3d",
    "2d",
    "アニメ",
    "ゲーム",
    "映画",
    "music",
    "sfx",
    "ambient",
    "サイバーパンク",
    "ファンタジー",
    "中世",
    "科幻",
    "像素",
    "复古",
    "cyberpunk",
    "fantasy",
    "medieval",
    "scifi",
    "pixel-art",
    "retro",
]

# ---------------------------------------------------------------------------
# Boundary Values
# ---------------------------------------------------------------------------
BOUNDARY_PRICES = [
    Decimal("0.00"),  # Free
    Decimal("0.01"),  # Minimum non-zero
    Decimal("0.99"),  # Common minimum
    Decimal("999.99"),  # Common maximum
    Decimal("9999.99"),  # High value
    Decimal("99999.99"),  # Very high value
    Decimal("999999.99"),  # Near max for NUMERIC(12,2)
]

BOUNDARY_REPUTATION_SCORES = [
    Decimal("0.00"),  # Minimum
    Decimal("0.01"),  # Near minimum
    Decimal("50.00"),  # Middle
    Decimal("99.99"),  # Near maximum
    Decimal("100.00"),  # Maximum
]

BOUNDARY_QUALITY_SCORES = [
    Decimal("0.000"),  # Minimum
    Decimal("0.001"),  # Near minimum
    Decimal("0.500"),  # Middle
    Decimal("0.999"),  # Near maximum
    Decimal("1.000"),  # Maximum
]

BOUNDARY_COUNTS = [
    0,  # Zero
    1,  # One
    999,  # Three digits
    1000,  # Four digits
    99999,  # Five digits
    100000,  # Six digits
]

BOUNDARY_STRING_LENGTHS = [
    "",  # Empty (where allowed)
    "a",  # Single char
    "a" * 50,  # Max username length
    "a" * 100,  # Max display_name length
    "a" * 255,  # Max title length
    "a" * 500,  # Max bio length
    "a" * 1000,  # Max description length
]

BOUNDARY_DATES = [
    datetime(1970, 1, 1, tzinfo=UTC),  # Unix epoch
    datetime(2000, 1, 1, tzinfo=UTC),  # Y2K
    datetime(2020, 2, 29, tzinfo=UTC),  # Leap day
    datetime(2038, 1, 19, tzinfo=UTC),  # 32-bit timestamp limit
    datetime.now(UTC),  # Now
    datetime.now(UTC) + timedelta(days=365),  # Future
]

BOUNDARY_JSON_DATA = [
    {},  # Empty object
    {"key": "value"},  # Simple
    {"nested": {"deeply": {"nested": {"value": "test"}}}},  # Deeply nested
    {"array": [1, 2, 3, 4, 5]},  # Array
    {
        "mixed": {"string": "value", "number": 42, "bool": True, "null": None}
    },  # Mixed types
    {"unicode": "日本語テスト", "emoji": "🎨🎮🎵"},  # Unicode
    {"special": {"chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"}},  # Special chars
]


# ---------------------------------------------------------------------------
# Edge Case Creator Generation
# ---------------------------------------------------------------------------
def seed_edge_case_creators(session: Session, count: int = 20) -> list[Creator]:
    """Generate creators with edge case data.

    Args:
        session: SQLAlchemy session.
        count: Number of edge case creators to create.

    Returns:
        List of created Creator instances.
    """
    creators: list[Creator] = []

    for i in range(count):
        edge_type = i % 10

        if edge_type == 0:
            # Unicode username
            creator = Creator(
                id=uuid4(),
                username=UNICODE_USERNAMES[i % len(UNICODE_USERNAMES)],
                email=f"unicode_{i}@example.com",
                display_name=UNICODE_DISPLAY_NAMES[i % len(UNICODE_DISPLAY_NAMES)],
                bio=UNICODE_BIOS[i % len(UNICODE_BIOS)],
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # Boundary reputation score (min)
            creator = Creator(
                id=uuid4(),
                username=f"boundary_min_{i}",
                email=f"boundary_min_{i}@example.com",
                display_name="Boundary Min",
                bio=None,
                avatar_url=None,
                website_url=None,
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("0.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # Boundary reputation score (max)
            creator = Creator(
                id=uuid4(),
                username=f"boundary_max_{i}",
                email=f"boundary_max_{i}@example.com",
                display_name="Boundary Max",
                bio=None,
                avatar_url=None,
                website_url=None,
                social_links={},
                verification_status=VerificationStatus.VERIFIED,
                reputation_score=Decimal("100.00"),
                total_earnings=Decimal("9999999999999.99"),
                total_sales=999999,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # All null optional fields
            creator = Creator(
                id=uuid4(),
                username=f"null_fields_{i}",
                email=f"null_fields_{i}@example.com",
                display_name=None,
                bio=None,
                avatar_url=None,
                website_url=None,
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("0.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # Maximum length strings
            creator = Creator(
                id=uuid4(),
                username=f"max_len_{i}",
                email=f"max_len_{i}@example.com",
                display_name="a" * 100,
                bio="a" * 500,
                avatar_url="https://example.com/" + "a" * 200,
                website_url="https://example.com/" + "a" * 200,
                social_links={"key" * 50: "value" * 50},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 5:
            # Special characters in strings
            creator = Creator(
                id=uuid4(),
                username=f"special_chars_{i}",
                email=f"special_chars_{i}@example.com",
                display_name="!@#$%^&*()_+-=[]{}|;':\",./<>?",
                bio="Special chars: \n\r\t\b\f\v\0",
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 6:
            # Emoji in display name
            creator = Creator(
                id=uuid4(),
                username=f"emoji_{i}",
                email=f"emoji_{i}@example.com",
                display_name="🎨 Artist 🎮 Gamer 🎵 Musician",
                bio="Creating amazing content! 🚀✨🎉",
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 7:
            # RTL (Right-to-Left) text
            creator = Creator(
                id=uuid4(),
                username=f"rtl_{i}",
                email=f"rtl_{i}@example.com",
                display_name="משתמש לבדיקה",
                bio="זה ביוגרפיה בעברית",
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 8:
            # Mixed scripts
            creator = Creator(
                id=uuid4(),
                username=f"mixed_{i}",
                email=f"mixed_{i}@example.com",
                display_name="Test 测试 テスト 테스트 परीक्षण",
                bio="Mixed: English 中文 日本語 한국어 हिन्दी",
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Very long unicode strings
            creator = Creator(
                id=uuid4(),
                username=f"long_unicode_{i}",
                email=f"long_unicode_{i}@example.com",
                display_name="日本語" * 33,  # 99 chars
                bio="中文" * 250,  # 500 chars
                social_links={},
                verification_status=VerificationStatus.UNVERIFIED,
                reputation_score=Decimal("50.00"),
                total_earnings=Decimal("0.00"),
                total_sales=0,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        session.add(creator)
        creators.append(creator)

    session.flush()
    logger.info("Seeded %d edge case creators", len(creators))
    return creators


# ---------------------------------------------------------------------------
# Edge Case Content Generation
# ---------------------------------------------------------------------------
def seed_edge_case_content(
    session: Session,
    creators: list[Creator],
    count: int = 20,
) -> list[Content]:
    """Generate content items with edge case data.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        count: Number of edge case content items to create.

    Returns:
        List of created Content instances.
    """
    content_items: list[Content] = []

    for i in range(count):
        creator = creators[i % len(creators)]
        edge_type = i % 8

        if edge_type == 0:
            # Unicode title
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=UNICODE_TITLES[i % len(UNICODE_TITLES)],
                description=UNICODE_DESCRIPTIONS[i % len(UNICODE_DESCRIPTIONS)],
                content_type="3d_model",
                media_urls=[],
                tags=UNICODE_TAGS[:5],
                metadata_={},
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=0,
                like_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # Boundary view/like counts
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"Boundary counts {i}",
                description=None,
                content_type="2d_art",
                media_urls=[],
                tags=[],
                metadata_={},
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=BOUNDARY_COUNTS[i % len(BOUNDARY_COUNTS)],
                like_count=BOUNDARY_COUNTS[(i + 3) % len(BOUNDARY_COUNTS)],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # Maximum length title
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title="a" * 255,
                description="a" * 1000,
                content_type="audio",
                media_urls=["https://example.com/" + "a" * 200],
                tags=["tag" * 50],
                metadata_={"key": "value" * 100},
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=0,
                like_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # Empty arrays and objects
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"Empty collections {i}",
                description=None,
                content_type="video",
                media_urls=[],
                tags=[],
                metadata_={},
                status=ContentStatus.DRAFT,
                is_nsfw=False,
                view_count=0,
                like_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # NSFW content
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"NSFW content {i}",
                description="Adult content",
                content_type="photography",
                media_urls=[],
                tags=["nsfw", "adult"],
                metadata_={},
                status=ContentStatus.PUBLISHED,
                is_nsfw=True,
                view_count=100,
                like_count=10,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 5:
            # All content types
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"Content type test {i}",
                description="Testing all content types",
                content_type=[
                    "3d_model",
                    "2d_art",
                    "audio",
                    "video",
                    "animation",
                    "texture",
                    "vfx",
                    "music",
                    "sound_effect",
                    "photography",
                    "illustration",
                    "game_asset",
                ][i % 12],
                media_urls=[f"https://example.com/file_{j}.ext" for j in range(5)],
                tags=UNICODE_TAGS[i % len(UNICODE_TAGS) :],
                metadata_={"format": "test", "version": "1.0"},
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=i * 100,
                like_count=i * 10,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 6:
            # Special characters in metadata
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"Special metadata {i}",
                description="Testing special characters in metadata",
                content_type="game_asset",
                media_urls=[],
                tags=[],
                metadata_={
                    "unicode": "日本語",
                    "emoji": "🎨🎮",
                    "special": "!@#$%^&*()",
                    "newline": "line1\nline2",
                    "tab": "col1\tcol2",
                    "quotes": 'He said "hello"',
                    "backslash": "path\\to\\file",
                },
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=0,
                like_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Very long tags array
            content = Content(
                id=uuid4(),
                creator_id=creator.id,
                title=f"Many tags {i}",
                description="Testing with many tags",
                content_type="illustration",
                media_urls=[],
                tags=[f"tag_{j}" for j in range(100)],
                metadata_={},
                status=ContentStatus.PUBLISHED,
                is_nsfw=False,
                view_count=0,
                like_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        session.add(content)
        content_items.append(content)

    session.flush()
    logger.info("Seeded %d edge case content items", len(content_items))
    return content_items


# ---------------------------------------------------------------------------
# Edge Case Listing Generation
# ---------------------------------------------------------------------------
def seed_edge_case_listings(
    session: Session,
    content_items: list[Content],
    creators: list[Creator],
    count: int = 20,
) -> list[Listing]:
    """Generate listings with edge case data.

    Args:
        session: SQLAlchemy session.
        content_items: List of Content instances.
        creators: List of Creator instances.
        count: Number of edge case listings to create.

    Returns:
        List of created Listing instances.
    """
    listings: list[Listing] = []

    for i in range(count):
        content = content_items[i % len(content_items)]
        creator = content.creator
        edge_type = i % 6

        if edge_type == 0:
            # Boundary prices
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"Boundary price {i}",
                description=None,
                price=BOUNDARY_PRICES[i % len(BOUNDARY_PRICES)],
                currency="USD",
                license_type="personal",
                usage_rights={},
                is_active=True,
                sales_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # All currencies
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"Currency test {i}",
                description="Testing all currencies",
                price=Decimal("99.99"),
                currency=["USD", "EUR", "GBP", "JPY", "CAD", "AUD"][i % 6],
                license_type="commercial",
                usage_rights={"commercial_use": True},
                is_active=True,
                sales_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # All license types
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"License type test {i}",
                description="Testing all license types",
                price=Decimal("49.99"),
                currency="USD",
                license_type=[
                    "personal",
                    "commercial",
                    "extended",
                    "single",
                    "exclusive",
                ][i % 5],
                usage_rights={},
                is_active=True,
                sales_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # Inactive listing
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"Inactive listing {i}",
                description="This listing is inactive",
                price=Decimal("29.99"),
                currency="USD",
                license_type="personal",
                usage_rights={},
                is_active=False,
                sales_count=100,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # Maximum sales count
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"Max sales {i}",
                description="High sales count",
                price=Decimal("9.99"),
                currency="USD",
                license_type="personal",
                usage_rights={},
                is_active=True,
                sales_count=99999,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Complex usage rights
            listing = Listing(
                id=uuid4(),
                content_id=content.id,
                creator_id=creator.id,
                title=f"Complex rights {i}",
                description="Complex usage rights",
                price=Decimal("199.99"),
                currency="EUR",
                license_type="extended",
                usage_rights={
                    "commercial_use": True,
                    "modification": True,
                    "redistribution": False,
                    "attribution": True,
                    "unlimited_projects": True,
                    "project_limit": None,
                    "seat_count": 50,
                    "custom_clause": "Additional terms apply",
                },
                is_active=True,
                sales_count=0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        session.add(listing)
        listings.append(listing)

    session.flush()
    logger.info("Seeded %d edge case listings", len(listings))
    return listings


# ---------------------------------------------------------------------------
# Edge Case Transaction Generation
# ---------------------------------------------------------------------------
def seed_edge_case_transactions(
    session: Session,
    listings: list[Listing],
    creators: list[Creator],
    count: int = 20,
) -> list[Transaction]:
    """Generate transactions with edge case data.

    Args:
        session: SQLAlchemy session.
        listings: List of Listing instances.
        creators: List of Creator instances.
        count: Number of edge case transactions to create.

    Returns:
        List of created Transaction instances.
    """
    transactions: list[Transaction] = []

    for i in range(count):
        listing = listings[i % len(listings)]
        seller = listing.creator

        # Pick a buyer that's not the seller
        buyer = None
        for c in creators:
            if c.id != seller.id:
                buyer = c
                break

        if buyer is None:
            continue

        edge_type = i % 6

        if edge_type == 0:
            # Boundary amounts
            amount = BOUNDARY_PRICES[i % len(BOUNDARY_PRICES)]
            platform_fee = (
                Decimal("0.00")
                if amount == Decimal("0.00")
                else amount * Decimal("0.10")
            )
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=amount,
                currency=listing.currency,
                platform_fee=platform_fee,
                seller_earnings=amount - platform_fee,
                payment_method="stripe",
                payment_status=PaymentStatus.COMPLETED,
                metadata_={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # All payment methods
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=listing.price,
                currency=listing.currency,
                platform_fee=listing.price * Decimal("0.10"),
                seller_earnings=listing.price * Decimal("0.90"),
                payment_method=[
                    "stripe",
                    "paypal",
                    "crypto",
                    "bank_transfer",
                    "credit_card",
                ][i % 5],
                payment_status=PaymentStatus.COMPLETED,
                metadata_={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # All payment statuses
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=listing.price,
                currency=listing.currency,
                platform_fee=listing.price * Decimal("0.10"),
                seller_earnings=listing.price * Decimal("0.90"),
                payment_method="stripe",
                payment_status=[
                    PaymentStatus.PENDING,
                    PaymentStatus.COMPLETED,
                    PaymentStatus.FAILED,
                    PaymentStatus.REFUNDED,
                    PaymentStatus.DISPUTED,
                ][i % 5],
                metadata_={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # With Stripe payment intent ID
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=listing.price,
                currency=listing.currency,
                platform_fee=listing.price * Decimal("0.10"),
                seller_earnings=listing.price * Decimal("0.90"),
                payment_method="stripe",
                payment_status=PaymentStatus.COMPLETED,
                stripe_payment_intent_id=f"pi_3{faker.lexify(text='????????????????????????????????')}",
                metadata_={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # Complex metadata
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=listing.price,
                currency=listing.currency,
                platform_fee=listing.price * Decimal("0.10"),
                seller_earnings=listing.price * Decimal("0.90"),
                payment_method="stripe",
                payment_status=PaymentStatus.COMPLETED,
                metadata_={
                    "ip_country": "US",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0",
                    "referrer": "https://google.com",
                    "campaign": "summer_sale",
                    "discount_code": "SUMMER20",
                    "custom_data": {"key": "value"},
                },
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Zero amount transaction
            transaction = Transaction(
                id=uuid4(),
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=Decimal("0.00"),
                currency=listing.currency,
                platform_fee=Decimal("0.00"),
                seller_earnings=Decimal("0.00"),
                payment_method="stripe",
                payment_status=PaymentStatus.COMPLETED,
                metadata_={"free": True, "promotion": "launch"},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        session.add(transaction)
        transactions.append(transaction)

    session.flush()
    logger.info("Seeded %d edge case transactions", len(transactions))
    return transactions


# ---------------------------------------------------------------------------
# Edge Case License Generation
# ---------------------------------------------------------------------------
def seed_edge_case_licenses(
    session: Session,
    transactions: list[Transaction],
    count: int = 20,
) -> list[License]:
    """Generate licenses with edge case data.

    Args:
        session: SQLAlchemy session.
        transactions: List of Transaction instances.
        count: Number of edge case licenses to create.

    Returns:
        List of created License instances.
    """
    licenses: list[License] = []

    for i in range(count):
        # Find a completed transaction
        completed_txns = [
            t for t in transactions if t.payment_status == PaymentStatus.COMPLETED
        ]
        if not completed_txns:
            break

        transaction = completed_txns[i % len(completed_txns)]
        edge_type = i % 5

        if edge_type == 0:
            # Perpetual license (no expiration)
            license_obj = License(
                id=uuid4(),
                transaction_id=transaction.id,
                licensee_id=transaction.buyer_id,
                licensor_id=transaction.seller_id,
                content_id=transaction.listing.content_id,
                license_type=LicenseType.PERSONAL,
                usage_scope={},
                valid_from=datetime.now(UTC),
                valid_until=None,
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # Expired license
            license_obj = License(
                id=uuid4(),
                transaction_id=transaction.id,
                licensee_id=transaction.buyer_id,
                licensor_id=transaction.seller_id,
                content_id=transaction.listing.content_id,
                license_type=LicenseType.COMMERCIAL,
                usage_scope={},
                valid_from=datetime.now(UTC) - timedelta(days=365),
                valid_until=datetime.now(UTC) - timedelta(days=1),
                is_active=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # All license types
            license_obj = License(
                id=uuid4(),
                transaction_id=transaction.id,
                licensee_id=transaction.buyer_id,
                licensor_id=transaction.seller_id,
                content_id=transaction.listing.content_id,
                license_type=[
                    LicenseType.PERSONAL,
                    LicenseType.COMMERCIAL,
                    LicenseType.EXTENDED,
                    LicenseType.SINGLE,
                    LicenseType.EXCLUSIVE,
                ][i % 5],
                usage_scope={},
                valid_from=datetime.now(UTC),
                valid_until=datetime.now(UTC) + timedelta(days=365),
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # Complex usage scope
            license_obj = License(
                id=uuid4(),
                transaction_id=transaction.id,
                licensee_id=transaction.buyer_id,
                licensor_id=transaction.seller_id,
                content_id=transaction.listing.content_id,
                license_type=LicenseType.EXTENDED,
                usage_scope={
                    "project_limit": "unlimited",
                    "seat_count": 100,
                    "redistribution": True,
                    "commercial_use": True,
                    "modification": True,
                    "sublicense": True,
                    "territory": "worldwide",
                    "media": ["digital", "print", "broadcast"],
                },
                valid_from=datetime.now(UTC),
                valid_until=datetime.now(UTC) + timedelta(days=365 * 5),
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Inactive license
            license_obj = License(
                id=uuid4(),
                transaction_id=transaction.id,
                licensee_id=transaction.buyer_id,
                licensor_id=transaction.seller_id,
                content_id=transaction.listing.content_id,
                license_type=LicenseType.SINGLE,
                usage_scope={},
                valid_from=datetime.now(UTC),
                valid_until=datetime.now(UTC) + timedelta(days=30),
                is_active=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        session.add(license_obj)
        licenses.append(license_obj)

    session.flush()
    logger.info("Seeded %d edge case licenses", len(licenses))
    return licenses


# ---------------------------------------------------------------------------
# Edge Case Quality Score Generation
# ---------------------------------------------------------------------------
def seed_edge_case_quality_scores(
    session: Session,
    content_items: list[Content],
    count: int = 20,
) -> list[QualityScore]:
    """Generate quality scores with edge case data.

    Args:
        session: SQLAlchemy session.
        content_items: List of Content instances.
        count: Number of edge case quality scores to create.

    Returns:
        List of created QualityScore instances.
    """
    scores: list[QualityScore] = []

    for i in range(count):
        content = content_items[i % len(content_items)]
        edge_type = i % 5

        if edge_type == 0:
            # Boundary scores (min)
            score = QualityScore(
                id=uuid4(),
                content_id=content.id,
                overall_score=Decimal("0.000"),
                technical_score=Decimal("0.000"),
                aesthetic_score=Decimal("0.000"),
                engagement_score=Decimal("0.000"),
                originality_score=Decimal("0.000"),
                scoring_model="quality-v1.0",
                details={},
                created_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # Boundary scores (max)
            score = QualityScore(
                id=uuid4(),
                content_id=content.id,
                overall_score=Decimal("1.000"),
                technical_score=Decimal("1.000"),
                aesthetic_score=Decimal("1.000"),
                engagement_score=Decimal("1.000"),
                originality_score=Decimal("1.000"),
                scoring_model="quality-v2.1",
                details={},
                created_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # Null sub-scores
            score = QualityScore(
                id=uuid4(),
                content_id=content.id,
                overall_score=Decimal("0.500"),
                technical_score=None,
                aesthetic_score=None,
                engagement_score=None,
                originality_score=None,
                scoring_model=None,
                details={},
                created_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # All scoring models
            score = QualityScore(
                id=uuid4(),
                content_id=content.id,
                overall_score=BOUNDARY_QUALITY_SCORES[i % len(BOUNDARY_QUALITY_SCORES)],
                technical_score=BOUNDARY_QUALITY_SCORES[
                    (i + 1) % len(BOUNDARY_QUALITY_SCORES)
                ],
                aesthetic_score=BOUNDARY_QUALITY_SCORES[
                    (i + 2) % len(BOUNDARY_QUALITY_SCORES)
                ],
                engagement_score=BOUNDARY_QUALITY_SCORES[
                    (i + 3) % len(BOUNDARY_QUALITY_SCORES)
                ],
                originality_score=BOUNDARY_QUALITY_SCORES[
                    (i + 4) % len(BOUNDARY_QUALITY_SCORES)
                ],
                scoring_model=[
                    "quality-v2.1",
                    "quality-v2.0",
                    "quality-v1.5",
                    "quality-v1.0",
                ][i % 4],
                details={},
                created_at=datetime.now(UTC),
            )
        else:
            # Complex details
            score = QualityScore(
                id=uuid4(),
                content_id=content.id,
                overall_score=Decimal("0.750"),
                technical_score=Decimal("0.800"),
                aesthetic_score=Decimal("0.700"),
                engagement_score=Decimal("0.600"),
                originality_score=Decimal("0.900"),
                scoring_model="quality-v2.1",
                details={
                    "texture_quality": "excellent",
                    "rigging": "professional",
                    "optimization": "excellent",
                    "modularity": "excellent",
                    "consistency": "perfect",
                    "coverage": "comprehensive",
                    "custom_metrics": {
                        "polycount_efficiency": 0.95,
                        "texture_resolution": "4k",
                        "animation_quality": "smooth",
                    },
                },
                created_at=datetime.now(UTC),
            )

        session.add(score)
        scores.append(score)

    session.flush()
    logger.info("Seeded %d edge case quality scores", len(scores))
    return scores


# ---------------------------------------------------------------------------
# Edge Case Fraud Report Generation
# ---------------------------------------------------------------------------
def seed_edge_case_fraud_reports(
    session: Session,
    creators: list[Creator],
    content_items: list[Content],
    listings: list[Listing],
    count: int = 20,
) -> list[FraudReport]:
    """Generate fraud reports with edge case data.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        content_items: List of Content instances.
        listings: List of Listing instances.
        count: Number of edge case fraud reports to create.

    Returns:
        List of created FraudReport instances.
    """
    reports: list[FraudReport] = []

    for i in range(count):
        reporter = creators[i % len(creators)]
        edge_type = i % 6

        if edge_type == 0:
            # All report types
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                reported_listing_id=None,
                reported_user_id=None,
                report_type=[
                    "copyright",
                    "fraud",
                    "spam",
                    "impersonation",
                    "prohibited_content",
                    "other",
                ][i % 6],
                description="Testing all report types",
                evidence={},
                status=FraudReportStatus.OPEN,
                resolution=None,
                resolved_by=None,
                resolved_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # All statuses
            status = [
                FraudReportStatus.OPEN,
                FraudReportStatus.INVESTIGATING,
                FraudReportStatus.RESOLVED,
                FraudReportStatus.DISMISSED,
                FraudReportStatus.ESCALATED,
            ][i % 5]
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=None,
                reported_listing_id=(
                    listings[i % len(listings)].id if listings else None
                ),
                reported_user_id=None,
                report_type="fraud",
                description="Testing all statuses",
                evidence={},
                status=status,
                resolution=(
                    "Resolved"
                    if status
                    in (FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED)
                    else None
                ),
                resolved_by=(
                    creators[(i + 1) % len(creators)].id
                    if status
                    in (FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED)
                    else None
                ),
                resolved_at=(
                    datetime.now(UTC)
                    if status
                    in (FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED)
                    else None
                ),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # Report against user
            reported_user = creators[(i + 1) % len(creators)]
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=None,
                reported_listing_id=None,
                reported_user_id=reported_user.id,
                report_type="impersonation",
                description="User impersonation report",
                evidence={},
                status=FraudReportStatus.OPEN,
                resolution=None,
                resolved_by=None,
                resolved_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # Complex evidence
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                reported_listing_id=None,
                reported_user_id=None,
                report_type="copyright",
                description="Copyright infringement with evidence",
                evidence={
                    "urls": [f"https://example.com/evidence_{j}" for j in range(5)],
                    "similarity_score": 0.95,
                    "screenshots": [
                        f"https://example.com/screenshot_{j}.png" for j in range(3)
                    ],
                    "communication_logs": [f"Log entry {j}" for j in range(10)],
                    "original_work_url": "https://original.example.com",
                    "registration_number": "VA000123456",
                },
                status=FraudReportStatus.INVESTIGATING,
                resolution=None,
                resolved_by=None,
                resolved_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # No description
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=None,
                reported_listing_id=None,
                reported_user_id=None,
                report_type="spam",
                description=None,
                evidence={},
                status=FraudReportStatus.OPEN,
                resolution=None,
                resolved_by=None,
                resolved_at=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        else:
            # Resolved with full details
            report = FraudReport(
                id=uuid4(),
                reporter_id=reporter.id,
                reported_content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                reported_listing_id=None,
                reported_user_id=None,
                report_type="fraud",
                description="Resolved fraud report",
                evidence={},
                status=FraudReportStatus.RESOLVED,
                resolution="Content removed and user banned",
                resolved_by=creators[(i + 2) % len(creators)].id,
                resolved_at=datetime.now(UTC),
                created_at=datetime.now(UTC) - timedelta(days=30),
                updated_at=datetime.now(UTC),
            )

        session.add(report)
        reports.append(report)

    session.flush()
    logger.info("Seeded %d edge case fraud reports", len(reports))
    return reports


# ---------------------------------------------------------------------------
# Edge Case Analytics Event Generation
# ---------------------------------------------------------------------------
def seed_edge_case_analytics_events(
    session: Session,
    creators: list[Creator],
    content_items: list[Content],
    listings: list[Listing],
    count: int = 50,
) -> list[AnalyticsEvent]:
    """Generate analytics events with edge case data.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        content_items: List of Content instances.
        listings: List of Listing instances.
        count: Number of edge case analytics events to create.

    Returns:
        List of created AnalyticsEvent instances.
    """
    events: list[AnalyticsEvent] = []

    for i in range(count):
        edge_type = i % 6

        if edge_type == 0:
            # All event types
            event = AnalyticsEvent(
                id=uuid4(),
                event_type=[
                    "page_view",
                    "add_to_cart",
                    "purchase_complete",
                    "search",
                    "content_like",
                    "content_share",
                    "content_download",
                    "listing_view",
                    "profile_view",
                ][i % 9],
                user_id=creators[i % len(creators)].id if creators else None,
                content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                listing_id=listings[i % len(listings)].id if listings else None,
                session_id=uuid4(),
                ip_address=f"192.168.{i % 256}.{(i + 1) % 256}",
                user_agent="Mozilla/5.0",
                referrer=None,
                event_data={},
                created_at=datetime.now(UTC),
            )
        elif edge_type == 1:
            # Anonymous event (no user)
            event = AnalyticsEvent(
                id=uuid4(),
                event_type="page_view",
                user_id=None,
                content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                listing_id=None,
                session_id=uuid4(),
                ip_address="10.0.0.1",
                user_agent="Bot/1.0",
                referrer="https://google.com",
                event_data={"page": "/home"},
                created_at=datetime.now(UTC),
            )
        elif edge_type == 2:
            # Complex event data
            event = AnalyticsEvent(
                id=uuid4(),
                event_type="search",
                user_id=creators[i % len(creators)].id if creators else None,
                content_id=None,
                listing_id=None,
                session_id=uuid4(),
                ip_address="172.16.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                referrer="https://www.google.com/search?q=test",
                event_data={
                    "page": "/search",
                    "duration_seconds": 120,
                    "query": "3d character model",
                    "results_count": 150,
                    "filters": {"category": "3d", "price_max": 100},
                    "sort_by": "relevance",
                },
                created_at=datetime.now(UTC),
            )
        elif edge_type == 3:
            # Unicode in event data
            event = AnalyticsEvent(
                id=uuid4(),
                event_type="search",
                user_id=creators[i % len(creators)].id if creators else None,
                content_id=None,
                listing_id=None,
                session_id=uuid4(),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                referrer=None,
                event_data={
                    "page": "/search",
                    "query": "日本語 3Dモデル",
                    "results_count": 25,
                },
                created_at=datetime.now(UTC),
            )
        elif edge_type == 4:
            # All relationships set
            event = AnalyticsEvent(
                id=uuid4(),
                event_type="purchase_complete",
                user_id=creators[i % len(creators)].id if creators else None,
                content_id=(
                    content_items[i % len(content_items)].id if content_items else None
                ),
                listing_id=listings[i % len(listings)].id if listings else None,
                session_id=uuid4(),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                referrer="https://example.com/listing/123",
                event_data={"price": 49.99, "currency": "USD"},
                created_at=datetime.now(UTC),
            )
        else:
            # Minimal event
            event = AnalyticsEvent(
                id=uuid4(),
                event_type="page_view",
                user_id=None,
                content_id=None,
                listing_id=None,
                session_id=uuid4(),
                ip_address=None,
                user_agent=None,
                referrer=None,
                event_data={},
                created_at=datetime.now(UTC),
            )

        session.add(event)
        events.append(event)

    session.flush()
    logger.info("Seeded %d edge case analytics events", len(events))
    return events


# ---------------------------------------------------------------------------
# Edge Case Audit Log Generation
# ---------------------------------------------------------------------------
def seed_edge_case_audit_logs(
    session: Session,
    creators: list[Creator],
    count: int = 20,
) -> list[AuditLog]:
    """Generate audit log entries with edge case data.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        count: Number of edge case audit log entries to create.

    Returns:
        List of created AuditLog instances.
    """
    logs: list[AuditLog] = []

    for i in range(count):
        edge_type = i % 5

        if edge_type == 0:
            # All actions
            log = AuditLog(
                id=uuid4(),
                table_name=[
                    "creators",
                    "content",
                    "listings",
                    "transactions",
                    "licenses",
                ][i % 5],
                record_id=uuid4(),
                action=["INSERT", "UPDATE", "DELETE"][i % 3],
                old_values=None,
                new_values={"field": "value"},
                changed_by=creators[i % len(creators)].id if creators else None,
                changed_at=datetime.now(UTC),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )
        elif edge_type == 1:
            # Update with old and new values
            log = AuditLog(
                id=uuid4(),
                table_name="content",
                record_id=uuid4(),
                action="UPDATE",
                old_values={"title": "Old Title", "status": "draft"},
                new_values={"title": "New Title", "status": "published"},
                changed_by=creators[i % len(creators)].id if creators else None,
                changed_at=datetime.now(UTC),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )
        elif edge_type == 2:
            # Delete with old values only
            log = AuditLog(
                id=uuid4(),
                table_name="listings",
                record_id=uuid4(),
                action="DELETE",
                old_values={"title": "Deleted Listing", "price": 49.99},
                new_values=None,
                changed_by=creators[i % len(creators)].id if creators else None,
                changed_at=datetime.now(UTC),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )
        elif edge_type == 3:
            # Anonymous change (no changed_by)
            log = AuditLog(
                id=uuid4(),
                table_name="creators",
                record_id=uuid4(),
                action="INSERT",
                old_values=None,
                new_values={"username": "new_user"},
                changed_by=None,
                changed_at=datetime.now(UTC),
                ip_address=None,
                user_agent=None,
            )
        else:
            # Complex values
            log = AuditLog(
                id=uuid4(),
                table_name="transactions",
                record_id=uuid4(),
                action="UPDATE",
                old_values={
                    "status": "pending",
                    "amount": 49.99,
                    "metadata": {"key": "value"},
                },
                new_values={
                    "status": "completed",
                    "amount": 49.99,
                    "metadata": {"key": "updated", "stripe_id": "pi_123"},
                },
                changed_by=creators[i % len(creators)].id if creators else None,
                changed_at=datetime.now(UTC),
                ip_address="10.0.0.1",
                user_agent="AdminPanel/1.0",
            )

        session.add(log)
        logs.append(log)

    session.flush()
    logger.info("Seeded %d edge case audit logs", len(logs))
    return logs


# ---------------------------------------------------------------------------
# Main Edge Case Seeding Function
# ---------------------------------------------------------------------------
def seed_edge_cases(session: Session) -> dict[str, list[Any]]:
    """Seed all edge case data.

    This is the main entry point for seeding edge case data. It creates
    a comprehensive set of edge case data across all entity types.

    Args:
        session: SQLAlchemy session.

    Returns:
        Dictionary with lists of created instances by type.
    """
    logger.info("Starting edge case data seeding")

    creators = seed_edge_case_creators(session, count=20)
    content_items = seed_edge_case_content(session, creators, count=20)
    listings = seed_edge_case_listings(session, content_items, creators, count=20)
    transactions = seed_edge_case_transactions(session, listings, creators, count=20)
    licenses = seed_edge_case_licenses(session, transactions, count=20)
    quality_scores = seed_edge_case_quality_scores(session, content_items, count=20)
    fraud_reports = seed_edge_case_fraud_reports(
        session, creators, content_items, listings, count=20
    )
    analytics_events = seed_edge_case_analytics_events(
        session, creators, content_items, listings, count=50
    )
    audit_logs = seed_edge_case_audit_logs(session, creators, count=20)

    session.commit()
    logger.info("Edge case data seeding completed")

    return {
        "creators": creators,
        "content": content_items,
        "listings": listings,
        "transactions": transactions,
        "licenses": licenses,
        "quality_scores": quality_scores,
        "fraud_reports": fraud_reports,
        "analytics_events": analytics_events,
        "audit_logs": audit_logs,
    }
