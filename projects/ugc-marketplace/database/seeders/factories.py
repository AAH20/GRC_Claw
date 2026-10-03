"""factory_boy factories for all UGC Marketplace models.

These factories generate realistic test data with proper relationships
between models. They use faker for realistic fake data and support
both synchronous and asynchronous usage patterns.
"""

from __future__ import annotations

import random
from datetime import UTC
from decimal import Decimal
from uuid import uuid4

import factory
from factory import LazyAttribute, LazyFunction, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker as FakerInstance

from ugc_marketplace.database.seeders.models import (AnalyticsEvent, AuditLog,
                                                     Content, ContentStatus,
                                                     Creator, FraudReport,
                                                     FraudReportStatus,
                                                     License, LicenseType,
                                                     Listing, ModerationAction,
                                                     PaymentStatus,
                                                     QualityScore, Transaction,
                                                     VerificationStatus)

# Initialize faker with multiple locales for diverse data
faker = FakerInstance(["en_US", "en_GB", "de_DE", "fr_FR", "ja_JP"])

# ---------------------------------------------------------------------------
# Constants for realistic data generation
# ---------------------------------------------------------------------------
CONTENT_TYPES = [
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
]

LICENSE_TYPES = ["personal", "commercial", "extended", "single", "exclusive"]

MODERATION_ACTION_TYPES = [
    "approve",
    "reject",
    "flag",
    "remove",
    "restore",
    "warn",
    "suspend",
    "ban",
]

FRAUD_REPORT_TYPES = [
    "copyright",
    "fraud",
    "spam",
    "impersonation",
    "prohibited_content",
    "other",
]

PAYMENT_METHODS = ["stripe", "paypal", "crypto", "bank_transfer", "credit_card"]

EVENT_TYPES = [
    "page_view",
    "add_to_cart",
    "purchase_complete",
    "search",
    "content_like",
    "content_share",
    "content_download",
    "listing_view",
    "profile_view",
]

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]

SCORING_MODELS = ["quality-v2.1", "quality-v2.0", "quality-v1.5", "quality-v1.0"]

TAG_POOL = [
    "fantasy",
    "sci-fi",
    "character",
    "environment",
    "3d",
    "2d",
    "game-ready",
    "pixel-art",
    "tileset",
    "ui",
    "icons",
    "gaming",
    "interface",
    "ambient",
    "soundscape",
    "meditation",
    "game-audio",
    "cinematic",
    "orchestral",
    "trailer",
    "epic",
    "animation",
    "logo",
    "after-effects",
    "template",
    "explainer",
    "video",
    "music",
    "sound",
    "effect",
    "texture",
    "material",
    "rigged",
    "modular",
    "low-poly",
    "high-poly",
    "stylized",
    "realistic",
    "hand-painted",
    "vector",
    "raster",
    "4k",
    "hd",
    "loop",
    "one-shot",
    "foley",
    "sfx",
    "bgm",
    "ost",
    "remix",
    "cover",
    "mashup",
    "vocal",
    "instrumental",
    "acoustic",
    "electronic",
    "synth",
    "synthwave",
    "retrowave",
    "chiptune",
    "8-bit",
    "16-bit",
    "choir",
    "strings",
    "brass",
    "woodwind",
    "percussion",
    "drums",
    "bass",
    "guitar",
    "piano",
    "violin",
    "cello",
    "flute",
    "trumpet",
    "saxophone",
    "harp",
    "synthesizer",
    "pad",
    "lead",
    "pluck",
    "arp",
    "sequence",
    "sample",
    "preset",
    "patch",
    "bank",
    "expansion",
    "soundfont",
    "vst",
    "au",
    "aax",
    "rtas",
    "standalone",
    "plugin",
    "processor",
    "compressor",
    "eq",
    "reverb",
    "delay",
    "chorus",
    "flanger",
    "phaser",
    "distortion",
    "overdrive",
    "fuzz",
    "bitcrusher",
    "ring-mod",
    "vocoder",
    "talkbox",
    "auto-tune",
    "pitch-correction",
    "harmonizer",
    "doubler",
    "widener",
    "stereo-expander",
    "mid-side",
    "utility",
    "gain",
    "pan",
    "width",
    "limiter",
    "gate",
    "expander",
    "transient",
    "shaper",
    "envelope",
    "follower",
    "sidechain",
    "ducking",
    "pumping",
    "rhythm",
    "groove",
    "swing",
    "shuffle",
    "quantize",
    "humanize",
    "randomize",
    "velocity",
    "timing",
    "length",
    "duration",
    "multi-sample",
    "round-robin",
    "layered",
    "stacked",
    "mixed",
    "mastered",
    "stem",
    "track",
    "bus",
    "group",
    "aux",
    "send",
    "return",
    "insert",
    "fx",
    "modulation",
    "dynamics",
    "filter",
    "saturation",
    "exciter",
    "enhancer",
    "maximizer",
    "clipper",
    "dither",
    "noise-reduction",
    "de-esser",
    "de-click",
    "de-crackle",
    "de-hum",
    "de-noise",
    "de-reverb",
    "de-bleed",
    "de-phase",
    "de-clip",
    "repair",
    "restore",
    "remaster",
    "upmix",
    "downmix",
    "surround",
    "spatial",
    "immersive",
    "3d-audio",
    "binaural",
    "ambisonic",
    "dolby-atmos",
    "auro-3d",
    "dts-x",
    "sony-360",
    "vr",
    "ar",
    "xr",
    "mr",
    "360",
    "180",
    "stereoscopic",
    "mono",
    "stereo",
    "quad",
    "5.1",
    "7.1",
    "9.1",
    "11.1",
    "22.2",
]


