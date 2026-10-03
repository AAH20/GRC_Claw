"""Pytest fixtures for UGC Marketplace database testing.

This module provides pytest fixtures for database testing with both
synchronous and asynchronous sessions. It includes fixtures for
creating test data using factory_boy factories.

Usage:
    # In your test files, import fixtures from this module:
    from ugc_marketplace.database.seeders.conftest import *

    # Or use them directly:
    def test_something(db_session, creator_factory):
        creator = creator_factory()
        assert creator.id is not None
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from ugc_marketplace.database.seeders.factories import (
    ActiveListingFactory, AnalyticsEventFactory, AuditLogFactory,
    CommercialLicenseFactory, CompletedTransactionFactory, ContentFactory,
    CreatorFactory, DraftContentFactory, FraudReportFactory, LicenseFactory,
    ListingFactory, ModerationActionFactory, PendingTransactionFactory,
    PublishedContentFactory, QualityScoreFactory, RefundedTransactionFactory,
    SuspendedCreatorFactory, TransactionFactory, VerifiedCreatorFactory)
from ugc_marketplace.database.seeders.models import (AnalyticsEvent, AuditLog,
                                                     Base, Content, Creator,
                                                     FraudReport, License,
                                                     Listing, ModerationAction,
                                                     QualityScore, Transaction)
from ugc_marketplace.database.seeders.seeders import seed_all, seed_all_async

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace_test"
)
TEST_DATABASE_URL_SYNC = (
    "postgresql://postgres:postgres@localhost:5432/ugc_marketplace_test"
)


# ---------------------------------------------------------------------------
# Session Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def db_engine():
    """Create a synchronous database engine for testing.

    Yields:
        SQLAlchemy engine instance.
    """
    engine = create_engine(TEST_DATABASE_URL_SYNC, poolclass=NullPool)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a synchronous database session for testing.

    This fixture creates a new session for each test function and
    rolls back all changes after the test completes.

    Yields:
        SQLAlchemy Session instance.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest_asyncio.fixture(scope="session")
async def async_db_engine():
    """Create an asynchronous database engine for testing.

    Yields:
        Async SQLAlchemy engine instance.
    """
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an asynchronous database session for testing.

    This fixture creates a new async session for each test function and
    rolls back all changes after the test completes.

    Yields:
        Async SQLAlchemy Session instance.
    """
    async with async_db_engine.connect() as connection, connection.begin() as transaction:
        session = async_sessionmaker(bind=connection, expire_on_commit=False)()
        yield session
        await session.close()
        await transaction.rollback()


# ---------------------------------------------------------------------------
# Factory Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def creator_factory(db_session):
    """Factory fixture for creating Creator instances.

    Returns:
        CreatorFactory bound to the test session.
    """
    return CreatorFactory


@pytest.fixture
def verified_creator_factory(db_session):
    """Factory fixture for creating verified Creator instances.

    Returns:
        VerifiedCreatorFactory bound to the test session.
    """
    return VerifiedCreatorFactory


@pytest.fixture
def suspended_creator_factory(db_session):
    """Factory fixture for creating suspended Creator instances.

    Returns:
        SuspendedCreatorFactory bound to the test session.
    """
    return SuspendedCreatorFactory


@pytest.fixture
def content_factory(db_session):
    """Factory fixture for creating Content instances.

    Returns:
        ContentFactory bound to the test session.
    """
    return ContentFactory


@pytest.fixture
def published_content_factory(db_session):
    """Factory fixture for creating published Content instances.

    Returns:
        PublishedContentFactory bound to the test session.
    """
    return PublishedContentFactory


@pytest.fixture
def draft_content_factory(db_session):
    """Factory fixture for creating draft Content instances.

    Returns:
        DraftContentFactory bound to the test session.
    """
    return DraftContentFactory


@pytest.fixture
def listing_factory(db_session):
    """Factory fixture for creating Listing instances.

    Returns:
        ListingFactory bound to the test session.
    """
    return ListingFactory


@pytest.fixture
def active_listing_factory(db_session):
    """Factory fixture for creating active Listing instances.

    Returns:
        ActiveListingFactory bound to the test session.
    """
    return ActiveListingFactory


@pytest.fixture
def transaction_factory(db_session):
    """Factory fixture for creating Transaction instances.

    Returns:
        TransactionFactory bound to the test session.
    """
    return TransactionFactory


@pytest.fixture
def completed_transaction_factory(db_session):
    """Factory fixture for creating completed Transaction instances.

    Returns:
        CompletedTransactionFactory bound to the test session.
    """
    return CompletedTransactionFactory


