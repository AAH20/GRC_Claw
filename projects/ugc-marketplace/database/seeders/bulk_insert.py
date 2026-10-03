"""Bulk insert optimization for UGC Marketplace database seeders.

This module provides COPY-based bulk insert operations that are significantly
faster than individual INSERT statements for large datasets.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from ugc_marketplace.database.seeders.models import (AnalyticsEvent, AuditLog,
                                                     Content, Creator, License,
                                                     Listing, Transaction)

logger = logging.getLogger(__name__)


class BulkInserter:
    """High-performance bulk inserter using PostgreSQL COPY."""

    def __init__(self, session: Session):
        self.session = session

    def _get_raw_connection(self):
        """Get the raw psycopg2 connection for COPY operations."""
        return self.session.connection().connection

    def _format_value(self, value: Any) -> str:
        """Format a value for COPY text format."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "t" if value else "f"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, list):
            import json

            return json.dumps(value)
        if isinstance(value, dict):
            import json

            return json.dumps(value)
        # Escape special characters for COPY text format
        text = str(value)
        text = text.replace("\\", "\\\\")
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        text = text.replace("\t", "\\t")
        return text

    def bulk_insert_creators(self, creators: Sequence[Creator]) -> int:
        """Bulk insert creators using COPY.

        Args:
            creators: List of Creator instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not creators:
            return 0

        buffer = io.StringIO()
        for creator in creators:
            buffer.write(
                "\t".join(
                    [
                        str(creator.id),
                        self._format_value(creator.username),
                        self._format_value(creator.email),
                        self._format_value(creator.display_name),
                        self._format_value(creator.bio),
                        self._format_value(creator.avatar_url),
                        self._format_value(creator.website_url),
                        self._format_value(creator.social_links),
                        (
                            creator.verification_status.value
                            if creator.verification_status
                            else "unverified"
                        ),
                        (
                            str(creator.reputation_score)
                            if creator.reputation_score
                            else "0.00"
                        ),
                        (
                            str(creator.total_earnings)
                            if creator.total_earnings
                            else "0.00"
                        ),
                        str(creator.total_sales) if creator.total_sales else "0",
                        "t" if creator.is_active else "f",
                        self._format_value(creator.created_at),
                        self._format_value(creator.updated_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "creators",
                columns=[
                    "id",
                    "username",
                    "email",
                    "display_name",
                    "bio",
                    "avatar_url",
                    "website_url",
                    "social_links",
                    "verification_status",
                    "reputation_score",
                    "total_earnings",
                    "total_sales",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d creators via COPY", len(creators))
        return len(creators)

    def bulk_insert_content(self, content_items: Sequence[Content]) -> int:
        """Bulk insert content using COPY.

        Args:
            content_items: List of Content instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not content_items:
            return 0

        buffer = io.StringIO()
        for content in content_items:
            buffer.write(
                "\t".join(
                    [
                        str(content.id),
                        str(content.creator_id),
                        self._format_value(content.title),
                        self._format_value(content.description),
                        self._format_value(content.content_type),
                        self._format_value(content.media_urls),
                        self._format_value(content.tags),
                        self._format_value(content.metadata_),
                        content.status.value if content.status else "draft",
                        "t" if content.is_nsfw else "f",
                        str(content.view_count) if content.view_count else "0",
                        str(content.like_count) if content.like_count else "0",
                        self._format_value(content.created_at),
                        self._format_value(content.updated_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "content",
                columns=[
                    "id",
                    "creator_id",
                    "title",
                    "description",
                    "content_type",
                    "media_urls",
                    "tags",
                    "metadata",
                    "status",
                    "is_nsfw",
                    "view_count",
                    "like_count",
                    "created_at",
                    "updated_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d content items via COPY", len(content_items))
        return len(content_items)

    def bulk_insert_listings(self, listings: Sequence[Listing]) -> int:
        """Bulk insert listings using COPY.

        Args:
            listings: List of Listing instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not listings:
            return 0

        buffer = io.StringIO()
        for listing in listings:
            buffer.write(
                "\t".join(
                    [
                        str(listing.id),
                        str(listing.content_id),
                        str(listing.creator_id),
                        self._format_value(listing.title),
                        self._format_value(listing.description),
                        str(listing.price) if listing.price else "0.00",
                        self._format_value(listing.currency),
                        self._format_value(listing.license_type),
                        self._format_value(listing.usage_rights),
                        "t" if listing.is_active else "f",
                        str(listing.sales_count) if listing.sales_count else "0",
                        self._format_value(listing.created_at),
                        self._format_value(listing.updated_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "listings",
                columns=[
                    "id",
                    "content_id",
                    "creator_id",
                    "title",
                    "description",
                    "price",
                    "currency",
                    "license_type",
                    "usage_rights",
                    "is_active",
                    "sales_count",
                    "created_at",
                    "updated_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d listings via COPY", len(listings))
        return len(listings)

    def bulk_insert_transactions(self, transactions: Sequence[Transaction]) -> int:
        """Bulk insert transactions using COPY.

        Args:
            transactions: List of Transaction instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not transactions:
            return 0

        buffer = io.StringIO()
        for txn in transactions:
            buffer.write(
                "\t".join(
                    [
                        str(txn.id),
                        str(txn.listing_id),
                        str(txn.buyer_id),
                        str(txn.seller_id),
                        str(txn.amount) if txn.amount else "0.00",
                        self._format_value(txn.currency),
                        str(txn.platform_fee) if txn.platform_fee else "0.00",
                        str(txn.seller_earnings) if txn.seller_earnings else "0.00",
                        self._format_value(txn.payment_method),
                        txn.payment_status.value if txn.payment_status else "pending",
                        self._format_value(txn.stripe_payment_intent_id),
                        self._format_value(txn.metadata_),
                        self._format_value(txn.created_at),
                        self._format_value(txn.updated_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "transactions",
                columns=[
                    "id",
                    "listing_id",
                    "buyer_id",
                    "seller_id",
                    "amount",
                    "currency",
                    "platform_fee",
                    "seller_earnings",
                    "payment_method",
                    "payment_status",
                    "stripe_payment_intent_id",
                    "metadata",
                    "created_at",
                    "updated_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d transactions via COPY", len(transactions))
        return len(transactions)

    def bulk_insert_licenses(self, licenses: Sequence[License]) -> int:
        """Bulk insert licenses using COPY.

        Args:
            licenses: List of License instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not licenses:
            return 0

        buffer = io.StringIO()
        for license_obj in licenses:
            buffer.write(
                "\t".join(
                    [
                        str(license_obj.id),
                        str(license_obj.transaction_id),
                        str(license_obj.licensee_id),
                        str(license_obj.licensor_id),
                        str(license_obj.content_id),
                        self._format_value(license_obj.license_type),
                        self._format_value(license_obj.usage_scope),
                        self._format_value(license_obj.valid_from),
                        self._format_value(license_obj.valid_until),
                        "t" if license_obj.is_active else "f",
                        self._format_value(license_obj.created_at),
                        self._format_value(license_obj.updated_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "licenses",
                columns=[
                    "id",
                    "transaction_id",
                    "licensee_id",
                    "licensor_id",
                    "content_id",
                    "license_type",
                    "usage_scope",
                    "valid_from",
                    "valid_until",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d licenses via COPY", len(licenses))
        return len(licenses)

    def bulk_insert_analytics_events(self, events: Sequence[AnalyticsEvent]) -> int:
        """Bulk insert analytics events using COPY.

        Args:
            events: List of AnalyticsEvent instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not events:
            return 0

        buffer = io.StringIO()
        for event in events:
            buffer.write(
                "\t".join(
                    [
                        str(event.id),
                        self._format_value(event.event_type),
                        str(event.user_id) if event.user_id else "",
                        str(event.content_id) if event.content_id else "",
                        str(event.listing_id) if event.listing_id else "",
                        str(event.session_id) if event.session_id else "",
                        self._format_value(event.ip_address),
                        self._format_value(event.user_agent),
                        self._format_value(event.referrer),
                        self._format_value(event.event_data),
                        self._format_value(event.created_at),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "analytics_events",
                columns=[
                    "id",
                    "event_type",
                    "user_id",
                    "content_id",
                    "listing_id",
                    "session_id",
                    "ip_address",
                    "user_agent",
                    "referrer",
                    "event_data",
                    "created_at",
                ],
                null="",
            )

        logger.info("Bulk inserted %d analytics events via COPY", len(events))
        return len(events)

    def bulk_insert_audit_logs(self, logs: Sequence[AuditLog]) -> int:
        """Bulk insert audit logs using COPY.

        Args:
            logs: List of AuditLog instances to insert.

        Returns:
            Number of rows inserted.
        """
        if not logs:
            return 0

        buffer = io.StringIO()
        for log in logs:
            buffer.write(
                "\t".join(
                    [
                        str(log.id),
                        self._format_value(log.table_name),
                        str(log.record_id),
                        self._format_value(log.action),
                        self._format_value(log.old_values),
                        self._format_value(log.new_values),
                        str(log.changed_by) if log.changed_by else "",
                        self._format_value(log.changed_at),
                        self._format_value(log.ip_address),
                        self._format_value(log.user_agent),
                    ]
                )
                + "\n"
            )

        buffer.seek(0)
        raw_conn = self._get_raw_connection()
        with raw_conn.cursor() as cursor:
            cursor.copy_from(
                buffer,
                "audit_log",
                columns=[
                    "id",
                    "table_name",
                    "record_id",
                    "action",
                    "old_values",
                    "new_values",
                    "changed_by",
                    "changed_at",
                    "ip_address",
                    "user_agent",
                ],
                null="",
            )

        logger.info("Bulk inserted %d audit logs via COPY", len(logs))
        return len(logs)


def bulk_insert_all(
    session: Session,
    creators: Sequence[Creator],
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    transactions: Sequence[Transaction],
    licenses: Sequence[License],
    analytics_events: Sequence[AnalyticsEvent],
    audit_logs: Sequence[AuditLog],
) -> dict[str, int]:
    """Bulk insert all entity types using COPY.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        content_items: List of Content instances.
        listings: List of Listing instances.
        transactions: List of Transaction instances.
        licenses: List of License instances.
        analytics_events: List of AnalyticsEvent instances.
        audit_logs: List of AuditLog instances.

    Returns:
        Dictionary with counts of inserted rows by type.
    """
    inserter = BulkInserter(session)

    counts = {
        "creators": inserter.bulk_insert_creators(creators),
        "content": inserter.bulk_insert_content(content_items),
        "listings": inserter.bulk_insert_listings(listings),
        "transactions": inserter.bulk_insert_transactions(transactions),
        "licenses": inserter.bulk_insert_licenses(licenses),
        "analytics_events": inserter.bulk_insert_analytics_events(analytics_events),
        "audit_logs": inserter.bulk_insert_audit_logs(audit_logs),
    }

    session.flush()
    logger.info("Bulk insert completed: %s", counts)
    return counts