# ---------------------------------------------------------------------------
# Base Factory
# ---------------------------------------------------------------------------
class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Creator Factory
# ---------------------------------------------------------------------------
class CreatorFactory(BaseFactory):
    """Factory for creating Creator instances."""

    class Meta:
        model = Creator

    id = LazyFunction(uuid4)
    username = factory.Sequence(lambda n: f"user_{n}_{faker.user_name()[:20]}")
    email = factory.Sequence(lambda n: f"user_{n}@{faker.free_email_domain()}")
    display_name = factory.LazyAttribute(lambda o: faker.name())
    bio = factory.LazyAttribute(
        lambda o: faker.text(max_nb_chars=500) if random.random() > 0.3 else None
    )
    avatar_url = factory.LazyAttribute(
        lambda o: (
            f"https://cdn.example.com/avatars/{o.username}.jpg"
            if random.random() > 0.3
            else None
        )
    )
    website_url = factory.LazyAttribute(
        lambda o: f"https://{o.username}.example.com" if random.random() > 0.5 else None
    )
    social_links = LazyFunction(
        lambda: {
            "twitter": f"@{faker.user_name()}" if random.random() > 0.5 else None,
            "instagram": f"@{faker.user_name()}" if random.random() > 0.5 else None,
            "github": faker.user_name() if random.random() > 0.7 else None,
            "youtube": faker.user_name() if random.random() > 0.7 else None,
            "tiktok": f"@{faker.user_name()}" if random.random() > 0.8 else None,
        }
    )
    verification_status = LazyFunction(lambda: random.choice(list(VerificationStatus)))
    reputation_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0, 100), 2)))
    )
    total_earnings = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0, 50000), 2)))
    )
    total_sales = LazyFunction(lambda: random.randint(0, 1000))
    is_active = LazyFunction(lambda: random.random() > 0.1)
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-2y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Content Factory
# ---------------------------------------------------------------------------
class ContentFactory(BaseFactory):
    """Factory for creating Content instances."""

    class Meta:
        model = Content

    id = LazyFunction(uuid4)
    creator = SubFactory(CreatorFactory)
    title = factory.LazyAttribute(
        lambda o: faker.sentence(nb_words=random.randint(2, 6))[:-1]
    )
    description = factory.LazyAttribute(
        lambda o: faker.text(max_nb_chars=1000) if random.random() > 0.2 else None
    )
    content_type = LazyFunction(lambda: random.choice(CONTENT_TYPES))
    media_urls = LazyFunction(
        lambda: [
            f"https://cdn.example.com/content/{faker.uuid4()[:8]}.{random.choice(['fbx', 'obj', 'png', 'jpg', 'wav', 'mp3', 'mp4', 'aep', 'zip'])}"
            for _ in range(random.randint(1, 5))
        ]
    )
    tags = LazyFunction(lambda: random.sample(TAG_POOL, k=random.randint(1, 6)))
    metadata_ = LazyFunction(
        lambda: {
            "format": random.choice(
                ["fbx", "obj", "png", "jpg", "wav", "mp3", "mp4", "aep", "zip"]
            ),
            "file_size_mb": round(random.uniform(0.1, 500), 2),
            "resolution": random.choice(
                ["1080p", "4k", "8k", "16x16", "32x32", "64x64"]
            ),
            "duration": (
                f"{random.randint(1, 60)}min" if random.random() > 0.5 else None
            ),
            "polycount": (
                f"{random.randint(1000, 500000)}" if random.random() > 0.5 else None
            ),
            "rigged": random.choice([True, False]) if random.random() > 0.5 else None,
            "animated": random.choice([True, False]) if random.random() > 0.5 else None,
        }
    )
    status = LazyFunction(lambda: random.choice(list(ContentStatus)))
    is_nsfw = LazyFunction(lambda: random.random() > 0.9)
    view_count = LazyFunction(lambda: random.randint(0, 100000))
    like_count = LazyFunction(lambda: random.randint(0, 10000))
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-2y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Listing Factory
# ---------------------------------------------------------------------------
class ListingFactory(BaseFactory):
    """Factory for creating Listing instances."""

    class Meta:
        model = Listing

    id = LazyFunction(uuid4)
    content = SubFactory(ContentFactory)
    creator = LazyAttribute(lambda o: o.content.creator)
    title = factory.LazyAttribute(
        lambda o: f"{o.content.title} - {random.choice(LICENSE_TYPES).title()}"
    )
    description = factory.LazyAttribute(
        lambda o: faker.text(max_nb_chars=500) if random.random() > 0.3 else None
    )
    price = LazyFunction(lambda: Decimal(str(round(random.uniform(0.99, 999.99), 2))))
    currency = LazyFunction(lambda: random.choice(CURRENCIES))
    license_type = LazyFunction(lambda: random.choice(LICENSE_TYPES))
    usage_rights = LazyFunction(
        lambda: {
            "commercial_use": random.choice([True, False]),
            "modification": random.choice([True, False]),
            "redistribution": random.choice([True, False]),
            "attribution": random.choice([True, False]),
            "unlimited_projects": random.choice([True, False]),
            "project_limit": random.choice([1, 5, 10, 25, None]),
            "seat_count": random.choice([1, 5, 10, 25, 50, None]),
        }
    )
    is_active = LazyFunction(lambda: random.random() > 0.15)
    sales_count = LazyFunction(lambda: random.randint(0, 500))
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Transaction Factory
# ---------------------------------------------------------------------------
class TransactionFactory(BaseFactory):
    """Factory for creating Transaction instances."""

    class Meta:
        model = Transaction

    id = LazyFunction(uuid4)
    listing = SubFactory(ListingFactory)
    buyer = SubFactory(CreatorFactory)
    seller = LazyAttribute(lambda o: o.listing.creator)
    amount = LazyAttribute(lambda o: o.listing.price)
    currency = LazyAttribute(lambda o: o.listing.currency)
    platform_fee = LazyAttribute(
        lambda o: Decimal(str(round(float(o.amount) * random.uniform(0.05, 0.15), 2)))
    )
    seller_earnings = LazyAttribute(lambda o: o.amount - o.platform_fee)
    payment_method = LazyFunction(lambda: random.choice(PAYMENT_METHODS))
    payment_status = LazyFunction(lambda: random.choice(list(PaymentStatus)))
    stripe_payment_intent_id = factory.LazyAttribute(
        lambda o: (
            f"pi_3{faker.lexify(text='????????????????????????????????')}"
            if random.random() > 0.3
            else None
        )
    )
    metadata_ = LazyFunction(
        lambda: {
            "ip_country": faker.country_code(),
            "ip_address": faker.ipv4(),
            "user_agent": faker.user_agent(),
            "referrer": faker.url() if random.random() > 0.5 else None,
        }
    )
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# License Factory
# ---------------------------------------------------------------------------
class LicenseFactory(BaseFactory):
    """Factory for creating License instances."""

    class Meta:
        model = License

    id = LazyFunction(uuid4)
    transaction = SubFactory(TransactionFactory)
    licensee = LazyAttribute(lambda o: o.transaction.buyer)
    licensor = LazyAttribute(lambda o: o.transaction.seller)
    content = LazyAttribute(lambda o: o.transaction.listing.content)
    license_type = LazyAttribute(lambda o: o.transaction.listing.license_type)
    usage_scope = LazyFunction(
        lambda: {
            "project_limit": random.choice(["unlimited", 1, 5, 10, 25]),
            "seat_count": random.choice([1, 5, 10, 25, 50]),
            "redistribution": random.choice([True, False]),
            "commercial_use": random.choice([True, False]),
            "modification": random.choice([True, False]),
        }
    )
    valid_from = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    valid_until = LazyFunction(
        lambda: (
            faker.date_time_between(start_date="now", end_date="+1y", tzinfo=UTC)
            if random.random() > 0.5
            else None
        )
    )
    is_active = LazyFunction(lambda: random.random() > 0.1)
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Moderation Action Factory
# ---------------------------------------------------------------------------
class ModerationActionFactory(BaseFactory):
    """Factory for creating ModerationAction instances."""

    class Meta:
        model = ModerationAction

    id = LazyFunction(uuid4)
    content = factory.LazyAttribute(
        lambda o: SubFactory(ContentFactory) if random.random() > 0.3 else None
    )
    listing = factory.LazyAttribute(
        lambda o: (
            SubFactory(ListingFactory)
            if o.content is None and random.random() > 0.5
            else None
        )
    )
    moderator = SubFactory(CreatorFactory)
    action_type = LazyFunction(lambda: random.choice(MODERATION_ACTION_TYPES))
    reason = factory.LazyAttribute(
        lambda o: faker.text(max_nb_chars=500) if random.random() > 0.3 else None
    )
    details = LazyFunction(
        lambda: {
            "review_time_minutes": random.randint(1, 60),
            "flags": random.sample(
                ["spam", "low_quality", "misleading", "copyright", "nsfw"],
                k=random.randint(0, 3),
            ),
            "notes": faker.text(max_nb_chars=200) if random.random() > 0.5 else None,
        }
    )
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Quality Score Factory
# ---------------------------------------------------------------------------
class QualityScoreFactory(BaseFactory):
    """Factory for creating QualityScore instances."""

    class Meta:
        model = QualityScore

    id = LazyFunction(uuid4)
    content = SubFactory(ContentFactory)
    overall_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0.5, 1.0), 3)))
    )
    technical_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0.5, 1.0), 3)))
    )
    aesthetic_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0.5, 1.0), 3)))
    )
    engagement_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0.5, 1.0), 3)))
    )
    originality_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0.5, 1.0), 3)))
    )
    scoring_model = LazyFunction(lambda: random.choice(SCORING_MODELS))
    details = LazyFunction(
        lambda: {
            "texture_quality": random.choice(
                ["excellent", "very_good", "good", "fair", "poor"]
            ),
            "rigging": random.choice(["professional", "good", "basic", "none"]),
            "optimization": random.choice(["excellent", "good", "fair", "poor"]),
            "modularity": random.choice(["excellent", "good", "fair", "poor"]),
            "consistency": random.choice(
                ["perfect", "very_good", "good", "fair", "poor"]
            ),
            "coverage": random.choice(["comprehensive", "good", "limited", "minimal"]),
        }
    )
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Fraud Report Factory
# ---------------------------------------------------------------------------
class FraudReportFactory(BaseFactory):
    """Factory for creating FraudReport instances."""

    class Meta:
        model = FraudReport

    id = LazyFunction(uuid4)
    reporter = SubFactory(CreatorFactory)
    reported_content = factory.LazyAttribute(
        lambda o: SubFactory(ContentFactory) if random.random() > 0.4 else None
    )
    reported_listing = factory.LazyAttribute(
        lambda o: (
            SubFactory(ListingFactory)
            if o.reported_content is None and random.random() > 0.5
            else None
        )
    )
    reported_user = factory.LazyAttribute(
        lambda o: SubFactory(CreatorFactory) if random.random() > 0.6 else None
    )
    report_type = LazyFunction(lambda: random.choice(FRAUD_REPORT_TYPES))
    description = factory.LazyAttribute(
        lambda o: faker.text(max_nb_chars=1000) if random.random() > 0.2 else None
    )
    evidence = LazyFunction(
        lambda: {
            "urls": [faker.url() for _ in range(random.randint(1, 3))],
            "similarity_score": (
                round(random.uniform(0.5, 1.0), 2) if random.random() > 0.5 else None
            ),
            "screenshots": [faker.image_url() for _ in range(random.randint(0, 3))],
            "communication_logs": [
                faker.text(max_nb_chars=200) for _ in range(random.randint(0, 5))
            ],
        }
    )
    status = LazyFunction(lambda: random.choice(list(FraudReportStatus)))
    resolution = factory.LazyAttribute(
        lambda o: (
            faker.text(max_nb_chars=500)
            if o.status in [FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED]
            else None
        )
    )
    resolved_by = factory.LazyAttribute(
        lambda o: (
            SubFactory(CreatorFactory)
            if o.status in [FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED]
            else None
        )
    )
    resolved_at = factory.LazyAttribute(
        lambda o: (
            faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
            if o.status in [FraudReportStatus.RESOLVED, FraudReportStatus.DISMISSED]
            else None
        )
    )
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    updated_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Analytics Event Factory
# ---------------------------------------------------------------------------
class AnalyticsEventFactory(BaseFactory):
    """Factory for creating AnalyticsEvent instances."""

    class Meta:
        model = AnalyticsEvent

    id = LazyFunction(uuid4)
    event_type = LazyFunction(lambda: random.choice(EVENT_TYPES))
    user = factory.LazyAttribute(
        lambda o: SubFactory(CreatorFactory) if random.random() > 0.3 else None
    )
    content = factory.LazyAttribute(
        lambda o: SubFactory(ContentFactory) if random.random() > 0.5 else None
    )
    listing = factory.LazyAttribute(
        lambda o: SubFactory(ListingFactory) if random.random() > 0.6 else None
    )
    session_id = LazyFunction(uuid4)
    ip_address = LazyFunction(lambda: faker.ipv4())
    user_agent = LazyFunction(lambda: faker.user_agent())
    referrer = LazyFunction(lambda: faker.url() if random.random() > 0.5 else None)
    event_data = LazyFunction(
        lambda: {
            "page": f"/{random.choice(['content', 'listing', 'profile', 'search'])}/{faker.slug()}",
            "duration_seconds": random.randint(1, 300),
            "query": faker.word() if random.random() > 0.7 else None,
            "results_count": random.randint(0, 100) if random.random() > 0.7 else None,
            "price": (
                round(random.uniform(0.99, 999.99), 2)
                if random.random() > 0.8
                else None
            ),
            "currency": random.choice(CURRENCIES) if random.random() > 0.8 else None,
        }
    )
    created_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )


