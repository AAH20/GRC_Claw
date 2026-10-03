"""Seeder scripts for UGC Marketplace test data.

This module provides functions to seed the database with realistic test data
for development, testing, and demonstration purposes. It supports both
synchronous and asynchronous database sessions.

Usage:
    # Synchronous usage
    from ugc_marketplace.database.seeders.seeders import seed_all
    seed_all(session, num_creators=50, num_content_per_creator=5)

    # Asynchronous usage
    from ugc_marketplace.database.seeders.seeders import seed_all_async
    await seed_all_async(async_session, num_creators=50, num_content_per_creator=5)
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ugc_marketplace.database.seeders.factories import (
    ActiveListingFactory,
    AnalyticsEventFactory,
    AuditLogFactory,
    CommercialLicenseFactory,
    CompletedTransactionFactory,
    ContentFactory,
    CreatorFactory,
    DraftContentFactory,
    FraudReportFactory,
    LicenseFactory,
    ListingFactory,
    ModerationActionFactory,
    OpenFraudReportFactory,
    PendingTransactionFactory,
    PublishedContentFactory,
    QualityScoreFactory,
    RefundedTransactionFactory,
    ResolvedFraudReportFactory,
    SuspendedCreatorFactory,
    TransactionFactory,
    VerifiedCreatorFactory,
)
from ugc_marketplace.database.seeders.models import (
    AnalyticsEvent,
    AuditLog,
    Content,
    ContentStatus,
    Creator,
    FraudReport,
    FraudReportStatus,
    License,
    LicenseType,
    Listing,
    ModerationAction,
    PaymentStatus,
    QualityScore,
    Transaction,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Synchronous Seeders
# ---------------------------------------------------------------------------
def seed_creators(
    session: Session,
    count: int = 50,
    *,
    verified_ratio: float = 0.6,
    suspended_ratio: float = 0.05,
) -> list[Creator]:
    """Seed creators with realistic data.

    Args:
        session: SQLAlchemy session.
        count: Number of creators to create.
        verified_ratio: Ratio of verified creators (0.0 to 1.0).
        suspended_ratio: Ratio of suspended creators (0.0 to 1.0).

    Returns:
        List of created Creator instances.
    """
    creators: list[Creator] = []
    verified_count = int(count * verified_ratio)
    suspended_count = int(count * suspended_ratio)
    unverified_count = count - verified_count - suspended_count

    for _ in range(verified_count):
        creator = VerifiedCreatorFactory()
        session.add(creator)
        creators.append(creator)

    for _ in range(suspended_count):
        creator = SuspendedCreatorFactory()
        session.add(creator)
        creators.append(creator)

    for _ in range(unverified_count):
        creator = CreatorFactory()
        session.add(creator)
        creators.append(creator)

    session.flush()
    logger.info("Seeded %d creators (%d verified, %d suspended, %d unverified)",
                count, verified_count, suspended_count, unverified_count)
    return creators


def seed_content(
    session: Session,
    creators: Sequence[Creator],
    *,
    per_creator: int = 5,
    published_ratio: float = 0.7,
    draft_ratio: float = 0.2,
) -> list[Content]:
    """Seed content for given creators.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances to create content for.
        per_creator: Number of content items per creator.
        published_ratio: Ratio of published content.
        draft_ratio: Ratio of draft content.

    Returns:
        List of created Content instances.
    """
    content_items: list[Content] = []

    for creator in creators:
        published_count = int(per_creator * published_ratio)
        draft_count = int(per_creator * draft_ratio)
        other_count = per_creator - published_count - draft_count

        for _ in range(published_count):
            content = PublishedContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

        for _ in range(draft_count):
            content = DraftContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

        for _ in range(other_count):
            content = ContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

    session.flush()
    logger.info("Seeded %d content items for %d creators", len(content_items), len(creators))
    return content_items


def seed_listings(
    session: Session,
    content_items: Sequence[Content],
    *,
    per_content: int = 2,
    active_ratio: float = 0.8,
) -> list[Listing]:
    """Seed listings for given content.

    Args:
        session: SQLAlchemy session.
        content_items: List of Content instances to create listings for.
        per_content: Number of listings per content item.
        active_ratio: Ratio of active listings.

    Returns:
        List of created Listing instances.
    """
    listings: list[Listing] = []

    for content in content_items:
        if content.status != ContentStatus.PUBLISHED:
            continue

        active_count = int(per_content * active_ratio)
        inactive_count = per_content - active_count

        for _ in range(active_count):
            listing = ActiveListingFactory(content=content, creator=content.creator)
            session.add(listing)
            listings.append(listing)

        for _ in range(inactive_count):
            listing = ListingFactory(content=content, creator=content.creator, is_active=False)
            session.add(listing)
            listings.append(listing)

    session.flush()
    logger.info("Seeded %d listings for %d content items", len(listings), len(content_items))
    return listings


def seed_transactions(
    session: Session,
    listings: Sequence[Listing],
    buyers: Sequence[Creator],
    *,
    per_listing: int = 3,
    completed_ratio: float = 0.7,
    pending_ratio: float = 0.15,
    refunded_ratio: float = 0.1,
) -> list[Transaction]:
    """Seed transactions for given listings.

    Args:
        session: SQLAlchemy session.
        listings: List of Listing instances to create transactions for.
        buyers: List of Creator instances to use as buyers.
        per_listing: Number of transactions per listing.
        completed_ratio: Ratio of completed transactions.
        pending_ratio: Ratio of pending transactions.
        refunded_ratio: Ratio of refunded transactions.

    Returns:
        List of created Transaction instances.
    """
    transactions: list[Transaction] = []

    for listing in listings:
        if not listing.is_active:
            continue

        completed_count = int(per_listing * completed_ratio)
        pending_count = int(per_listing * pending_ratio)
        refunded_count = int(per_listing * refunded_ratio)
        other_count = per_listing - completed_count - pending_count - refunded_count

        for _ in range(completed_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = CompletedTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(pending_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = PendingTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(refunded_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = RefundedTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(other_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = TransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

    session.flush()
    logger.info("Seeded %d transactions for %d listings", len(transactions), len(listings))
    return transactions


def seed_licenses(
    session: Session,
    transactions: Sequence[Transaction],
    *,
    per_transaction: int = 1,
) -> list[License]:
    """Seed licenses for given transactions.

    Args:
        session: SQLAlchemy session.
        transactions: List of Transaction instances to create licenses for.
        per_transaction: Number of licenses per transaction.

    Returns:
        List of created License instances.
    """
    licenses: list[License] = []

    for transaction in transactions:
        if transaction.payment_status != PaymentStatus.COMPLETED:
            continue

        for _ in range(per_transaction):
            license_type = random.choice(list(LicenseType))
            if license_type == LicenseType.COMMERCIAL:
                license_obj = CommercialLicenseFactory(transaction=transaction)
            elif license_type == LicenseType.PERSONAL:
                license_obj = PersonalLicenseFactory(transaction=transaction)
            else:
                license_obj = LicenseFactory(transaction=transaction)
            session.add(license_obj)
            licenses.append(license_obj)

    session.flush()
    logger.info("Seeded %d licenses for %d transactions", len(licenses), len(transactions))
    return licenses


def seed_moderation_actions(
    session: Session,
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    moderators: Sequence[Creator],
    *,
    count: int = 100,
) -> list[ModerationAction]:
    """Seed moderation actions.

    Args:
        session: SQLAlchemy session.
        content_items: List of Content instances.
        listings: List of Listing instances.
        moderators: List of Creator instances to use as moderators.
        count: Number of moderation actions to create.

    Returns:
        List of created ModerationAction instances.
    """
    actions: list[ModerationAction] = []

    for _ in range(count):
        moderator = random.choice(moderators)
        if random.random() > 0.3 and content_items:
            content = random.choice(content_items)
            action = ModerationActionFactory(content=content, moderator=moderator)
        elif listings:
            listing = random.choice(listings)
            action = ModerationActionFactory(listing=listing, moderator=moderator)
        else:
            action = ModerationActionFactory(moderator=moderator)
        session.add(action)
        actions.append(action)

    session.flush()
    logger.info("Seeded %d moderation actions", len(actions))
    return actions


def seed_quality_scores(
    session: Session,
    content_items: Sequence[Content],
    *,
    per_content: int = 1,
) -> list[QualityScore]:
    """Seed quality scores for content.

    Args:
        session: SQLAlchemy session.
        content_items: List of Content instances.
        per_content: Number of quality scores per content item.

    Returns:
        List of created QualityScore instances.
    """
    scores: list[QualityScore] = []

    for content in content_items:
        for _ in range(per_content):
            score = QualityScoreFactory(content=content)
            session.add(score)
            scores.append(score)

    session.flush()
    logger.info("Seeded %d quality scores for %d content items", len(scores), len(content_items))
    return scores


def seed_fraud_reports(
    session: Session,
    creators: Sequence[Creator],
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    *,
    count: int = 50,
) -> list[FraudReport]:
    """Seed fraud reports.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        content_items: List of Content instances.
        listings: List of Listing instances.
        count: Number of fraud reports to create.

    Returns:
        List of created FraudReport instances.
    """
    reports: list[FraudReport] = []

    for _ in range(count):
        reporter = random.choice(creators)
        status = random.choice(list(FraudReportStatus))

        if status == FraudReportStatus.RESOLVED:
            report = ResolvedFraudReportFactory(reporter=reporter)
        elif status == FraudReportStatus.OPEN:
            report = OpenFraudReportFactory(reporter=reporter)
        else:
            report = FraudReportFactory(reporter=reporter)

        if content_items and random.random() > 0.4:
            report.reported_content = random.choice(content_items)
        if listings and random.random() > 0.5:
            report.reported_listing = random.choice(listings)
        if random.random() > 0.6:
            report.reported_user = random.choice(creators)

        session.add(report)
        reports.append(report)

    session.flush()
    logger.info("Seeded %d fraud reports", len(reports))
    return reports


def seed_analytics_events(
    session: Session,
    creators: Sequence[Creator],
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    *,
    count: int = 1000,
) -> list[AnalyticsEvent]:
    """Seed analytics events.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        content_items: List of Content instances.
        listings: List of Listing instances.
        count: Number of analytics events to create.

    Returns:
        List of created AnalyticsEvent instances.
    """
    events: list[AnalyticsEvent] = []

    for _ in range(count):
        user = random.choice(creators) if creators and random.random() > 0.3 else None
        content = random.choice(content_items) if content_items and random.random() > 0.5 else None
        listing = random.choice(listings) if listings and random.random() > 0.6 else None

        event = AnalyticsEventFactory(user=user, content=content, listing=listing)
        session.add(event)
        events.append(event)

    session.flush()
    logger.info("Seeded %d analytics events", len(events))
    return events


def seed_audit_logs(
    session: Session,
    creators: Sequence[Creator],
    *,
    count: int = 200,
) -> list[AuditLog]:
    """Seed audit log entries.

    Args:
        session: SQLAlchemy session.
        creators: List of Creator instances.
        count: Number of audit log entries to create.

    Returns:
        List of created AuditLog instances.
    """
    logs: list[AuditLog] = []

    for _ in range(count):
        changed_by = random.choice(creators) if creators and random.random() > 0.3 else None
        log = AuditLogFactory(changed_by=changed_by)
        session.add(log)
        logs.append(log)

    session.flush()
    logger.info("Seeded %d audit log entries", len(logs))
    return logs


def seed_all(
    session: Session,
    *,
    num_creators: int = 50,
    num_content_per_creator: int = 5,
    num_listings_per_content: int = 2,
    num_transactions_per_listing: int = 3,
    num_licenses_per_transaction: int = 1,
    num_moderation_actions: int = 100,
    num_quality_scores_per_content: int = 1,
    num_fraud_reports: int = 50,
    num_analytics_events: int = 1000,
    num_audit_logs: int = 200,
) -> dict[str, list[Any]]:
    """Seed the database with all test data.

    This is the main entry point for seeding the database. It creates
    a complete set of related test data.

    Args:
        session: SQLAlchemy session.
        num_creators: Number of creators to create.
        num_content_per_creator: Number of content items per creator.
        num_listings_per_content: Number of listings per content item.
        num_transactions_per_listing: Number of transactions per listing.
        num_licenses_per_transaction: Number of licenses per transaction.
        num_moderation_actions: Number of moderation actions to create.
        num_quality_scores_per_content: Number of quality scores per content item.
        num_fraud_reports: Number of fraud reports to create.
        num_analytics_events: Number of analytics events to create.
        num_audit_logs: Number of audit log entries to create.

    Returns:
        Dictionary with lists of created instances by type.
    """
    logger.info("Starting database seed with %d creators", num_creators)

    creators = seed_creators(session, num_creators)
    content_items = seed_content(session, creators, per_creator=num_content_per_creator)
    listings = seed_listings(session, content_items, per_content=num_listings_per_content)
    transactions = seed_transactions(
        session, listings, buyers=creators, per_listing=num_transactions_per_listing
    )
    licenses = seed_licenses(session, transactions, per_transaction=num_licenses_per_transaction)
    moderation_actions = seed_moderation_actions(
        session, content_items, listings, moderators=creators, count=num_moderation_actions
    )
    quality_scores = seed_quality_scores(
        session, content_items, per_content=num_quality_scores_per_content
    )
    fraud_reports = seed_fraud_reports(
        session, creators, content_items, listings, count=num_fraud_reports
    )
    analytics_events = seed_analytics_events(
        session, creators, content_items, listings, count=num_analytics_events
    )
    audit_logs = seed_audit_logs(session, creators, count=num_audit_logs)

    session.commit()
    logger.info("Database seed completed successfully")

    return {
        "creators": creators,
        "content": content_items,
        "listings": listings,
        "transactions": transactions,
        "licenses": licenses,
        "moderation_actions": moderation_actions,
        "quality_scores": quality_scores,
        "fraud_reports": fraud_reports,
        "analytics_events": analytics_events,
        "audit_logs": audit_logs,
    }


# ---------------------------------------------------------------------------
# Asynchronous Seeders
# ---------------------------------------------------------------------------
async def seed_creators_async(
    session: AsyncSession,
    count: int = 50,
    *,
    verified_ratio: float = 0.6,
    suspended_ratio: float = 0.05,
) -> list[Creator]:
    """Async version of seed_creators."""
    creators: list[Creator] = []
    verified_count = int(count * verified_ratio)
    suspended_count = int(count * suspended_ratio)
    unverified_count = count - verified_count - suspended_count

    for _ in range(verified_count):
        creator = VerifiedCreatorFactory()
        session.add(creator)
        creators.append(creator)

    for _ in range(suspended_count):
        creator = SuspendedCreatorFactory()
        session.add(creator)
        creators.append(creator)

    for _ in range(unverified_count):
        creator = CreatorFactory()
        session.add(creator)
        creators.append(creator)

    await session.flush()
    logger.info("Seeded %d creators asynchronously", count)
    return creators


async def seed_content_async(
    session: AsyncSession,
    creators: Sequence[Creator],
    *,
    per_creator: int = 5,
    published_ratio: float = 0.7,
    draft_ratio: float = 0.2,
) -> list[Content]:
    """Async version of seed_content."""
    content_items: list[Content] = []

    for creator in creators:
        published_count = int(per_creator * published_ratio)
        draft_count = int(per_creator * draft_ratio)
        other_count = per_creator - published_count - draft_count

        for _ in range(published_count):
            content = PublishedContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

        for _ in range(draft_count):
            content = DraftContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

        for _ in range(other_count):
            content = ContentFactory(creator=creator)
            session.add(content)
            content_items.append(content)

    await session.flush()
    logger.info("Seeded %d content items asynchronously", len(content_items))
    return content_items


async def seed_listings_async(
    session: AsyncSession,
    content_items: Sequence[Content],
    *,
    per_content: int = 2,
    active_ratio: float = 0.8,
) -> list[Listing]:
    """Async version of seed_listings."""
    listings: list[Listing] = []

    for content in content_items:
        if content.status != ContentStatus.PUBLISHED:
            continue

        active_count = int(per_content * active_ratio)
        inactive_count = per_content - active_count

        for _ in range(active_count):
            listing = ActiveListingFactory(content=content, creator=content.creator)
            session.add(listing)
            listings.append(listing)

        for _ in range(inactive_count):
            listing = ListingFactory(content=content, creator=content.creator, is_active=False)
            session.add(listing)
            listings.append(listing)

    await session.flush()
    logger.info("Seeded %d listings asynchronously", len(listings))
    return listings


async def seed_transactions_async(
    session: AsyncSession,
    listings: Sequence[Listing],
    buyers: Sequence[Creator],
    *,
    per_listing: int = 3,
    completed_ratio: float = 0.7,
    pending_ratio: float = 0.15,
    refunded_ratio: float = 0.1,
) -> list[Transaction]:
    """Async version of seed_transactions."""
    transactions: list[Transaction] = []

    for listing in listings:
        if not listing.is_active:
            continue

        completed_count = int(per_listing * completed_ratio)
        pending_count = int(per_listing * pending_ratio)
        refunded_count = int(per_listing * refunded_ratio)
        other_count = per_listing - completed_count - pending_count - refunded_count

        for _ in range(completed_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = CompletedTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(pending_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = PendingTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(refunded_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = RefundedTransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

        for _ in range(other_count):
            buyer = random.choice(buyers)
            if buyer.id == listing.creator_id:
                continue
            transaction = TransactionFactory(listing=listing, buyer=buyer, seller=listing.creator)
            session.add(transaction)
            transactions.append(transaction)

    await session.flush()
    logger.info("Seeded %d transactions asynchronously", len(transactions))
    return transactions


async def seed_licenses_async(
    session: AsyncSession,
    transactions: Sequence[Transaction],
    *,
    per_transaction: int = 1,
) -> list[License]:
    """Async version of seed_licenses."""
    licenses: list[License] = []

    for transaction in transactions:
        if transaction.payment_status != PaymentStatus.COMPLETED:
            continue

        for _ in range(per_transaction):
            license_type = random.choice(list(LicenseType))
            if license_type == LicenseType.COMMERCIAL:
                license_obj = CommercialLicenseFactory(transaction=transaction)
            elif license_type == LicenseType.PERSONAL:
                license_obj = PersonalLicenseFactory(transaction=transaction)
            else:
                license_obj = LicenseFactory(transaction=transaction)
            session.add(license_obj)
            licenses.append(license_obj)

    await session.flush()
    logger.info("Seeded %d licenses asynchronously", len(licenses))
    return licenses


async def seed_moderation_actions_async(
    session: AsyncSession,
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    moderators: Sequence[Creator],
    *,
    count: int = 100,
) -> list[ModerationAction]:
    """Async version of seed_moderation_actions."""
    actions: list[ModerationAction] = []

    for _ in range(count):
        moderator = random.choice(moderators)
        if random.random() > 0.3 and content_items:
            content = random.choice(content_items)
            action = ModerationActionFactory(content=content, moderator=moderator)
        elif listings:
            listing = random.choice(listings)
            action = ModerationActionFactory(listing=listing, moderator=moderator)
        else:
            action = ModerationActionFactory(moderator=moderator)
        session.add(action)
        actions.append(action)

    await session.flush()
    logger.info("Seeded %d moderation actions asynchronously", len(actions))
    return actions


async def seed_quality_scores_async(
    session: AsyncSession,
    content_items: Sequence[Content],
    *,
    per_content: int = 1,
) -> list[QualityScore]:
    """Async version of seed_quality_scores."""
    scores: list[QualityScore] = []

    for content in content_items:
        for _ in range(per_content):
            score = QualityScoreFactory(content=content)
            session.add(score)
            scores.append(score)

    await session.flush()
    logger.info("Seeded %d quality scores asynchronously", len(scores))
    return scores


async def seed_fraud_reports_async(
    session: AsyncSession,
    creators: Sequence[Creator],
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    *,
    count: int = 50,
) -> list[FraudReport]:
    """Async version of seed_fraud_reports."""
    reports: list[FraudReport] = []

    for _ in range(count):
        reporter = random.choice(creators)
        status = random.choice(list(FraudReportStatus))

        if status == FraudReportStatus.RESOLVED:
            report = ResolvedFraudReportFactory(reporter=reporter)
        elif status == FraudReportStatus.OPEN:
            report = OpenFraudReportFactory(reporter=reporter)
        else:
            report = FraudReportFactory(reporter=reporter)

        if content_items and random.random() > 0.4:
            report.reported_content = random.choice(content_items)
        if listings and random.random() > 0.5:
            report.reported_listing = random.choice(listings)
        if random.random() > 0.6:
            report.reported_user = random.choice(creators)

        session.add(report)
        reports.append(report)

    await session.flush()
    logger.info("Seeded %d fraud reports asynchronously", len(reports))
    return reports


async def seed_analytics_events_async(
    session: AsyncSession,
    creators: Sequence[Creator],
    content_items: Sequence[Content],
    listings: Sequence[Listing],
    *,
    count: int = 1000,
) -> list[AnalyticsEvent]:
    """Async version of seed_analytics_events."""
    events: list[AnalyticsEvent] = []

    for _ in range(count):
        user = random.choice(creators) if creators and random.random() > 0.3 else None
        content = random.choice(content_items) if content_items and random.random() > 0.5 else None
        listing = random.choice(listings) if listings and random.random() > 0.6 else None

        event = AnalyticsEventFactory(user=user, content=content, listing=listing)
        session.add(event)
        events.append(event)

    await session.flush()
    logger.info("Seeded %d analytics events asynchronously", len(events))
    return events


async def seed_audit_logs_async(
    session: AsyncSession,
    creators: Sequence[Creator],
    *,
    count: int = 200,
) -> list[AuditLog]:
    """Async version of seed_audit_logs."""
    logs: list[AuditLog] = []

    for _ in range(count):
        changed_by = random.choice(creators) if creators and random.random() > 0.3 else None
        log = AuditLogFactory(changed_by=changed_by)
        session.add(log)
        logs.append(log)

    await session.flush()
    logger.info("Seeded %d audit log entries asynchronously", len(logs))
    return logs


async def seed_all_async(
    session: AsyncSession,
    *,
    num_creators: int = 50,
    num_content_per_creator: int = 5,
    num_listings_per_content: int = 2,
    num_transactions_per_listing: int = 3,
    num_licenses_per_transaction: int = 1,
    num_moderation_actions: int = 100,
    num_quality_scores_per_content: int = 1,
    num_fraud_reports: int = 50,
    num_analytics_events: int = 1000,
    num_audit_logs: int = 200,
) -> dict[str, list[Any]]:
    """Async version of seed_all.

    This is the main entry point for seeding the database asynchronously.
    It creates a complete set of related test data.

    Args:
        session: Async SQLAlchemy session.
        num_creators: Number of creators to create.
        num_content_per_creator: Number of content items per creator.
        num_listings_per_content: Number of listings per content item.
        num_transactions_per_listing: Number of transactions per listing.
        num_licenses_per_transaction: Number of licenses per transaction.
        num_moderation_actions: Number of moderation actions to create.
        num_quality_scores_per_content: Number of quality scores per content item.
        num_fraud_reports: Number of fraud reports to create.
        num_analytics_events: Number of analytics events to create.
        num_audit_logs: Number of audit log entries to create.

    Returns:
        Dictionary with lists of created instances by type.
    """
    logger.info("Starting async database seed with %d creators", num_creators)

    creators = await seed_creators_async(session, num_creators)
    content_items = await seed_content_async(session, creators, per_creator=num_content_per_creator)
    listings = await seed_listings_async(session, content_items, per_content=num_listings_per_content)
    transactions = await seed_transactions_async(
        session, listings, buyers=creators, per_listing=num_transactions_per_listing
    )
    licenses = await seed_licenses_async(session, transactions, per_transaction=num_licenses_per_transaction)
    moderation_actions = await seed_moderation_actions_async(
        session, content_items, listings, moderators=creators, count=num_moderation_actions
    )
    quality_scores = await seed_quality_scores_async(
        session, content_items, per_content=num_quality_scores_per_content
    )
    fraud_reports = await seed_fraud_reports_async(
        session, creators, content_items, listings, count=num_fraud_reports
    )
    analytics_events = await seed_analytics_events_async(
        session, creators, content_items, listings, count=num_analytics_events
    )
    audit_logs = await seed_audit_logs_async(session, creators, count=num_audit_logs)

    await session.commit()
    logger.info("Async database seed completed successfully")

    return {
        "creators": creators,
        "content": content_items,
        "listings": listings,
        "transactions": transactions,
        "licenses": licenses,
        "moderation_actions": moderation_actions,
        "quality_scores": quality_scores,
        "fraud_reports": fraud_reports,
        "analytics_events": analytics_events,
        "audit_logs": audit_logs,
    }


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for running seeders from command line."""
    import argparse
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from ugc_marketplace.database.seeders.models import Base

    parser = argparse.ArgumentParser(description="Seed UGC Marketplace database with test data")
    parser.add_argument("--database-url", default="postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace",
                        help="Database connection URL")
    parser.add_argument("--creators", type=int, default=50, help="Number of creators to create")
    parser.add_argument("--content-per-creator", type=int, default=5, help="Content items per creator")
    parser.add_argument("--listings-per-content", type=int, default=2, help="Listings per content item")
    parser.add_argument("--transactions-per-listing", type=int, default=3, help="Transactions per listing")
    parser.add_argument("--licenses-per-transaction", type=int, default=1, help="Licenses per transaction")
    parser.add_argument("--moderation-actions", type=int, default=100, help="Moderation actions to create")
    parser.add_argument("--quality-scores-per-content", type=int, default=1, help="Quality scores per content item")
    parser.add_argument("--fraud-reports", type=int, default=50, help="Fraud reports to create")
    parser.add_argument("--analytics-events", type=int, default=1000, help="Analytics events to create")
    parser.add_argument("--audit-logs", type=int, default=200, help="Audit log entries to create")
    parser.add_argument("--drop-all", action="store_true", help="Drop all tables before seeding")

    args = parser.parse_args()

    engine = create_engine(args.database_url)

    if args.drop_all:
        Base.metadata.drop_all(engine)
        logger.info("Dropped all tables")

    Base.metadata.create_all(engine)
    logger.info("Created all tables")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        seed_all(
            session,
            num_creators=args.creators,
            num_content_per_creator=args.content_per_creator,
            num_listings_per_content=args.listings_per_content,
            num_transactions_per_listing=args.transactions_per_listing,
            num_licenses_per_transaction=args.licenses_per_transaction,
            num_moderation_actions=args.moderation_actions,
            num_quality_scores_per_content=args.quality_scores_per_content,
            num_fraud_reports=args.fraud_reports,
            num_analytics_events=args.analytics_events,
            num_audit_logs=args.audit_logs,
        )
        logger.info("Seeding completed successfully")
    except Exception as e:
        logger.error("Seeding failed: %s", e)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
