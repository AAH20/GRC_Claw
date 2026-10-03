# UGC Marketplace Database Schema

Production-grade PostgreSQL 16+ database schema for a User-Generated Content marketplace platform.

## Overview

This schema supports a marketplace where creators can list digital content (3D models, 2D art, audio, video) for sale. It includes user management, content catalog, licensing, transactions, moderation, quality scoring, fraud detection, analytics, and comprehensive audit logging.

## Entity Relationship Diagram

```mermaid
erDiagram
    creators ||--o{ content : creates
    creators ||--o{ listings : owns
    creators ||--o{ transactions : buys
    creators ||--o{ transactions : sells
    creators ||--o{ licenses : licensee
    creators ||--o{ licenses : licensor
    creators ||--o{ moderation_actions : moderates
    creators ||--o{ fraud_reports : reports
    creators ||--o{ analytics_events : generates
    creators ||--o{ audit_log : changes

    content ||--o{ listings : listed_as
    content ||--o{ quality_scores : scored
    content ||--o{ moderation_actions : moderated
    content ||--o{ fraud_reports : reported
    content ||--o{ analytics_events : tracked
    content ||--o{ licenses : licensed

    listings ||--o{ transactions : purchased
    listings ||--o{ moderation_actions : moderated
    listings ||--o{ fraud_reports : reported
    listings ||--o{ analytics_events : tracked

    transactions ||--o{ licenses : grants

    creators {
        uuid id PK
        varchar username UK
        varchar email UK
        varchar display_name
        text bio
        text avatar_url
        text website_url
        jsonb social_links
        varchar verification_status
        numeric reputation_score
        numeric total_earnings
        int total_sales
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    content {
        uuid id PK
        uuid creator_id FK
        varchar title
        text description
        varchar content_type
        jsonb media_urls
        text[] tags
        jsonb metadata
        varchar status
        boolean is_nsfw
        int view_count
        int like_count
        tsvector search_vector
        timestamptz created_at
        timestamptz updated_at
    }

    listings {
        uuid id PK
        uuid content_id FK
        uuid creator_id FK
        varchar title
        text description
        numeric price
        varchar currency
        varchar license_type
        jsonb usage_rights
        boolean is_active
        int sales_count
        timestamptz created_at
        timestamptz updated_at
    }

    transactions {
        uuid id PK
        uuid listing_id FK
        uuid buyer_id FK
        uuid seller_id FK
        numeric amount
        varchar currency
        numeric platform_fee
        numeric seller_earnings
        varchar payment_method
        varchar payment_status
        varchar stripe_payment_intent_id
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    licenses {
        uuid id PK
        uuid transaction_id FK
        uuid licensee_id FK
        uuid licensor_id FK
        uuid content_id FK
        varchar license_type
        jsonb usage_scope
        timestamptz valid_from
        timestamptz valid_until
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    moderation_actions {
        uuid id PK
        uuid content_id FK
        uuid listing_id FK
        uuid moderator_id FK
        varchar action_type
        text reason
        jsonb details
        timestamptz created_at
    }

    quality_scores {
        uuid id PK
        uuid content_id FK
        numeric overall_score
        numeric technical_score
        numeric aesthetic_score
        numeric engagement_score
        numeric originality_score
        varchar scoring_model
        jsonb details
        timestamptz created_at
    }

    fraud_reports {
        uuid id PK
        uuid reporter_id FK
        uuid reported_content_id FK
        uuid reported_listing_id FK
        uuid reported_user_id FK
        varchar report_type
        text description
        jsonb evidence
        varchar status
        text resolution
        uuid resolved_by FK
        timestamptz resolved_at
        timestamptz created_at
        timestamptz updated_at
    }

    analytics_events {
        uuid id PK
        varchar event_type
        uuid user_id FK
        uuid content_id FK
        uuid listing_id FK
        uuid session_id
        inet ip_address
        text user_agent
        text referrer
        jsonb event_data
        timestamptz created_at
    }

    audit_log {
        uuid id PK
        varchar table_name
        uuid record_id
        varchar action
        jsonb old_values
        jsonb new_values
        uuid changed_by FK
        timestamptz changed_at
        inet ip_address
        text user_agent
    }
```

## Table Descriptions

### creators
User accounts for content creators and buyers. Tracks verification status, reputation, and earnings.

### content
UGC items (3D models, 2D art, audio, video). Includes full-text search vector, tags, and metadata.

### listings
Marketplace listings for content. Each listing defines pricing, license type, and usage rights.

### transactions
Purchase records with payment processing details, platform fees, and seller earnings.

### licenses
License grants from transactions. Defines usage scope, validity period, and active status.

### moderation_actions
Audit trail of moderation decisions on content and listings.

### quality_scores
AI/human quality assessments with multiple scoring dimensions.

### fraud_reports
User-submitted reports for copyright violations, fraud, spam, and impersonation.

### analytics_events
Partitioned event tracking for page views, searches, purchases, and user interactions.

### audit_log
Comprehensive audit trail for all changes to creators, content, listings, and transactions.

## Key Features

- **UUID Primary Keys**: All tables use UUID v4 for distributed system compatibility
- **JSONB Columns**: Flexible metadata storage for social links, usage rights, event data, etc.
- **Full-Text Search**: Generated TSVECTOR column on content with weighted fields
- **Table Partitioning**: analytics_events partitioned by quarter for performance
- **Audit Logging**: Automatic audit trail via database triggers
- **Auto-updating Timestamps**: `updated_at` columns maintained by triggers
- **Comprehensive Indexing**: B-tree, GIN, and partial indexes for query optimization
- **Foreign Key Constraints**: Proper referential integrity with CASCADE/SET NULL actions
- **Check Constraints**: Data validation at the database level

## Setup

### Quick Start

```bash
# Create database
createdb ugc_marketplace

# Run schema
psql -d ugc_marketplace -f schema.sql

# Run seed data
psql -d ugc_marketplace -f seed.sql
```

### Using Alembic Migrations

```bash
# Install dependencies
pip install alembic sqlalchemy psycopg2-binary

# Set database URL
export DATABASE_URL="postgresql://user:password@localhost:5432/ugc_marketplace"

# Run migrations
cd migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## File Structure

```
database/
├── schema.sql              # Complete database schema
├── seed.sql                # Sample data for development
├── README.md               # This file
└── migrations/
    ├── env.py              # Alembic environment config
    ├── script.py.mako      # Migration template
    └── versions/
        └── 0001_initial_schema.py  # Initial migration
```

## Views

- **v_creator_summary**: Creator statistics with content and listing counts
- **v_content_detail**: Content with creator info and quality scores
- **v_transaction_summary**: Transactions with listing and user details

## Partitioning Strategy

The `analytics_events` table uses PostgreSQL declarative partitioning by range on `created_at`:

- `analytics_events_2024_q4`: October 2024 - December 2024
- `analytics_events_2025_q1`: January 2025 - March 2025
- `analytics_events_2025_q2`: April 2025 - June 2025
- `analytics_events_default`: Catch-all for out-of-range dates

New partitions should be created before the current period ends:

```sql
CREATE TABLE analytics_events_2025_q3 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');
```

## Security Considerations

- All tables use UUID primary keys to prevent enumeration attacks
- Audit logging tracks all changes to sensitive tables
- Foreign key constraints prevent orphaned records
- Check constraints validate data at the database level
- JSONB columns allow flexible schemas without DDL changes