# ---------------------------------------------------------------------------
# Audit Log Factory
# ---------------------------------------------------------------------------
class AuditLogFactory(BaseFactory):
    """Factory for creating AuditLog instances."""

    class Meta:
        model = AuditLog

    id = LazyFunction(uuid4)
    table_name = LazyFunction(
        lambda: random.choice(
            ["creators", "content", "listings", "transactions", "licenses"]
        )
    )
    record_id = LazyFunction(uuid4)
    action = LazyFunction(lambda: random.choice(["INSERT", "UPDATE", "DELETE"]))
    old_values = LazyFunction(
        lambda: (
            {"field": faker.word(), "value": faker.word()}
            if random.random() > 0.5
            else None
        )
    )
    new_values = LazyFunction(
        lambda: (
            {"field": faker.word(), "value": faker.word()}
            if random.random() > 0.5
            else None
        )
    )
    changed_by = factory.LazyAttribute(
        lambda o: SubFactory(CreatorFactory) if random.random() > 0.3 else None
    )
    changed_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
    )
    ip_address = LazyFunction(lambda: faker.ipv4() if random.random() > 0.3 else None)
    user_agent = LazyFunction(
        lambda: faker.user_agent() if random.random() > 0.3 else None
    )


# ---------------------------------------------------------------------------
# Specialized Factories for Common Test Scenarios
# ---------------------------------------------------------------------------
class VerifiedCreatorFactory(CreatorFactory):
    """Factory for creating verified creators."""

    verification_status = VerificationStatus.VERIFIED
    reputation_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(70, 100), 2)))
    )
    total_earnings = LazyFunction(
        lambda: Decimal(str(round(random.uniform(1000, 50000), 2)))
    )
    total_sales = LazyFunction(lambda: random.randint(10, 1000))


