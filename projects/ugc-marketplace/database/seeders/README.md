# UGC Marketplace Database Seeders

This directory contains database seeders and factories for generating realistic test data for the UGC Marketplace platform. It includes factory_boy factories, seeder scripts, pytest fixtures, and comprehensive documentation.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Synchronous Seeding](#synchronous-seeding)
  - [Asynchronous Seeding](#asynchronous-seeding)
  - [CLI Usage](#cli-usage)
- [Factories](#factories)
  - [Base Factories](#base-factories)
  - [Specialized Factories](#specialized-factories)
- [Pytest Fixtures](#pytest-fixtures)
- [Configuration](#configuration)
- [Testing](#testing)
- [API Reference](#api-reference)

## Overview

The seeders module provides:

1. **SQLAlchemy ORM Models** (`models.py`) - Complete ORM models mirroring the production schema
2. **factory_boy Factories** (`factories.py`) - 22 factory classes for generating realistic test data
3. **Seeder Scripts** (`seeders.py`) - Synchronous and asynchronous functions for bulk data generation
4. **Pytest Fixtures** (`conftest.py`) - 40+ fixtures for database testing

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Dependencies from `pyproject.toml`

### Install Dependencies

```bash
# Install the project with dev dependencies
pip install -e ".[dev]"

# Or install required packages directly
pip install factory_boy faker sqlalchemy[asyncio] asyncpg pytest pytest-asyncio
```

### Database Setup

```bash
# Create the test database
createdb ugc_marketplace_test

# Or using psql
psql -U postgres -c "CREATE DATABASE ugc_marketplace_test;"
```

## Quick Start

### Basic Seeding

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ugc_marketplace.database.seeders.models import Base
from ugc_marketplace.database.seeders.seeders import seed_all

# Create engine and session
engine = create_engine("postgresql://postgres:postgres@localhost:5432/ugc_marketplace")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Seed the database
results = seed_all(session, num_creators=50, num_content_per_creator=5)

# Access created data
creators = results["creators"]
content_items = results["content"]
listings = results["listings"]
```

### Async Seeding

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ugc_marketplace.database.seeders.models import Base
from ugc_marketplace.database.seeders.seeders import seed_all_async

# Create async engine and session
engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace")
async_session = async_sessionmaker(engine, expire_on_commit=False)

async with async_session() as session:
    results = await seed_all_async(session, num_creators=50)
```

## Usage

### Synchronous Seeding

```python
from ugc_marketplace.database.seeders.seeders import (
    seed_creators,
    seed_content,
    seed_listings,
    seed_transactions,
    seed_licenses,
    seed_moderation_actions,
    seed_quality_scores,
    seed_fraud_reports,
    seed_analytics_events,
    seed_audit_logs,
)

# Seed individual entity types
creators = seed_creators(session, count=100, verified_ratio=0.7)
content_items = seed_content(session, creators, per_creator=5)
listings = seed_listings(session, content_items, per_content=2)
transactions = seed_transactions(session, listings, buyers=creators, per_listing=3)
licenses = seed_licenses(session, transactions, per_transaction=1)
```

### Asynchronous Seeding

```python
from ugc_marketplace.database.seeders.seeders import (
    seed_creators_async,
    seed_content_async,
    seed_listings_async,
    seed_transactions_async,
    seed_licenses_async,
)

# Seed individual entity types asynchronously
creators = await seed_creators_async(session, count=100)
content_items = await seed_content_async(session, creators, per_creator=5)
listings = await seed_listings_async(session, content_items, per_content=2)
transactions = await seed_transactions_async(session, listings, buyers=creators, per_listing=3)
licenses = await seed_licenses_async(session, transactions, per_transaction=1)
```

### CLI Usage

```bash
# Seed with default settings
python -m ugc_marketplace.database.seeders.seeders

# Seed with custom parameters
python -m ugc_marketplace.database.seeders.seeders \
    --database-url "postgresql://user:pass@localhost:5432/mydb" \
    --creators 100 \
    --content-per-creator 10 \
    --listings-per-content 3 \
    --transactions-per-listing 5 \
    --analytics-events 5000

# Drop and recreate all tables before seeding
python -m ugc_marketplace.database.seeders.seeders --drop-all
```

## Factories

### Base Factories

| Factory | Model | Description |
|---------|-------|-------------|
| `CreatorFactory` | `Creator` | Creates users with random verification status |
| `ContentFactory` | `Content` | Creates content items with random status |
| `ListingFactory` | `Listing` | Creates marketplace listings |
| `TransactionFactory` | `Transaction` | Creates payment transactions |
| `LicenseFactory` | `License` | Creates usage licenses |
| `ModerationActionFactory` | `ModerationAction` | Creates moderation records |
| `QualityScoreFactory` | `QualityScore` | Creates quality assessments |
| `FraudReportFactory` | `FraudReport` | Creates fraud reports |
| `AnalyticsEventFactory` | `AnalyticsEvent` | Creates analytics events |
| `AuditLogFactory` | `AuditLog` | Creates audit log entries |

### Specialized Factories

| Factory | Parent | Description |
|---------|--------|-------------|
| `VerifiedCreatorFactory` | `CreatorFactory` | Creates verified creators with high reputation |
| `SuspendedCreatorFactory` | `CreatorFactory` | Creates suspended creators |
| `PublishedContentFactory` | `ContentFactory` | Creates published content with views/likes |
| `DraftContentFactory` | `ContentFactory` | Creates draft content |
| `ActiveListingFactory` | `ListingFactory` | Creates active listings |
| `CompletedTransactionFactory` | `TransactionFactory` | Creates completed transactions |
| `PendingTransactionFactory` | `TransactionFactory` | Creates pending transactions |
| `RefundedTransactionFactory` | `TransactionFactory` | Creates refunded transactions |
| `CommercialLicenseFactory` | `LicenseFactory` | Creates commercial licenses |
| `PersonalLicenseFactory` | `LicenseFactory` | Creates personal licenses |
| `ResolvedFraudReportFactory` | `FraudReportFactory` | Creates resolved fraud reports |
| `OpenFraudReportFactory` | `FraudReportFactory` | Creates open fraud reports |

### Factory Usage Examples

```python
from ugc_marketplace.database.seeders.factories import (
    CreatorFactory,
    PublishedContentFactory,
    ActiveListingFactory,
    CompletedTransactionFactory,
)

# Create a single creator
creator = CreatorFactory()

# Create a verified creator
verified_creator = VerifiedCreatorFactory()

# Create content for a specific creator
content = PublishedContentFactory(creator=creator)

# Create a listing for specific content
listing = ActiveListingFactory(content=content, creator=creator)

# Create a completed transaction
transaction = CompletedTransactionFactory(
    listing=listing,
    buyer=another_creator,
    seller=creator,
)

# Create multiple creators
creators = CreatorFactory.create_batch(10)

# Create with custom attributes
creator = CreatorFactory(
    username="custom_user",
    email="custom@example.com",
    verification_status=VerificationStatus.VERIFIED,
)
```

## Pytest Fixtures

### Session Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_engine` | session | Synchronous database engine |
| `db_session` | function | Synchronous database session with rollback |
| `async_db_engine` | session | Asynchronous database engine |
| `async_db_session` | function | Asynchronous database session with rollback |

### Factory Fixtures

All factories are available as fixtures:

```python
def test_creator_creation(creator_factory):
    creator = creator_factory()
    assert creator.id is not None
    assert creator.username
    assert creator.email

def test_verified_creator(verified_creator_factory):
    creator = verified_creator_factory()
    assert creator.verification_status == VerificationStatus.VERIFIED
    assert creator.reputation_score >= 70
```

### Data Fixtures

| Fixture | Description |
|---------|-------------|
| `sample_creator` | Single creator instance |
| `sample_verified_creator` | Single verified creator |
| `sample_suspended_creator` | Single suspended creator |
| `sample_content` | Single published content item |
| `sample_listing` | Single active listing |
| `sample_transaction` | Single completed transaction |
| `sample_license` | Single commercial license |
| `sample_quality_score` | Single quality score |
| `sample_moderation_action` | Single moderation action |
| `sample_fraud_report` | Single fraud report |
| `sample_analytics_event` | Single analytics event |
| `sample_audit_log` | Single audit log entry |

### Bulk Data Fixtures

| Fixture | Default Count | Description |
|---------|---------------|-------------|
| `creators` | 10 | Multiple creators |
| `content_items` | 10 | Multiple content items |
| `listings` | 10 | Multiple listings |
| `transactions` | 10 | Multiple transactions |
| `licenses` | 10 | Multiple licenses |
| `moderation_actions` | 10 | Multiple moderation actions |
| `quality_scores` | 10 | Multiple quality scores |
| `fraud_reports` | 10 | Multiple fraud reports |
| `analytics_events` | 10 | Multiple analytics events |
| `audit_logs` | 10 | Multiple audit log entries |

### Seeded Database Fixtures

```python
def test_with_seeded_db(seeded_db):
    creators = seeded_db["creators"]
    content_items = seeded_db["content"]
    assert len(creators) == 10
    assert len(content_items) == 30

async def test_with_async_seeded_db(async_seeded_db):
    creators = async_seeded_db["creators"]
    assert len(creators) == 10
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace_test` | Async test database URL |
| `TEST_DATABASE_URL_SYNC` | `postgresql://postgres:postgres@localhost:5432/ugc_marketplace_test` | Sync test database URL |

### Custom Configuration

```python
# Override database URLs in your conftest.py
import ugc_marketplace.database.seeders.conftest as conftest

conftest.TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/db"
conftest.TEST_DATABASE_URL_SYNC = "postgresql://user:pass@host:5432/db"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ugc_marketplace.database.seeders

# Run specific test file
pytest tests/test_seeders.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest -m integration

# Run slow tests only
pytest -m slow
```

### Test Configuration

Add to your `pyproject.toml` or `pytest.ini`:

```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
```

## API Reference

### Seeder Functions

#### `seed_all(session, **kwargs) -> dict[str, list[Any]]`

Seed the database with all test data synchronously.

**Parameters:**
- `session` (Session): SQLAlchemy session
- `num_creators` (int): Number of creators to create (default: 50)
- `num_content_per_creator` (int): Content items per creator (default: 5)
- `num_listings_per_content` (int): Listings per content item (default: 2)
- `num_transactions_per_listing` (int): Transactions per listing (default: 3)
- `num_licenses_per_transaction` (int): Licenses per transaction (default: 1)
- `num_moderation_actions` (int): Moderation actions to create (default: 100)
- `num_quality_scores_per_content` (int): Quality scores per content (default: 1)
- `num_fraud_reports` (int): Fraud reports to create (default: 50)
- `num_analytics_events` (int): Analytics events to create (default: 1000)
- `num_audit_logs` (int): Audit log entries to create (default: 200)

**Returns:**
Dictionary with lists of created instances by type.

#### `seed_all_async(session, **kwargs) -> dict[str, list[Any]]`

Async version of `seed_all`.

### Individual Seeder Functions

All seeder functions follow the pattern `seed_<entity>[_async](session, ..., **kwargs) -> list[Model]`:

- `seed_creators(session, count, ...)`
- `seed_content(session, creators, ...)`
- `seed_listings(session, content_items, ...)`
- `seed_transactions(session, listings, buyers, ...)`
- `seed_licenses(session, transactions, ...)`
- `seed_moderation_actions(session, content_items, listings, moderators, ...)`
- `seed_quality_scores(session, content_items, ...)`
- `seed_fraud_reports(session, creators, content_items, listings, ...)`
- `seed_analytics_events(session, creators, content_items, listings, ...)`
- `seed_audit_logs(session, creators, ...)`

## License

MIT License - See project root for details.
