"""Data consistency checks for UGC Marketplace database seeders.

This module verifies foreign key relationships, data integrity, and
business rule compliance after seeding.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyResult:
    """Result of a single consistency check."""

    name: str
    passed: bool
    message: str
    violations: int = 0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsistencyReport:
    """Complete consistency report."""

    results: list[ConsistencyResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def total_violations(self) -> int:
        return sum(r.violations for r in self.results)

    def add(self, result: ConsistencyResult) -> None:
        self.results.append(result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_checks": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "total_violations": self.total_violations,
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
                    "violations": r.violations,
                    "details": r.details,
                }
                for r in self.results
            ],
        }


class ConsistencyChecker:
    """Checks data consistency after seeding."""

    def __init__(self, session: Session):
        self.session = session
        self.report = ConsistencyReport()

    def run_all(self) -> ConsistencyReport:
        """Run all consistency checks."""
        self.check_foreign_key_integrity()
        self.check_business_rules()
        self.check_data_ranges()
        self.check_referential_integrity()
        self.check_orphaned_records()
        self.check_duplicate_data()
        self.check_temporal_consistency()
        self.check_json_field_validity()
        return self.report

    def _check(
        self, name: str, condition: bool, message: str, violations: int = 0, **details
    ) -> None:
        """Record a consistency check result."""
        self.report.add(
            ConsistencyResult(
                name=name,
                passed=condition,
                message=message,
                violations=violations,
                details=details,
            )
        )

    def check_foreign_key_integrity(self) -> None:
        """Verify all foreign key relationships are valid."""
        # Check content.creator_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content c
                LEFT JOIN creators cr ON c.creator_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_content_creator",
            result == 0,
            "All content.creator_id values reference existing creators",
            violations=result or 0,
        )

        # Check listings.content_id references content.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings l
                LEFT JOIN content c ON l.content_id = c.id
                WHERE c.id IS NULL
            """)).scalar()
        self._check(
            "fk_listing_content",
            result == 0,
            "All listings.content_id values reference existing content",
            violations=result or 0,
        )

        # Check listings.creator_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings l
                LEFT JOIN creators cr ON l.creator_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_listing_creator",
            result == 0,
            "All listings.creator_id values reference existing creators",
            violations=result or 0,
        )

        # Check transactions.listing_id references listings.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN listings l ON t.listing_id = l.id
                WHERE l.id IS NULL
            """)).scalar()
        self._check(
            "fk_transaction_listing",
            result == 0,
            "All transactions.listing_id values reference existing listings",
            violations=result or 0,
        )

        # Check transactions.buyer_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN creators cr ON t.buyer_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_transaction_buyer",
            result == 0,
            "All transactions.buyer_id values reference existing creators",
            violations=result or 0,
        )

        # Check transactions.seller_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN creators cr ON t.seller_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_transaction_seller",
            result == 0,
            "All transactions.seller_id values reference existing creators",
            violations=result or 0,
        )

        # Check licenses.transaction_id references transactions.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                LEFT JOIN transactions t ON l.transaction_id = t.id
                WHERE t.id IS NULL
            """)).scalar()
        self._check(
            "fk_license_transaction",
            result == 0,
            "All licenses.transaction_id values reference existing transactions",
            violations=result or 0,
        )

        # Check licenses.content_id references content.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                LEFT JOIN content c ON l.content_id = c.id
                WHERE c.id IS NULL
            """)).scalar()
        self._check(
            "fk_license_content",
            result == 0,
            "All licenses.content_id values reference existing content",
            violations=result or 0,
        )

        # Check licenses.licensee_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                LEFT JOIN creators cr ON l.licensee_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_license_licensee",
            result == 0,
            "All licenses.licensee_id values reference existing creators",
            violations=result or 0,
        )

        # Check licenses.licensor_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                LEFT JOIN creators cr ON l.licensor_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_license_licensor",
            result == 0,
            "All licenses.licensor_id values reference existing creators",
            violations=result or 0,
        )

        # Check quality_scores.content_id references content.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM quality_scores q
                LEFT JOIN content c ON q.content_id = c.id
                WHERE c.id IS NULL
            """)).scalar()
        self._check(
            "fk_quality_content",
            result == 0,
            "All quality_scores.content_id values reference existing content",
            violations=result or 0,
        )

        # Check fraud_reports.reporter_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports f
                LEFT JOIN creators cr ON f.reporter_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_fraud_reporter",
            result == 0,
            "All fraud_reports.reporter_id values reference existing creators",
            violations=result or 0,
        )

        # Check moderation_actions.moderator_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM moderation_actions m
                LEFT JOIN creators cr ON m.moderator_id = cr.id
                WHERE m.moderator_id IS NOT NULL AND cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_moderation_moderator",
            result == 0,
            "All moderation_actions.moderator_id values reference existing creators",
            violations=result or 0,
        )

        # Check analytics_events.user_id references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM analytics_events a
                LEFT JOIN creators cr ON a.user_id = cr.id
                WHERE a.user_id IS NOT NULL AND cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_analytics_user",
            result == 0,
            "All analytics_events.user_id values reference existing creators",
            violations=result or 0,
        )

        # Check audit_log.changed_by references creators.id
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM audit_log a
                LEFT JOIN creators cr ON a.changed_by = cr.id
                WHERE a.changed_by IS NOT NULL AND cr.id IS NULL
            """)).scalar()
        self._check(
            "fk_audit_changed_by",
            result == 0,
            "All audit_log.changed_by values reference existing creators",
            violations=result or 0,
        )

    def check_business_rules(self) -> None:
        """Verify business rules are enforced."""
        # Check buyer != seller in transactions
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE buyer_id = seller_id
            """)).scalar()
        self._check(
            "business_buyer_seller_different",
            result == 0,
            "No transactions have buyer_id == seller_id",
            violations=result or 0,
        )

        # Check reputation_score is between 0 and 100
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE reputation_score < 0 OR reputation_score > 100
            """)).scalar()
        self._check(
            "business_reputation_range",
            result == 0,
            "All reputation scores are between 0 and 100",
            violations=result or 0,
        )

        # Check total_earnings is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE total_earnings < 0
            """)).scalar()
        self._check(
            "business_earnings_non_negative",
            result == 0,
            "All total_earnings values are non-negative",
            violations=result or 0,
        )

        # Check total_sales is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE total_sales < 0
            """)).scalar()
        self._check(
            "business_sales_non_negative",
            result == 0,
            "All total_sales values are non-negative",
            violations=result or 0,
        )

        # Check view_count is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE view_count < 0
            """)).scalar()
        self._check(
            "business_view_count_non_negative",
            result == 0,
            "All view_count values are non-negative",
            violations=result or 0,
        )

        # Check like_count is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE like_count < 0
            """)).scalar()
        self._check(
            "business_like_count_non_negative",
            result == 0,
            "All like_count values are non-negative",
            violations=result or 0,
        )

        # Check price is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE price < 0
            """)).scalar()
        self._check(
            "business_price_non_negative",
            result == 0,
            "All listing prices are non-negative",
            violations=result or 0,
        )

        # Check sales_count is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE sales_count < 0
            """)).scalar()
        self._check(
            "business_sales_count_non_negative",
            result == 0,
            "All sales_count values are non-negative",
            violations=result or 0,
        )

        # Check amount is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE amount < 0
            """)).scalar()
        self._check(
            "business_amount_non_negative",
            result == 0,
            "All transaction amounts are non-negative",
            violations=result or 0,
        )

        # Check platform_fee is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE platform_fee < 0
            """)).scalar()
        self._check(
            "business_platform_fee_non_negative",
            result == 0,
            "All platform_fee values are non-negative",
            violations=result or 0,
        )

        # Check seller_earnings is non-negative
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE seller_earnings < 0
            """)).scalar()
        self._check(
            "business_seller_earnings_non_negative",
            result == 0,
            "All seller_earnings values are non-negative",
            violations=result or 0,
        )

        # Check quality scores are between 0 and 1
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM quality_scores
                WHERE overall_score < 0 OR overall_score > 1
            """)).scalar()
        self._check(
            "business_quality_score_range",
            result == 0,
            "All quality scores are between 0 and 1",
            violations=result or 0,
        )

        # Check valid_until > valid_from in licenses
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses
                WHERE valid_until IS NOT NULL AND valid_until <= valid_from
            """)).scalar()
        self._check(
            "business_license_validity",
            result == 0,
            "All licenses have valid_until > valid_from",
            violations=result or 0,
        )

        # Check resolved fraud reports have resolution details
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports
                WHERE status IN ('resolved', 'dismissed')
                AND (resolution IS NULL OR resolved_by IS NULL OR resolved_at IS NULL)
            """)).scalar()
        self._check(
            "business_resolved_fraud_complete",
            result == 0,
            "All resolved/dismissed fraud reports have complete resolution details",
            violations=result or 0,
        )

        # Check open fraud reports don't have resolution details
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports
                WHERE status = 'open'
                AND (resolution IS NOT NULL OR resolved_by IS NOT NULL OR resolved_at IS NOT NULL)
            """)).scalar()
        self._check(
            "business_open_fraud_no_resolution",
            result == 0,
            "Open fraud reports don't have resolution details",
            violations=result or 0,
        )

    def check_data_ranges(self) -> None:
        """Verify data values are within expected ranges."""
        # Check username length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE LENGTH(username) > 50
            """)).scalar()
        self._check(
            "range_username_length",
            result == 0,
            "All usernames are <= 50 characters",
            violations=result or 0,
        )

        # Check email length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE LENGTH(email) > 255
            """)).scalar()
        self._check(
            "range_email_length",
            result == 0,
            "All emails are <= 255 characters",
            violations=result or 0,
        )

        # Check display_name length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE display_name IS NOT NULL AND LENGTH(display_name) > 100
            """)).scalar()
        self._check(
            "range_display_name_length",
            result == 0,
            "All display names are <= 100 characters",
            violations=result or 0,
        )

        # Check title length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE LENGTH(title) > 255
            """)).scalar()
        self._check(
            "range_content_title_length",
            result == 0,
            "All content titles are <= 255 characters",
            violations=result or 0,
        )

        # Check currency length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE LENGTH(currency) != 3
            """)).scalar()
        self._check(
            "range_currency_length",
            result == 0,
            "All currency codes are exactly 3 characters",
            violations=result or 0,
        )

        # Check content_type length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE LENGTH(content_type) > 50
            """)).scalar()
        self._check(
            "range_content_type_length",
            result == 0,
            "All content types are <= 50 characters",
            violations=result or 0,
        )

        # Check license_type length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE LENGTH(license_type) > 50
            """)).scalar()
        self._check(
            "range_license_type_length",
            result == 0,
            "All license types are <= 50 characters",
            violations=result or 0,
        )

        # Check event_type length
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM analytics_events
                WHERE LENGTH(event_type) > 100
            """)).scalar()
        self._check(
            "range_event_type_length",
            result == 0,
            "All event types are <= 100 characters",
            violations=result or 0,
        )

        # Check table_name length in audit_log
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM audit_log
                WHERE LENGTH(table_name) > 100
            """)).scalar()
        self._check(
            "range_audit_table_name_length",
            result == 0,
            "All audit log table names are <= 100 characters",
            violations=result or 0,
        )

    def check_referential_integrity(self) -> None:
        """Verify referential integrity across all relationships."""
        # Check that content.creator exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content c
                WHERE NOT EXISTS (SELECT 1 FROM creators cr WHERE cr.id = c.creator_id)
            """)).scalar()
        self._check(
            "ref_content_creator_exists",
            result == 0,
            "All content creators exist",
            violations=result or 0,
        )

        # Check that listing.content exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings l
                WHERE NOT EXISTS (SELECT 1 FROM content c WHERE c.id = l.content_id)
            """)).scalar()
        self._check(
            "ref_listing_content_exists",
            result == 0,
            "All listing content items exist",
            violations=result or 0,
        )

        # Check that listing.creator exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings l
                WHERE NOT EXISTS (SELECT 1 FROM creators cr WHERE cr.id = l.creator_id)
            """)).scalar()
        self._check(
            "ref_listing_creator_exists",
            result == 0,
            "All listing creators exist",
            violations=result or 0,
        )

        # Check that transaction.listing exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions t
                WHERE NOT EXISTS (SELECT 1 FROM listings l WHERE l.id = t.listing_id)
            """)).scalar()
        self._check(
            "ref_transaction_listing_exists",
            result == 0,
            "All transaction listings exist",
            violations=result or 0,
        )

        # Check that license.transaction exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                WHERE NOT EXISTS (SELECT 1 FROM transactions t WHERE t.id = l.transaction_id)
            """)).scalar()
        self._check(
            "ref_license_transaction_exists",
            result == 0,
            "All license transactions exist",
            violations=result or 0,
        )

        # Check that quality_score.content exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM quality_scores q
                WHERE NOT EXISTS (SELECT 1 FROM content c WHERE c.id = q.content_id)
            """)).scalar()
        self._check(
            "ref_quality_content_exists",
            result == 0,
            "All quality score content items exist",
            violations=result or 0,
        )

        # Check that fraud_report.reporter exists
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports f
                WHERE NOT EXISTS (SELECT 1 FROM creators cr WHERE cr.id = f.reporter_id)
            """)).scalar()
        self._check(
            "ref_fraud_reporter_exists",
            result == 0,
            "All fraud report reporters exist",
            violations=result or 0,
        )

    def check_orphaned_records(self) -> None:
        """Check for orphaned records that shouldn't exist."""
        # Check for content without creators (shouldn't happen with CASCADE)
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content c
                LEFT JOIN creators cr ON c.creator_id = cr.id
                WHERE cr.id IS NULL
            """)).scalar()
        self._check(
            "orphan_content_no_creator",
            result == 0,
            "No orphaned content without creators",
            violations=result or 0,
        )

        # Check for listings without content
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings l
                LEFT JOIN content c ON l.content_id = c.id
                WHERE c.id IS NULL
            """)).scalar()
        self._check(
            "orphan_listing_no_content",
            result == 0,
            "No orphaned listings without content",
            violations=result or 0,
        )

        # Check for transactions without listings
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN listings l ON t.listing_id = l.id
                WHERE l.id IS NULL
            """)).scalar()
        self._check(
            "orphan_transaction_no_listing",
            result == 0,
            "No orphaned transactions without listings",
            violations=result or 0,
        )

        # Check for licenses without transactions
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses l
                LEFT JOIN transactions t ON l.transaction_id = t.id
                WHERE t.id IS NULL
            """)).scalar()
        self._check(
            "orphan_license_no_transaction",
            result == 0,
            "No orphaned licenses without transactions",
            violations=result or 0,
        )

        # Check for quality scores without content
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM quality_scores q
                LEFT JOIN content c ON q.content_id = c.id
                WHERE c.id IS NULL
            """)).scalar()
        self._check(
            "orphan_quality_no_content",
            result == 0,
            "No orphaned quality scores without content",
            violations=result or 0,
        )

    def check_duplicate_data(self) -> None:
        """Check for duplicate data that violates unique constraints."""
        # Check for duplicate usernames
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT username FROM creators
                    GROUP BY username HAVING COUNT(*) > 1
                ) dupes
            """)).scalar()
        self._check(
            "duplicate_usernames",
            result == 0,
            "No duplicate usernames",
            violations=result or 0,
        )

        # Check for duplicate emails
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT email FROM creators
                    GROUP BY email HAVING COUNT(*) > 1
                ) dupes
            """)).scalar()
        self._check(
            "duplicate_emails",
            result == 0,
            "No duplicate emails",
            violations=result or 0,
        )

    def check_temporal_consistency(self) -> None:
        """Check temporal consistency (created_at <= updated_at, etc.)."""
        # Check content created_at <= updated_at
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE created_at > updated_at
            """)).scalar()
        self._check(
            "temporal_content_timestamps",
            result == 0,
            "All content has created_at <= updated_at",
            violations=result or 0,
        )

        # Check listings created_at <= updated_at
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE created_at > updated_at
            """)).scalar()
        self._check(
            "temporal_listing_timestamps",
            result == 0,
            "All listings have created_at <= updated_at",
            violations=result or 0,
        )

        # Check transactions created_at <= updated_at
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE created_at > updated_at
            """)).scalar()
        self._check(
            "temporal_transaction_timestamps",
            result == 0,
            "All transactions have created_at <= updated_at",
            violations=result or 0,
        )

        # Check licenses created_at <= updated_at
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses
                WHERE created_at > updated_at
            """)).scalar()
        self._check(
            "temporal_license_timestamps",
            result == 0,
            "All licenses have created_at <= updated_at",
            violations=result or 0,
        )

        # Check fraud reports resolved_at >= created_at
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports
                WHERE resolved_at IS NOT NULL AND resolved_at < created_at
            """)).scalar()
        self._check(
            "temporal_fraud_resolved_after_created",
            result == 0,
            "All resolved fraud reports have resolved_at >= created_at",
            violations=result or 0,
        )

    def check_json_field_validity(self) -> None:
        """Check that JSON fields contain valid data."""
        # Check creators.social_links is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM creators
                WHERE social_links IS NOT NULL AND jsonb_typeof(social_links) != 'object'
            """)).scalar()
        self._check(
            "json_creator_social_links",
            result == 0,
            "All creator social_links are valid JSON objects",
            violations=result or 0,
        )

        # Check content.metadata is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM content
                WHERE metadata IS NOT NULL AND jsonb_typeof(metadata) != 'object'
            """)).scalar()
        self._check(
            "json_content_metadata",
            result == 0,
            "All content metadata are valid JSON objects",
            violations=result or 0,
        )

        # Check listings.usage_rights is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM listings
                WHERE usage_rights IS NOT NULL AND jsonb_typeof(usage_rights) != 'object'
            """)).scalar()
        self._check(
            "json_listing_usage_rights",
            result == 0,
            "All listing usage_rights are valid JSON objects",
            violations=result or 0,
        )

        # Check transactions.metadata is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE metadata IS NOT NULL AND jsonb_typeof(metadata) != 'object'
            """)).scalar()
        self._check(
            "json_transaction_metadata",
            result == 0,
            "All transaction metadata are valid JSON objects",
            violations=result or 0,
        )

        # Check licenses.usage_scope is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM licenses
                WHERE usage_scope IS NOT NULL AND jsonb_typeof(usage_scope) != 'object'
            """)).scalar()
        self._check(
            "json_license_usage_scope",
            result == 0,
            "All license usage_scope are valid JSON objects",
            violations=result or 0,
        )

        # Check quality_scores.details is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM quality_scores
                WHERE details IS NOT NULL AND jsonb_typeof(details) != 'object'
            """)).scalar()
        self._check(
            "json_quality_details",
            result == 0,
            "All quality score details are valid JSON objects",
            violations=result or 0,
        )

        # Check fraud_reports.evidence is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM fraud_reports
                WHERE evidence IS NOT NULL AND jsonb_typeof(evidence) != 'object'
            """)).scalar()
        self._check(
            "json_fraud_evidence",
            result == 0,
            "All fraud report evidence are valid JSON objects",
            violations=result or 0,
        )

        # Check moderation_actions.details is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM moderation_actions
                WHERE details IS NOT NULL AND jsonb_typeof(details) != 'object'
            """)).scalar()
        self._check(
            "json_moderation_details",
            result == 0,
            "All moderation action details are valid JSON objects",
            violations=result or 0,
        )

        # Check analytics_events.event_data is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM analytics_events
                WHERE event_data IS NOT NULL AND jsonb_typeof(event_data) != 'object'
            """)).scalar()
        self._check(
            "json_analytics_event_data",
            result == 0,
            "All analytics event data are valid JSON objects",
            violations=result or 0,
        )

        # Check audit_log.old_values is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM audit_log
                WHERE old_values IS NOT NULL AND jsonb_typeof(old_values) != 'object'
            """)).scalar()
        self._check(
            "json_audit_old_values",
            result == 0,
            "All audit log old_values are valid JSON objects",
            violations=result or 0,
        )

        # Check audit_log.new_values is valid JSON
        result = self.session.execute(text("""
                SELECT COUNT(*) FROM audit_log
                WHERE new_values IS NOT NULL AND jsonb_typeof(new_values) != 'object'
            """)).scalar()
        self._check(
            "json_audit_new_values",
            result == 0,
            "All audit log new_values are valid JSON objects",
            violations=result or 0,
        )


def run_consistency_checks(session: Session) -> ConsistencyReport:
    """Run all consistency checks and return the report.

    Args:
        session: SQLAlchemy session.

    Returns:
        ConsistencyReport with all results.
    """
    checker = ConsistencyChecker(session)
    return checker.run_all()