@pytest.fixture
def pending_transaction_factory(db_session):
    """Factory fixture for creating pending Transaction instances.

    Returns:
        PendingTransactionFactory bound to the test session.
    """
    return PendingTransactionFactory


@pytest.fixture
def refunded_transaction_factory(db_session):
    """Factory fixture for creating refunded Transaction instances.

    Returns:
        RefundedTransactionFactory bound to the test session.
    """
    return RefundedTransactionFactory


@pytest.fixture
def license_factory(db_session):
    """Factory fixture for creating License instances.

    Returns:
        LicenseFactory bound to the test session.
    """
    return LicenseFactory


@pytest.fixture
def commercial_license_factory(db_session):
    """Factory fixture for creating commercial License instances.

    Returns:
        CommercialLicenseFactory bound to the test session.
    """
    return CommercialLicenseFactory


@pytest.fixture
def moderation_action_factory(db_session):
    """Factory fixture for creating ModerationAction instances.

    Returns:
        ModerationActionFactory bound to the test session.
    """
    return ModerationActionFactory


@pytest.fixture
def quality_score_factory(db_session):
    """Factory fixture for creating QualityScore instances.

    Returns:
        QualityScoreFactory bound to the test session.
    """
    return QualityScoreFactory


@pytest.fixture
def fraud_report_factory(db_session):
    """Factory fixture for creating FraudReport instances.

    Returns:
        FraudReportFactory bound to the test session.
    """
    return FraudReportFactory


@pytest.fixture
def analytics_event_factory(db_session):
    """Factory fixture for creating AnalyticsEvent instances.

    Returns:
        AnalyticsEventFactory bound to the test session.
    """
    return AnalyticsEventFactory


@pytest.fixture
def audit_log_factory(db_session):
    """Factory fixture for creating AuditLog instances.

    Returns:
        AuditLogFactory bound to the test session.
    """
    return AuditLogFactory


# ---------------------------------------------------------------------------
# Data Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_creator(db_session) -> Creator:
    """Create a single sample creator.

    Returns:
        Creator instance.
    """
    creator = CreatorFactory()
    db_session.add(creator)
    db_session.flush()
    return creator


@pytest.fixture
def sample_verified_creator(db_session) -> Creator:
    """Create a single sample verified creator.

    Returns:
        Verified Creator instance.
    """
    creator = VerifiedCreatorFactory()
    db_session.add(creator)
    db_session.flush()
    return creator


@pytest.fixture
def sample_suspended_creator(db_session) -> Creator:
    """Create a single sample suspended creator.

    Returns:
        Suspended Creator instance.
    """
    creator = SuspendedCreatorFactory()
    db_session.add(creator)
    db_session.flush()
    return creator


@pytest.fixture
def sample_content(db_session, sample_creator) -> Content:
    """Create a single sample content item.

    Args:
        sample_creator: Creator instance.

    Returns:
        Content instance.
    """
    content = PublishedContentFactory(creator=sample_creator)
    db_session.add(content)
    db_session.flush()
    return content


@pytest.fixture
def sample_listing(db_session, sample_content) -> Listing:
    """Create a single sample listing.

    Args:
        sample_content: Content instance.

    Returns:
        Listing instance.
    """
    listing = ActiveListingFactory(
        content=sample_content, creator=sample_content.creator
    )
    db_session.add(listing)
    db_session.flush()
    return listing


@pytest.fixture
def sample_transaction(db_session, sample_listing, sample_creator) -> Transaction:
    """Create a single sample transaction.

    Args:
        sample_listing: Listing instance.
        sample_creator: Creator instance (used as buyer).

    Returns:
        Transaction instance.
    """
    transaction = CompletedTransactionFactory(
        listing=sample_listing,
        buyer=sample_creator,
        seller=sample_listing.creator,
    )
    db_session.add(transaction)
    db_session.flush()
    return transaction


@pytest.fixture
def sample_license(db_session, sample_transaction) -> License:
    """Create a single sample license.

    Args:
        sample_transaction: Transaction instance.

    Returns:
        License instance.
    """
    license_obj = CommercialLicenseFactory(transaction=sample_transaction)
    db_session.add(license_obj)
    db_session.flush()
    return license_obj


@pytest.fixture
def sample_quality_score(db_session, sample_content) -> QualityScore:
    """Create a single sample quality score.

    Args:
        sample_content: Content instance.

    Returns:
        QualityScore instance.
    """
    score = QualityScoreFactory(content=sample_content)
    db_session.add(score)
    db_session.flush()
    return score