class SuspendedCreatorFactory(CreatorFactory):
    """Factory for creating suspended creators."""

    verification_status = VerificationStatus.SUSPENDED
    is_active = False
    reputation_score = LazyFunction(
        lambda: Decimal(str(round(random.uniform(0, 30), 2)))
    )


class PublishedContentFactory(ContentFactory):
    """Factory for creating published content."""

    status = ContentStatus.PUBLISHED
    view_count = LazyFunction(lambda: random.randint(100, 100000))
    like_count = LazyFunction(lambda: random.randint(10, 10000))


class DraftContentFactory(ContentFactory):
    """Factory for creating draft content."""

    status = ContentStatus.DRAFT
    view_count = 0
    like_count = 0


class ActiveListingFactory(ListingFactory):
    """Factory for creating active listings."""

    is_active = True
    sales_count = LazyFunction(lambda: random.randint(1, 500))


class CompletedTransactionFactory(TransactionFactory):
    """Factory for creating completed transactions."""

    payment_status = PaymentStatus.COMPLETED


class PendingTransactionFactory(TransactionFactory):
    """Factory for creating pending transactions."""

    payment_status = PaymentStatus.PENDING


class RefundedTransactionFactory(TransactionFactory):
    """Factory for creating refunded transactions."""

    payment_status = PaymentStatus.REFUNDED


