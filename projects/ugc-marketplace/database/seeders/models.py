"""SQLAlchemy ORM models for UGC Marketplace database seeders.

These models mirror the production schema defined in database/schema.sql
and are used by factory_boy factories and seeder scripts.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (JSON, Boolean, CheckConstraint, DateTime, Enum,
                        ForeignKey, Index, Integer, Numeric, String, Text,
                        func)
from sqlalchemy.dialects.postgresql import ARRAY, INET, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REMOVED = "removed"


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD_OUT = "sold_out"
    REMOVED = "removed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class LicenseType(str, enum.Enum):
    PERSONAL = "personal"
    COMMERCIAL = "commercial"
    EXTENDED = "extended"
    SINGLE = "single"
    EXCLUSIVE = "exclusive"


class ModerationActionType(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    REMOVE = "remove"
    RESTORE = "restore"
    WARN = "warn"
    SUSPEND = "suspend"
    BAN = "ban"


class FraudReportType(str, enum.Enum):
    COPYRIGHT = "copyright"
    FRAUD = "fraud"
    SPAM = "spam"
    IMPERSONATION = "impersonation"
    PROHIBITED_CONTENT = "prohibited_content"
    OTHER = "other"


class FraudReportStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class AuditAction(str, enum.Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Creator(Base):
    """Creator/user model."""

    __tablename__ = "creators"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(Text)
    social_links: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )
    reputation_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    total_earnings: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[list[Content]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    listings: Mapped[list[Listing]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
    transactions_as_buyer: Mapped[list[Transaction]] = relationship(
        foreign_keys="Transaction.buyer_id", back_populates="buyer"
    )
    transactions_as_seller: Mapped[list[Transaction]] = relationship(
        foreign_keys="Transaction.seller_id", back_populates="seller"
    )
    licenses_as_licensee: Mapped[list[License]] = relationship(
        foreign_keys="License.licensee_id", back_populates="licensee"
    )
    licenses_as_licensor: Mapped[list[License]] = relationship(
        foreign_keys="License.licensor_id", back_populates="licensor"
    )
    moderation_actions: Mapped[list[ModerationAction]] = relationship(
        foreign_keys="ModerationAction.moderator_id", back_populates="moderator"
    )
    fraud_reports_filed: Mapped[list[FraudReport]] = relationship(
        foreign_keys="FraudReport.reporter_id", back_populates="reporter"
    )
    fraud_reports_against: Mapped[list[FraudReport]] = relationship(
        foreign_keys="FraudReport.reported_user_id", back_populates="reported_user"
    )
    fraud_reports_resolved: Mapped[list[FraudReport]] = relationship(
        foreign_keys="FraudReport.resolved_by", back_populates="resolver"
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(back_populates="user")
    audit_log_entries: Mapped[list[AuditLog]] = relationship(
        foreign_keys="AuditLog.changed_by", back_populates="changed_by_user"
    )

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('unverified', 'pending', 'verified', 'suspended')",
            name="creators_verification_check",
        ),
        CheckConstraint(
            "reputation_score >= 0.00 AND reputation_score <= 100.00",
            name="creators_reputation_check",
        ),
        CheckConstraint("total_earnings >= 0.00", name="creators_earnings_check"),
        CheckConstraint("total_sales >= 0", name="creators_sales_check"),
        Index("idx_creators_verification_status", "verification_status"),
        Index("idx_creators_is_active", "is_active"),
        Index("idx_creators_reputation_score", "reputation_score"),
    )


class Content(Base):
    """Content model."""

    __tablename__ = "content"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    creator_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"),
        default=ContentStatus.DRAFT,
        nullable=False,
    )
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)

    # Relationships
    creator: Mapped[Creator] = relationship(back_populates="content")
    listings: Mapped[list[Listing]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )
    quality_scores: Mapped[list[QualityScore]] = relationship(
        back_populates="content", cascade="all, delete-orphan"
    )
    moderation_actions: Mapped[list[ModerationAction]] = relationship(
        back_populates="content"
    )
    fraud_reports: Mapped[list[FraudReport]] = relationship(
        foreign_keys="FraudReport.reported_content_id",
        back_populates="reported_content",
    )
    licenses: Mapped[list[License]] = relationship(back_populates="content")
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(
        back_populates="content"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived', 'removed')",
            name="content_status_check",
        ),
        CheckConstraint("view_count >= 0", name="content_view_count_check"),
        CheckConstraint("like_count >= 0", name="content_like_count_check"),
        Index("idx_content_creator_id", "creator_id"),
        Index("idx_content_status", "status"),
        Index("idx_content_content_type", "content_type"),
        Index("idx_content_is_nsfw", "is_nsfw"),
        Index("idx_content_created_at", "created_at"),
    )


class Listing(Base):
    """Listing model."""

    __tablename__ = "listings"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("content.id", ondelete="CASCADE"), nullable=False
    )
    creator_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    license_type: Mapped[str] = mapped_column(String(50), nullable=False)
    usage_rights: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sales_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content] = relationship(back_populates="listings")
    creator: Mapped[Creator] = relationship(back_populates="listings")
    transactions: Mapped[list[Transaction]] = relationship(back_populates="listing")
    moderation_actions: Mapped[list[ModerationAction]] = relationship(
        back_populates="listing"
    )
    fraud_reports: Mapped[list[FraudReport]] = relationship(
        foreign_keys="FraudReport.reported_listing_id",
        back_populates="reported_listing",
    )
    analytics_events: Mapped[list[AnalyticsEvent]] = relationship(
        back_populates="listing"
    )

    __table_args__ = (
        CheckConstraint("price >= 0.00", name="listings_price_check"),
        CheckConstraint("sales_count >= 0", name="listings_sales_check"),
        Index("idx_listings_content_id", "content_id"),
        Index("idx_listings_creator_id", "creator_id"),
        Index("idx_listings_is_active", "is_active"),
        Index("idx_listings_price", "price"),
        Index("idx_listings_license_type", "license_type"),
    )


class Transaction(Base):
    """Transaction model."""

    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("listings.id"), nullable=False
    )
    buyer_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id"), nullable=False
    )
    seller_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    seller_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50))
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    listing: Mapped[Listing] = relationship(back_populates="transactions")
    buyer: Mapped[Creator] = relationship(
        foreign_keys=[buyer_id], back_populates="transactions_as_buyer"
    )
    seller: Mapped[Creator] = relationship(
        foreign_keys=[seller_id], back_populates="transactions_as_seller"
    )
    licenses: Mapped[list[License]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("amount >= 0.00", name="transactions_amount_check"),
        CheckConstraint("platform_fee >= 0.00", name="transactions_fee_check"),
        CheckConstraint("seller_earnings >= 0.00", name="transactions_earnings_check"),
        CheckConstraint(
            "payment_status IN ('pending', 'completed', 'failed', 'refunded', 'disputed')",
            name="transactions_status_check",
        ),
        CheckConstraint(
            "buyer_id != seller_id", name="transactions_buyer_seller_check"
        ),
        Index("idx_transactions_listing_id", "listing_id"),
        Index("idx_transactions_buyer_id", "buyer_id"),
        Index("idx_transactions_seller_id", "seller_id"),
        Index("idx_transactions_status", "payment_status"),
        Index("idx_transactions_created_at", "created_at"),
    )


class License(Base):
    """License model."""

    __tablename__ = "licenses"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    transaction_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    licensee_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id"), nullable=False
    )
    licensor_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id"), nullable=False
    )
    content_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("content.id"), nullable=False
    )
    license_type: Mapped[str] = mapped_column(String(50), nullable=False)
    usage_scope: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    transaction: Mapped[Transaction] = relationship(back_populates="licenses")
    licensee: Mapped[Creator] = relationship(
        foreign_keys=[licensee_id], back_populates="licenses_as_licensee"
    )
    licensor: Mapped[Creator] = relationship(
        foreign_keys=[licensor_id], back_populates="licenses_as_licensor"
    )
    content: Mapped[Content] = relationship(back_populates="licenses")

    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="licenses_validity_check",
        ),
        Index("idx_licenses_transaction_id", "transaction_id"),
        Index("idx_licenses_licensee_id", "licensee_id"),
        Index("idx_licenses_licensor_id", "licensor_id"),
        Index("idx_licenses_content_id", "content_id"),
        Index("idx_licenses_is_active", "is_active"),
        Index("idx_licenses_valid_until", "valid_until"),
    )


class ModerationAction(Base):
    """Moderation action model."""

    __tablename__ = "moderation_actions"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    content_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("content.id", ondelete="SET NULL")
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("listings.id", ondelete="SET NULL")
    )
    moderator_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="SET NULL")
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content | None] = relationship(back_populates="moderation_actions")
    listing: Mapped[Listing | None] = relationship(back_populates="moderation_actions")
    moderator: Mapped[Creator | None] = relationship(
        foreign_keys=[moderator_id], back_populates="moderation_actions"
    )

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('approve', 'reject', 'flag', 'remove', 'restore', 'warn', 'suspend', 'ban')",
            name="moderation_action_check",
        ),
        Index("idx_moderation_content_id", "content_id"),
        Index("idx_moderation_listing_id", "listing_id"),
        Index("idx_moderation_moderator_id", "moderator_id"),
        Index("idx_moderation_action_type", "action_type"),
        Index("idx_moderation_created_at", "created_at"),
    )


class QualityScore(Base):
    """Quality score model."""

    __tablename__ = "quality_scores"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("content.id", ondelete="CASCADE"), nullable=False
    )
    overall_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    technical_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    aesthetic_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    engagement_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    originality_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    scoring_model: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    content: Mapped[Content] = relationship(back_populates="quality_scores")

    __table_args__ = (
        CheckConstraint(
            "overall_score >= 0.000 AND overall_score <= 1.000",
            name="quality_overall_check",
        ),
        CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 0.000 AND technical_score <= 1.000)",
            name="quality_technical_check",
        ),
        CheckConstraint(
            "aesthetic_score IS NULL OR (aesthetic_score >= 0.000 AND aesthetic_score <= 1.000)",
            name="quality_aesthetic_check",
        ),
        CheckConstraint(
            "engagement_score IS NULL OR (engagement_score >= 0.000 AND engagement_score <= 1.000)",
            name="quality_engagement_check",
        ),
        CheckConstraint(
            "originality_score IS NULL OR (originality_score >= 0.000 AND originality_score <= 1.000)",
            name="quality_originality_check",
        ),
        Index("idx_quality_content_id", "content_id"),
        Index("idx_quality_overall_score", "overall_score"),
        Index("idx_quality_scoring_model", "scoring_model"),
    )


class FraudReport(Base):
    """Fraud report model."""

    __tablename__ = "fraud_reports"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    reporter_id: Mapped[UUID] = mapped_column(
        PGUUID, ForeignKey("creators.id"), nullable=False
    )
    reported_content_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("content.id", ondelete="SET NULL")
    )
    reported_listing_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("listings.id", ondelete="SET NULL")
    )
    reported_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="SET NULL")
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[FraudReportStatus] = mapped_column(
        Enum(FraudReportStatus, name="fraud_status"),
        default=FraudReportStatus.OPEN,
        nullable=False,
    )
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    reporter: Mapped[Creator] = relationship(
        foreign_keys=[reporter_id], back_populates="fraud_reports_filed"
    )
    reported_content: Mapped[Content | None] = relationship(
        foreign_keys=[reported_content_id], back_populates="fraud_reports"
    )
    reported_listing: Mapped[Listing | None] = relationship(
        foreign_keys=[reported_listing_id], back_populates="fraud_reports"
    )
    reported_user: Mapped[Creator | None] = relationship(
        foreign_keys=[reported_user_id], back_populates="fraud_reports_against"
    )
    resolver: Mapped[Creator | None] = relationship(
        foreign_keys=[resolved_by], back_populates="fraud_reports_resolved"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'investigating', 'resolved', 'dismissed', 'escalated')",
            name="fraud_status_check",
        ),
        CheckConstraint(
            "report_type IN ('copyright', 'fraud', 'spam', 'impersonation', 'prohibited_content', 'other')",
            name="fraud_type_check",
        ),
        Index("idx_fraud_reporter_id", "reporter_id"),
        Index("idx_fraud_content_id", "reported_content_id"),
        Index("idx_fraud_listing_id", "reported_listing_id"),
        Index("idx_fraud_reported_user_id", "reported_user_id"),
        Index("idx_fraud_status", "status"),
        Index("idx_fraud_report_type", "report_type"),
        Index("idx_fraud_created_at", "created_at"),
    )


class AnalyticsEvent(Base):
    """Analytics event model (partitioned table)."""

    __tablename__ = "analytics_events"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="SET NULL")
    )
    content_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("content.id", ondelete="SET NULL")
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("listings.id", ondelete="SET NULL")
    )
    session_id: Mapped[UUID | None] = mapped_column(PGUUID)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    referrer: Mapped[str | None] = mapped_column(Text)
    event_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Creator | None] = relationship(back_populates="analytics_events")
    content: Mapped[Content | None] = relationship(back_populates="analytics_events")
    listing: Mapped[Listing | None] = relationship(back_populates="analytics_events")

    __table_args__ = (
        Index("idx_analytics_event_type", "event_type"),
        Index("idx_analytics_user_id", "user_id"),
        Index("idx_analytics_content_id", "content_id"),
        Index("idx_analytics_listing_id", "listing_id"),
        Index("idx_analytics_created_at", "created_at"),
    )


class AuditLog(Base):
    """Audit log model."""

    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PGUUID, primary_key=True, default=uuid4)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[UUID] = mapped_column(PGUUID, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    changed_by: Mapped[UUID | None] = mapped_column(
        PGUUID, ForeignKey("creators.id", ondelete="SET NULL")
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Relationships
    changed_by_user: Mapped[Creator | None] = relationship(
        foreign_keys=[changed_by], back_populates="audit_log_entries"
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('INSERT', 'UPDATE', 'DELETE')",
            name="audit_action_check",
        ),
        Index("idx_audit_table_name", "table_name"),
        Index("idx_audit_record_id", "record_id"),
        Index("idx_audit_changed_by", "changed_by"),
        Index("idx_audit_changed_at", "changed_at"),
    )