@pytest.fixture
def sample_moderation_action(
    db_session, sample_content, sample_creator
) -> ModerationAction:
    """Create a single sample moderation action.

    Args:
        sample_content: Content instance.
        sample_creator: Creator instance (used as moderator).

    Returns:
        ModerationAction instance.
    """
    action = ModerationActionFactory(content=sample_content, moderator=sample_creator)
    db_session.add(action)
    db_session.flush()
    return action


@pytest.fixture
def sample_fraud_report(db_session, sample_creator) -> FraudReport:
    """Create a single sample fraud report.

    Args:
        sample_creator: Creator instance (used as reporter).

    Returns:
        FraudReport instance.
    """
    report = FraudReportFactory(reporter=sample_creator)
    db_session.add(report)
    db_session.flush()
    return report


@pytest.fixture
def sample_analytics_event(db_session, sample_creator) -> AnalyticsEvent:
    """Create a single sample analytics event.

    Args:
        sample_creator: Creator instance.

    Returns:
        AnalyticsEvent instance.
    """
    event = AnalyticsEventFactory(user=sample_creator)
    db_session.add(event)
    db_session.flush()
    return event


@pytest.fixture
def sample_audit_log(db_session, sample_creator) -> AuditLog:
    """Create a single sample audit log entry.

    Args:
        sample_creator: Creator instance.

    Returns:
        AuditLog instance.
    """
    log = AuditLogFactory(changed_by=sample_creator)
    db_session.add(log)
    db_session.flush()
    return log


# ---------------------------------------------------------------------------
# Bulk Data Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def creators(db_session, count: int = 10) -> list[Creator]:
    """Create multiple sample creators.

    Args:
        count: Number of creators to create.

    Returns:
        List of Creator instances.
    """
    creators = [CreatorFactory() for _ in range(count)]
    db_session.add_all(creators)
    db_session.flush()
    return creators


@pytest.fixture
def content_items(db_session, sample_creator, count: int = 10) -> list[Content]:
    """Create multiple sample content items.

    Args:
        sample_creator: Creator instance.
        count: Number of content items to create.

    Returns:
        List of Content instances.
    """
    content_items = [
        PublishedContentFactory(creator=sample_creator) for _ in range(count)
    ]
    db_session.add_all(content_items)
    db_session.flush()
    return content_items


@pytest.fixture
def listings(db_session, sample_content, count: int = 10) -> list[Listing]:
    """Create multiple sample listings.

    Args:
        sample_content: Content instance.
        count: Number of listings to create.

    Returns:
        List of Listing instances.
    """
    listings = [
        ActiveListingFactory(content=sample_content, creator=sample_content.creator)
        for _ in range(count)
    ]
    db_session.add_all(listings)
    db_session.flush()
    return listings


@pytest.fixture
def transactions(
    db_session, sample_listing, sample_creator, count: int = 10
) -> list[Transaction]:
    """Create multiple sample transactions.

    Args:
        sample_listing: Listing instance.
        sample_creator: Creator instance (used as buyer).
        count: Number of transactions to create.

    Returns:
        List of Transaction instances.
    """
    transactions = [
        CompletedTransactionFactory(
            listing=sample_listing, buyer=sample_creator, seller=sample_listing.creator
        )
        for _ in range(count)
    ]
    db_session.add_all(transactions)
    db_session.flush()
    return transactions


@pytest.fixture
def licenses(db_session, sample_transaction, count: int = 10) -> list[License]:
    """Create multiple sample licenses.

    Args:
        sample_transaction: Transaction instance.
        count: Number of licenses to create.

    Returns:
        List of License instances.
    """
    licenses = [
        CommercialLicenseFactory(transaction=sample_transaction) for _ in range(count)
    ]
    db_session.add_all(licenses)
    db_session.flush()
    return licenses


@pytest.fixture
def moderation_actions(
    db_session, sample_content, sample_creator, count: int = 10
) -> list[ModerationAction]:
    """Create multiple sample moderation actions.

    Args:
        sample_content: Content instance.
        sample_creator: Creator instance (used as moderator).
        count: Number of moderation actions to create.

    Returns:
        List of ModerationAction instances.
    """
    actions = [
        ModerationActionFactory(content=sample_content, moderator=sample_creator)
        for _ in range(count)
    ]
    db_session.add_all(actions)
    db_session.flush()
    return actions


