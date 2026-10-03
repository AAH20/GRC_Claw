"""Validation module for UGC Marketplace database seeders.

This module validates that all factories produce valid data that satisfies
model constraints, foreign key relationships, and business rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from ugc_marketplace.database.seeders.factories import (
    ActiveListingFactory, AnalyticsEventFactory, AuditLogFactory,
    CommercialLicenseFactory, CompletedTransactionFactory, ContentFactory,
    CreatorFactory, DraftContentFactory, FraudReportFactory, LicenseFactory,
    ListingFactory, ModerationActionFactory, OpenFraudReportFactory,
    PendingTransactionFactory, PublishedContentFactory, QualityScoreFactory,
    RefundedTransactionFactory, ResolvedFraudReportFactory,
    SuspendedCreatorFactory, TransactionFactory, VerifiedCreatorFactory)
from ugc_marketplace.database.seeders.models import (ContentStatus,
                                                     FraudReportStatus,
                                                     LicenseType,
                                                     PaymentStatus,
                                                     VerificationStatus)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report for all factories."""

    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    def add(self, result: ValidationResult) -> None:
        self.results.append(result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "success_rate": (
                    f"{(self.passed / self.total * 100):.1f}%"
                    if self.total > 0
                    else "N/A"
                ),
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }


class FactoryValidator:
    """Validates that factories produce valid data."""

    def __init__(self, session: Session):
        self.session = session
        self.report = ValidationReport()

    def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        self.validate_creator_factory()
        self.validate_verified_creator_factory()
        self.validate_suspended_creator_factory()
        self.validate_content_factory()
        self.validate_published_content_factory()
        self.validate_draft_content_factory()
        self.validate_listing_factory()
        self.validate_active_listing_factory()
        self.validate_transaction_factory()
        self.validate_completed_transaction_factory()
        self.validate_pending_transaction_factory()
        self.validate_refunded_transaction_factory()
        self.validate_license_factory()
        self.validate_commercial_license_factory()
        self.validate_moderation_action_factory()
        self.validate_quality_score_factory()
        self.validate_fraud_report_factory()
        self.validate_resolved_fraud_report_factory()
        self.validate_open_fraud_report_factory()
        self.validate_analytics_event_factory()
        self.validate_audit_log_factory()
        self.validate_foreign_key_integrity()
        self.validate_business_rules()
        return self.report

    def _check(self, name: str, condition: bool, message: str, **details) -> None:
        """Record a validation check result."""
        self.report.add(
            ValidationResult(
                name=name,
                passed=condition,
                message=message,
                details=details,
            )
        )

    def validate_creator_factory(self) -> None:
        """Validate CreatorFactory produces valid creators."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        self._check(
            "creator_has_id",
            creator.id is not None,
            "Creator should have an ID",
        )
        self._check(
            "creator_has_username",
            creator.username is not None and len(creator.username) > 0,
            "Creator should have a username",
        )
        self._check(
            "creator_has_email",
            creator.email is not None and "@" in creator.email,
            "Creator should have a valid email",
        )
        self._check(
            "creator_username_length",
            creator.username is not None and len(creator.username) <= 50,
            "Username should be <= 50 chars",
            username_length=len(creator.username) if creator.username else 0,
        )
        self._check(
            "creator_email_length",
            creator.email is not None and len(creator.email) <= 255,
            "Email should be <= 255 chars",
        )
        self._check(
            "creator_reputation_range",
            creator.reputation_score is not None
            and Decimal("0.00") <= creator.reputation_score <= Decimal("100.00"),
            "Reputation score should be between 0 and 100",
            reputation_score=(
                str(creator.reputation_score) if creator.reputation_score else None
            ),
        )
        self._check(
            "creator_earnings_non_negative",
            creator.total_earnings is not None
            and creator.total_earnings >= Decimal("0.00"),
            "Total earnings should be non-negative",
        )
        self._check(
            "creator_sales_non_negative",
            creator.total_sales is not None and creator.total_sales >= 0,
            "Total sales should be non-negative",
        )
        self._check(
            "creator_has_verification_status",
            creator.verification_status is not None,
            "Creator should have a verification status",
            status=(
                creator.verification_status.value
                if creator.verification_status
                else None
            ),
        )
        self._check(
            "creator_has_social_links",
            creator.social_links is not None,
            "Creator should have social links dict",
        )
        self._check(
            "creator_has_timestamps",
            creator.created_at is not None and creator.updated_at is not None,
            "Creator should have created_at and updated_at",
        )

    def validate_verified_creator_factory(self) -> None:
        """Validate VerifiedCreatorFactory produces valid verified creators."""
        creator = VerifiedCreatorFactory()
        self.session.add(creator)
        self.session.flush()

        self._check(
            "verified_creator_status",
            creator.verification_status == VerificationStatus.VERIFIED,
            "Verified creator should have VERIFIED status",
            status=(
                creator.verification_status.value
                if creator.verification_status
                else None
            ),
        )
        self._check(
            "verified_creator_reputation",
            creator.reputation_score is not None
            and creator.reputation_score >= Decimal("70.00"),
            "Verified creator should have reputation >= 70",
            reputation_score=(
                str(creator.reputation_score) if creator.reputation_score else None
            ),
        )
        self._check(
            "verified_creator_earnings",
            creator.total_earnings is not None
            and creator.total_earnings >= Decimal("1000.00"),
            "Verified creator should have earnings >= 1000",
        )

    def validate_suspended_creator_factory(self) -> None:
        """Validate SuspendedCreatorFactory produces valid suspended creators."""
        creator = SuspendedCreatorFactory()
        self.session.add(creator)
        self.session.flush()

        self._check(
            "suspended_creator_status",
            creator.verification_status == VerificationStatus.SUSPENDED,
            "Suspended creator should have SUSPENDED status",
        )
        self._check(
            "suspended_creator_inactive",
            creator.is_active is False,
            "Suspended creator should be inactive",
        )
        self._check(
            "suspended_creator_reputation",
            creator.reputation_score is not None
            and creator.reputation_score <= Decimal("30.00"),
            "Suspended creator should have reputation <= 30",
        )

    def validate_content_factory(self) -> None:
        """Validate ContentFactory produces valid content."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = ContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        self._check(
            "content_has_id",
            content.id is not None,
            "Content should have an ID",
        )
        self._check(
            "content_has_title",
            content.title is not None and len(content.title) > 0,
            "Content should have a title",
        )
        self._check(
            "content_title_length",
            content.title is not None and len(content.title) <= 255,
            "Title should be <= 255 chars",
        )
        self._check(
            "content_has_creator",
            content.creator_id is not None,
            "Content should have a creator_id",
        )
        self._check(
            "content_has_type",
            content.content_type is not None and len(content.content_type) > 0,
            "Content should have a content_type",
        )
        self._check(
            "content_has_status",
            content.status is not None,
            "Content should have a status",
            status=content.status.value if content.status else None,
        )
        self._check(
            "content_view_count_non_negative",
            content.view_count is not None and content.view_count >= 0,
            "View count should be non-negative",
        )
        self._check(
            "content_like_count_non_negative",
            content.like_count is not None and content.like_count >= 0,
            "Like count should be non-negative",
        )
        self._check(
            "content_has_media_urls",
            content.media_urls is not None,
            "Content should have media_urls list",
        )
        self._check(
            "content_has_tags",
            content.tags is not None,
            "Content should have tags list",
        )
        self._check(
            "content_has_metadata",
            content.metadata_ is not None,
            "Content should have metadata dict",
        )

    def validate_published_content_factory(self) -> None:
        """Validate PublishedContentFactory produces valid published content."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        self._check(
            "published_content_status",
            content.status == ContentStatus.PUBLISHED,
            "Published content should have PUBLISHED status",
        )
        self._check(
            "published_content_has_views",
            content.view_count is not None and content.view_count >= 100,
            "Published content should have >= 100 views",
            view_count=content.view_count,
        )

    def validate_draft_content_factory(self) -> None:
        """Validate DraftContentFactory produces valid draft content."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = DraftContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        self._check(
            "draft_content_status",
            content.status == ContentStatus.DRAFT,
            "Draft content should have DRAFT status",
        )
        self._check(
            "draft_content_no_views",
            content.view_count == 0,
            "Draft content should have 0 views",
        )
        self._check(
            "draft_content_no_likes",
            content.like_count == 0,
            "Draft content should have 0 likes",
        )

    def validate_listing_factory(self) -> None:
        """Validate ListingFactory produces valid listings."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        self._check(
            "listing_has_id",
            listing.id is not None,
            "Listing should have an ID",
        )
        self._check(
            "listing_has_content",
            listing.content_id is not None,
            "Listing should have a content_id",
        )
        self._check(
            "listing_has_creator",
            listing.creator_id is not None,
            "Listing should have a creator_id",
        )
        self._check(
            "listing_has_title",
            listing.title is not None and len(listing.title) > 0,
            "Listing should have a title",
        )
        self._check(
            "listing_price_non_negative",
            listing.price is not None and listing.price >= Decimal("0.00"),
            "Listing price should be non-negative",
            price=str(listing.price) if listing.price else None,
        )
        self._check(
            "listing_has_currency",
            listing.currency is not None and len(listing.currency) == 3,
            "Listing should have a 3-char currency code",
            currency=listing.currency,
        )
        self._check(
            "listing_has_license_type",
            listing.license_type is not None and len(listing.license_type) > 0,
            "Listing should have a license_type",
        )
        self._check(
            "listing_has_usage_rights",
            listing.usage_rights is not None,
            "Listing should have usage_rights dict",
        )
        self._check(
            "listing_sales_count_non_negative",
            listing.sales_count is not None and listing.sales_count >= 0,
            "Sales count should be non-negative",
        )

    def validate_active_listing_factory(self) -> None:
        """Validate ActiveListingFactory produces valid active listings."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        self._check(
            "listing_is_active",
            listing.is_active is True,
            "Active listing should have is_active=True",
        )
        self._check(
            "listing_has_sales",
            listing.sales_count is not None and listing.sales_count >= 1,
            "Active listing should have >= 1 sales",
            sales_count=listing.sales_count,
        )

    def validate_transaction_factory(self) -> None:
        """Validate TransactionFactory produces valid transactions."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = TransactionFactory(listing=listing, buyer=buyer, seller=creator)
        self.session.add(transaction)
        self.session.flush()

        self._check(
            "transaction_has_id",
            transaction.id is not None,
            "Transaction should have an ID",
        )
        self._check(
            "transaction_has_listing",
            transaction.listing_id is not None,
            "Transaction should have a listing_id",
        )
        self._check(
            "transaction_has_buyer",
            transaction.buyer_id is not None,
            "Transaction should have a buyer_id",
        )
        self._check(
            "transaction_has_seller",
            transaction.seller_id is not None,
            "Transaction should have a seller_id",
        )
        self._check(
            "transaction_buyer_not_seller",
            transaction.buyer_id != transaction.seller_id,
            "Buyer and seller should be different",
        )
        self._check(
            "transaction_amount_non_negative",
            transaction.amount is not None and transaction.amount >= Decimal("0.00"),
            "Transaction amount should be non-negative",
        )
        self._check(
            "transaction_fee_non_negative",
            transaction.platform_fee is not None
            and transaction.platform_fee >= Decimal("0.00"),
            "Platform fee should be non-negative",
        )
        self._check(
            "transaction_earnings_non_negative",
            transaction.seller_earnings is not None
            and transaction.seller_earnings >= Decimal("0.00"),
            "Seller earnings should be non-negative",
        )
        self._check(
            "transaction_has_status",
            transaction.payment_status is not None,
            "Transaction should have a payment status",
            status=(
                transaction.payment_status.value if transaction.payment_status else None
            ),
        )
        self._check(
            "transaction_has_payment_method",
            transaction.payment_method is not None,
            "Transaction should have a payment method",
        )

    def validate_completed_transaction_factory(self) -> None:
        """Validate CompletedTransactionFactory produces valid completed transactions."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = CompletedTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        self._check(
            "completed_transaction_status",
            transaction.payment_status == PaymentStatus.COMPLETED,
            "Completed transaction should have COMPLETED status",
        )

    def validate_pending_transaction_factory(self) -> None:
        """Validate PendingTransactionFactory produces valid pending transactions."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = PendingTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        self._check(
            "pending_transaction_status",
            transaction.payment_status == PaymentStatus.PENDING,
            "Pending transaction should have PENDING status",
        )

    def validate_refunded_transaction_factory(self) -> None:
        """Validate RefundedTransactionFactory produces valid refunded transactions."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = RefundedTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        self._check(
            "refunded_transaction_status",
            transaction.payment_status == PaymentStatus.REFUNDED,
            "Refunded transaction should have REFUNDED status",
        )

    def validate_license_factory(self) -> None:
        """Validate LicenseFactory produces valid licenses."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = CompletedTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        license_obj = LicenseFactory(transaction=transaction)
        self.session.add(license_obj)
        self.session.flush()

        self._check(
            "license_has_id",
            license_obj.id is not None,
            "License should have an ID",
        )
        self._check(
            "license_has_transaction",
            license_obj.transaction_id is not None,
            "License should have a transaction_id",
        )
        self._check(
            "license_has_licensee",
            license_obj.licensee_id is not None,
            "License should have a licensee_id",
        )
        self._check(
            "license_has_licensor",
            license_obj.licensor_id is not None,
            "License should have a licensor_id",
        )
        self._check(
            "license_has_content",
            license_obj.content_id is not None,
            "License should have a content_id",
        )
        self._check(
            "license_has_type",
            license_obj.license_type is not None,
            "License should have a license_type",
            license_type=license_obj.license_type,
        )
        self._check(
            "license_has_usage_scope",
            license_obj.usage_scope is not None,
            "License should have usage_scope dict",
        )
        self._check(
            "license_has_valid_from",
            license_obj.valid_from is not None,
            "License should have valid_from timestamp",
        )
        if license_obj.valid_until is not None:
            self._check(
                "license_valid_until_after_from",
                license_obj.valid_until > license_obj.valid_from,
                "valid_until should be after valid_from",
            )
        else:
            self._check(
                "license_valid_until_nullable",
                True,
                "valid_until can be None (perpetual license)",
            )

    def validate_commercial_license_factory(self) -> None:
        """Validate CommercialLicenseFactory produces valid commercial licenses."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = CompletedTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        license_obj = CommercialLicenseFactory(transaction=transaction)
        self.session.add(license_obj)
        self.session.flush()

        self._check(
            "commercial_license_type",
            license_obj.license_type == LicenseType.COMMERCIAL,
            "Commercial license should have COMMERCIAL type",
        )
        self._check(
            "commercial_license_commercial_use",
            license_obj.usage_scope.get("commercial_use") is True,
            "Commercial license should allow commercial use",
        )

    def validate_moderation_action_factory(self) -> None:
        """Validate ModerationActionFactory produces valid moderation actions."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        moderator = CreatorFactory()
        self.session.add(moderator)
        self.session.flush()

        action = ModerationActionFactory(content=content, moderator=moderator)
        self.session.add(action)
        self.session.flush()

        self._check(
            "moderation_action_has_id",
            action.id is not None,
            "Moderation action should have an ID",
        )
        self._check(
            "moderation_action_has_type",
            action.action_type is not None and len(action.action_type) > 0,
            "Moderation action should have an action_type",
            action_type=action.action_type,
        )
        self._check(
            "moderation_action_has_moderator",
            action.moderator_id is not None,
            "Moderation action should have a moderator_id",
        )
        self._check(
            "moderation_action_has_details",
            action.details is not None,
            "Moderation action should have details dict",
        )
        self._check(
            "moderation_action_has_created_at",
            action.created_at is not None,
            "Moderation action should have created_at",
        )

    def validate_quality_score_factory(self) -> None:
        """Validate QualityScoreFactory produces valid quality scores."""
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        score = QualityScoreFactory(content=content)
        self.session.add(score)
        self.session.flush()

        self._check(
            "quality_score_has_id",
            score.id is not None,
            "Quality score should have an ID",
        )
        self._check(
            "quality_score_has_content",
            score.content_id is not None,
            "Quality score should have a content_id",
        )
        self._check(
            "quality_score_overall_range",
            score.overall_score is not None
            and Decimal("0.000") <= score.overall_score <= Decimal("1.000"),
            "Overall score should be between 0 and 1",
            overall_score=str(score.overall_score) if score.overall_score else None,
        )
        self._check(
            "quality_score_has_model",
            score.scoring_model is not None,
            "Quality score should have a scoring_model",
            scoring_model=score.scoring_model,
        )
        self._check(
            "quality_score_has_details",
            score.details is not None,
            "Quality score should have details dict",
        )

    def validate_fraud_report_factory(self) -> None:
        """Validate FraudReportFactory produces valid fraud reports."""
        reporter = CreatorFactory()
        self.session.add(reporter)
        self.session.flush()

        report = FraudReportFactory(reporter=reporter)
        self.session.add(report)
        self.session.flush()

        self._check(
            "fraud_report_has_id",
            report.id is not None,
            "Fraud report should have an ID",
        )
        self._check(
            "fraud_report_has_reporter",
            report.reporter_id is not None,
            "Fraud report should have a reporter_id",
        )
        self._check(
            "fraud_report_has_type",
            report.report_type is not None and len(report.report_type) > 0,
            "Fraud report should have a report_type",
            report_type=report.report_type,
        )
        self._check(
            "fraud_report_has_status",
            report.status is not None,
            "Fraud report should have a status",
            status=report.status.value if report.status else None,
        )
        self._check(
            "fraud_report_has_evidence",
            report.evidence is not None,
            "Fraud report should have evidence dict",
        )

    def validate_resolved_fraud_report_factory(self) -> None:
        """Validate ResolvedFraudReportFactory produces valid resolved fraud reports."""
        reporter = CreatorFactory()
        self.session.add(reporter)
        self.session.flush()

        report = ResolvedFraudReportFactory(reporter=reporter)
        self.session.add(report)
        self.session.flush()

        self._check(
            "resolved_fraud_report_status",
            report.status == FraudReportStatus.RESOLVED,
            "Resolved fraud report should have RESOLVED status",
        )
        self._check(
            "resolved_fraud_report_has_resolution",
            report.resolution is not None,
            "Resolved fraud report should have a resolution",
        )
        self._check(
            "resolved_fraud_report_has_resolved_by",
            report.resolved_by is not None,
            "Resolved fraud report should have a resolved_by",
        )
        self._check(
            "resolved_fraud_report_has_resolved_at",
            report.resolved_at is not None,
            "Resolved fraud report should have a resolved_at timestamp",
        )

    def validate_open_fraud_report_factory(self) -> None:
        """Validate OpenFraudReportFactory produces valid open fraud reports."""
        reporter = CreatorFactory()
        self.session.add(reporter)
        self.session.flush()

        report = OpenFraudReportFactory(reporter=reporter)
        self.session.add(report)
        self.session.flush()

        self._check(
            "open_fraud_report_status",
            report.status == FraudReportStatus.OPEN,
            "Open fraud report should have OPEN status",
        )
        self._check(
            "open_fraud_report_no_resolution",
            report.resolution is None,
            "Open fraud report should not have a resolution",
        )
        self._check(
            "open_fraud_report_no_resolved_by",
            report.resolved_by is None,
            "Open fraud report should not have a resolved_by",
        )

    def validate_analytics_event_factory(self) -> None:
        """Validate AnalyticsEventFactory produces valid analytics events."""
        event = AnalyticsEventFactory()
        self.session.add(event)
        self.session.flush()

        self._check(
            "analytics_event_has_id",
            event.id is not None,
            "Analytics event should have an ID",
        )
        self._check(
            "analytics_event_has_type",
            event.event_type is not None and len(event.event_type) > 0,
            "Analytics event should have an event_type",
            event_type=event.event_type,
        )
        self._check(
            "analytics_event_has_session_id",
            event.session_id is not None,
            "Analytics event should have a session_id",
        )
        self._check(
            "analytics_event_has_created_at",
            event.created_at is not None,
            "Analytics event should have created_at",
        )
        self._check(
            "analytics_event_has_event_data",
            event.event_data is not None,
            "Analytics event should have event_data dict",
        )

    def validate_audit_log_factory(self) -> None:
        """Validate AuditLogFactory produces valid audit log entries."""
        log = AuditLogFactory()
        self.session.add(log)
        self.session.flush()

        self._check(
            "audit_log_has_id",
            log.id is not None,
            "Audit log should have an ID",
        )
        self._check(
            "audit_log_has_table_name",
            log.table_name is not None and len(log.table_name) > 0,
            "Audit log should have a table_name",
            table_name=log.table_name,
        )
        self._check(
            "audit_log_has_record_id",
            log.record_id is not None,
            "Audit log should have a record_id",
        )
        self._check(
            "audit_log_has_action",
            log.action is not None and log.action in ("INSERT", "UPDATE", "DELETE"),
            "Audit log should have a valid action",
            action=log.action,
        )
        self._check(
            "audit_log_has_changed_at",
            log.changed_at is not None,
            "Audit log should have changed_at",
        )

    def validate_foreign_key_integrity(self) -> None:
        """Validate that all foreign key relationships are correct."""
        # Create a complete chain of related entities
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        buyer = CreatorFactory()
        self.session.add(buyer)
        self.session.flush()

        transaction = CompletedTransactionFactory(
            listing=listing, buyer=buyer, seller=creator
        )
        self.session.add(transaction)
        self.session.flush()

        license_obj = CommercialLicenseFactory(transaction=transaction)
        self.session.add(license_obj)
        self.session.flush()

        # Verify FK relationships
        self._check(
            "fk_content_creator",
            content.creator_id == creator.id,
            "Content creator_id should match creator id",
        )
        self._check(
            "fk_listing_content",
            listing.content_id == content.id,
            "Listing content_id should match content id",
        )
        self._check(
            "fk_listing_creator",
            listing.creator_id == creator.id,
            "Listing creator_id should match creator id",
        )
        self._check(
            "fk_transaction_listing",
            transaction.listing_id == listing.id,
            "Transaction listing_id should match listing id",
        )
        self._check(
            "fk_transaction_buyer",
            transaction.buyer_id == buyer.id,
            "Transaction buyer_id should match buyer id",
        )
        self._check(
            "fk_transaction_seller",
            transaction.seller_id == creator.id,
            "Transaction seller_id should match seller id",
        )
        self._check(
            "fk_license_transaction",
            license_obj.transaction_id == transaction.id,
            "License transaction_id should match transaction id",
        )
        self._check(
            "fk_license_content",
            license_obj.content_id == content.id,
            "License content_id should match content id",
        )
        self._check(
            "fk_license_licensee",
            license_obj.licensee_id == buyer.id,
            "License licensee_id should match buyer id",
        )
        self._check(
            "fk_license_licensor",
            license_obj.licensor_id == creator.id,
            "License licensor_id should match creator id",
        )

    def validate_business_rules(self) -> None:
        """Validate business rules and constraints."""
        # Test that buyer != seller constraint is enforced
        creator = CreatorFactory()
        self.session.add(creator)
        self.session.flush()

        content = PublishedContentFactory(creator=creator)
        self.session.add(content)
        self.session.flush()

        listing = ActiveListingFactory(content=content, creator=creator)
        self.session.add(listing)
        self.session.flush()

        # This should work - different buyer and seller
        transaction = CompletedTransactionFactory(
            listing=listing, buyer=creator, seller=creator
        )
        self.session.add(transaction)

        # The constraint should prevent this
        from sqlalchemy.exc import IntegrityError

        try:
            self.session.flush()
            self._check(
                "business_rule_buyer_seller_different",
                False,
                "Should not allow buyer == seller",
            )
        except IntegrityError:
            self._check(
                "business_rule_buyer_seller_different",
                True,
                "Correctly prevents buyer == seller",
            )
            self.session.rollback()


def run_validation(session: Session) -> ValidationReport:
    """Run all validations and return the report.

    Args:
        session: SQLAlchemy session.

    Returns:
        ValidationReport with all results.
    """
    validator = FactoryValidator(session)
    return validator.validate_all()