class CommercialLicenseFactory(LicenseFactory):
    """Factory for creating commercial licenses."""

    license_type = LicenseType.COMMERCIAL
    usage_scope = LazyFunction(
        lambda: {
            "project_limit": "unlimited",
            "seat_count": random.choice([1, 5, 10, 25, 50]),
            "redistribution": False,
            "commercial_use": True,
            "modification": True,
        }
    )


class PersonalLicenseFactory(LicenseFactory):
    """Factory for creating personal licenses."""

    license_type = LicenseType.PERSONAL
    usage_scope = LazyFunction(
        lambda: {
            "project_limit": random.choice([1, 5, 10]),
            "seat_count": 1,
            "redistribution": False,
            "commercial_use": False,
            "modification": True,
        }
    )


class ResolvedFraudReportFactory(FraudReportFactory):
    """Factory for creating resolved fraud reports."""

    status = FraudReportStatus.RESOLVED
    resolution = factory.LazyAttribute(lambda o: faker.text(max_nb_chars=500))
    resolved_by = SubFactory(CreatorFactory)
    resolved_at = LazyFunction(
        lambda: faker.date_time_between(start_date="-6m", end_date="now", tzinfo=UTC)
    )


class OpenFraudReportFactory(FraudReportFactory):
    """Factory for creating open fraud reports."""

    status = FraudReportStatus.OPEN
    resolution = None
    resolved_by = None
    resolved_at = None


# ---------------------------------------------------------------------------
# Factory Registry
# ---------------------------------------------------------------------------
FACTORIES = {
    "Creator": CreatorFactory,
    "Content": ContentFactory,
    "Listing": ListingFactory,
    "Transaction": TransactionFactory,
    "License": LicenseFactory,
    "ModerationAction": ModerationActionFactory,
    "QualityScore": QualityScoreFactory,
    "FraudReport": FraudReportFactory,
    "AnalyticsEvent": AnalyticsEventFactory,
    "AuditLog": AuditLogFactory,
    "VerifiedCreator": VerifiedCreatorFactory,
    "SuspendedCreator": SuspendedCreatorFactory,
    "PublishedContent": PublishedContentFactory,
    "DraftContent": DraftContentFactory,
    "ActiveListing": ActiveListingFactory,
    "CompletedTransaction": CompletedTransactionFactory,
    "PendingTransaction": PendingTransactionFactory,
    "RefundedTransaction": RefundedTransactionFactory,
    "CommercialLicense": CommercialLicenseFactory,
    "PersonalLicense": PersonalLicenseFactory,
    "ResolvedFraudReport": ResolvedFraudReportFactory,
    "OpenFraudReport": OpenFraudReportFactory,
}