@pytest.fixture
def quality_scores(db_session, sample_content, count: int = 10) -> list[QualityScore]:
    """Create multiple sample quality scores.

    Args:
        sample_content: Content instance.
        count: Number of quality scores to create.

    Returns:
        List of QualityScore instances.
    """
    scores = [QualityScoreFactory(content=sample_content) for _ in range(count)]
    db_session.add_all(scores)
    db_session.flush()
    return scores


@pytest.fixture
def fraud_reports(db_session, sample_creator, count: int = 10) -> list[FraudReport]:
    """Create multiple sample fraud reports.

    Args:
        sample_creator: Creator instance (used as reporter).
        count: Number of fraud reports to create.

    Returns:
        List of FraudReport instances.
    """
    reports = [FraudReportFactory(reporter=sample_creator) for _ in range(count)]
    db_session.add_all(reports)
    db_session.flush()
    return reports


@pytest.fixture
def analytics_events(
    db_session, sample_creator, count: int = 10
) -> list[AnalyticsEvent]:
    """Create multiple sample analytics events.

    Args:
        sample_creator: Creator instance.
        count: Number of analytics events to create.

    Returns:
        List of AnalyticsEvent instances.
    """
    events = [AnalyticsEventFactory(user=sample_creator) for _ in range(count)]
    db_session.add_all(events)
    db_session.flush()
    return events


@pytest.fixture
def audit_logs(db_session, sample_creator, count: int = 10) -> list[AuditLog]:
    """Create multiple sample audit log entries.

    Args:
        sample_creator: Creator instance.
        count: Number of audit log entries to create.

    Returns:
        List of AuditLog instances.
    """
    logs = [AuditLogFactory(changed_by=sample_creator) for _ in range(count)]
    db_session.add_all(logs)
    db_session.flush()
    return logs


# ---------------------------------------------------------------------------
# Seeded Database Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def seeded_db(db_session) -> dict[str, list[Any]]:
    """Seed the database with a complete set of test data.

    This fixture creates a full set of related test data using the
    seed_all function. It's useful for integration tests that need
    a populated database.

    Returns:
        Dictionary with lists of created instances by type.
    """
    return seed_all(
        db_session,
        num_creators=10,
        num_content_per_creator=3,
        num_listings_per_content=2,
        num_transactions_per_listing=2,
        num_licenses_per_transaction=1,
        num_moderation_actions=20,
        num_quality_scores_per_content=1,
        num_fraud_reports=10,
        num_analytics_events=100,
        num_audit_logs=50,
    )


@pytest_asyncio.fixture
async def async_seeded_db(async_db_session) -> dict[str, list[Any]]:
    """Async version of seeded_db fixture.

    This fixture creates a full set of related test data using the
    seed_all_async function. It's useful for async integration tests
    that need a populated database.

    Returns:
        Dictionary with lists of created instances by type.
    """
    return await seed_all_async(
        async_db_session,
        num_creators=10,
        num_content_per_creator=3,
        num_listings_per_content=2,
        num_transactions_per_listing=2,
        num_licenses_per_transaction=1,
        num_moderation_actions=20,
        num_quality_scores_per_content=1,
        num_fraud_reports=10,
        num_analytics_events=100,
        num_audit_logs=50,
    )


# ---------------------------------------------------------------------------
# Utility Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_transaction(db_session):
    """Provide a transaction context for tests that need explicit transaction control.

    Yields:
        SQLAlchemy Session with an active transaction.
    """
    yield db_session


@pytest.fixture
def faker():
    """Provide a faker instance for generating test data.

    Returns:
        Faker instance.
    """
    from faker import Faker

    return Faker()


@pytest.fixture
def uuid_str():
    """Generate a random UUID string.

    Returns:
        Random UUID as string.
    """
    return str(uuid4())


@pytest.fixture
def random_email(faker):
    """Generate a random email address.

    Returns:
        Random email address.
    """
    return faker.email()


@pytest.fixture
def random_username(faker):
    """Generate a random username.

    Returns:
        Random username.
    """
    return faker.user_name()


@pytest.fixture
def random_price():
    """Generate a random price.

    Returns:
        Random price as Decimal.
    """
    import random
    from decimal import Decimal

    return Decimal(str(round(random.uniform(0.99, 999.99), 2)))


@pytest.fixture
def random_score():
    """Generate a random quality score.

    Returns:
        Random score as Decimal between 0.0 and 1.0.
    """
    import random
    from decimal import Decimal

    return Decimal(str(round(random.uniform(0.0, 1.0), 3)))


# ---------------------------------------------------------------------------
# Pytest Configuration
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as a slow test")
    config.addinivalue_line("markers", "asyncio: mark test as an async test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
