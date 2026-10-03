# Gated Communities — Database Schema

Production-grade PostgreSQL 16+ schema for a gated community platform with membership tiers, content management, moderation, reputation tracking, and comprehensive audit trails.

## Table of Contents

- [Overview](#overview)
- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Tables](#tables)
  - [communities](#communities)
  - [tiers](#tiers)
  - [members](#members)
  - [content](#content)
  - [moderation_actions](#moderation_actions)
  - [reputation_scores](#reputation_scores)
  - [escalations](#escalations)
  - [compliance_reports](#compliance_reports)
  - [analytics_events](#analytics_events)
  - [audit_log](#audit_log)
- [Views](#views)
- [Functions & Triggers](#functions--triggers)
- [Getting Started](#getting-started)
- [Migrations](#migrations)

## Overview

This schema implements a multi-tenant gated community platform where:

- **Communities** are the top-level entity representing gated groups
- **Tiers** define membership levels with different pricing and benefits
- **Members** link users to communities with specific roles and statuses
- **Content** supports posts, comments, replies, polls, events, and media
- **Moderation Actions** track all moderation activities
- **Reputation Scores** maintain per-member reputation within each community
- **Escalations** handle reports requiring manual review
- **Compliance Reports** manage GDPR, DMCA, and other legal requests
- **Analytics Events** track user behavior (partitioned by month)
- **Audit Log** provides a complete audit trail of all changes

### Key Features

- **UUID Primary Keys** for all entities (using `pgcrypto` extension)
- **JSONB Columns** for flexible, schema-less data storage
- **Full-Text Search** on communities and content using PostgreSQL's built-in FTS
- **Table Partitioning** for analytics_events (monthly range partitions)
- **Audit Triggers** automatically log all INSERT/UPDATE/DELETE operations
- **Auto-updating Timestamps** via triggers
- **Comprehensive Indexing** including GIN indexes for JSONB columns
- **Foreign Key Constraints** with appropriate ON DELETE actions
- **Check Constraints** for data integrity
- **ENUM Types** for type safety and performance

## Entity Relationship Diagram

```
┌─────────────────┐
│   communities   │
├─────────────────┤
│ id (UUID, PK)   │
│ slug (UQ)       │
│ name            │
│ visibility      │
│ status          │
│ settings (JSONB)│
│ metadata (JSONB)│
│ search_vector   │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│     tiers       │     │    members      │
├─────────────────┤     ├─────────────────┤
│ id (UUID, PK)   │◄────│ tier_id (FK)    │
│ community_id(FK)│     │ id (UUID, PK)   │
│ slug            │     │ community_id(FK)│
│ name            │     │ user_id         │
│ price_cents     │     │ role            │
│ billing_period  │     │ status          │
│ benefits(JSONB) │     │ display_name    │
└─────────────────┘     │ notification_prefs│
                        │ metadata (JSONB)│
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         │ 1:N                   │ 1:N                   │ 1:N
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     content     │     │moderation_actions│     │reputation_scores│
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (UUID, PK)   │     │ id (UUID, PK)   │     │ id (UUID, PK)   │
│ community_id(FK)│     │ community_id(FK)│     │ community_id(FK)│
│ author_id (FK)  │     │ target_member(FK)│    │ member_id (FK)  │
│ parent_id (FK)  │◄────│ target_content  │     │ score           │
│ content_type    │     │ action_type     │     │ breakdown(JSONB)│
│ status          │     │ status          │     └─────────────────┘
│ title           │     │ reason          │
│ body            │     │ details (JSONB) │
│ tags (JSONB)    │     └─────────────────┘
│ search_vector   │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│  escalations    │     │compliance_reports│
├─────────────────┤     ├─────────────────┤
│ id (UUID, PK)   │     │ id (UUID, PK)   │
│ community_id(FK)│     │ community_id(FK)│
│ reporter_id(FK) │     │ reporter_id(FK) │
│ target_member   │     │ report_type     │
│ target_content  │     │ status          │
│ category        │     │ subject         │
│ priority        │     │ description     │
│ status          │     │ evidence_urls   │
│ metadata(JSONB) │     │ metadata(JSONB) │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ analytics_events│     │   audit_log     │
│ (Partitioned)   │     ├─────────────────┤
├─────────────────┤     │ id (BIGSERIAL)  │
│ id (UUID, PK)   │     │ table_name      │
│ community_id    │     │ record_id       │
│ user_id         │     │ action          │
│ event_type      │     │ old_data(JSONB) │
│ event_data(JSONB)│    │ new_data(JSONB) │
│ created_at (PK) │     │ changed_fields  │
└─────────────────┘     │ created_at      │
                        └─────────────────┘
```

## Tables

### communities

Core communities table — top-level entity for gated groups.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| description | TEXT | DEFAULT '' | Community description |
| avatar_url | TEXT | | Avatar image URL |
| banner_url | TEXT | | Banner image URL |
| visibility | community_visibility | DEFAULT 'private' | public, private, hidden |
| status | community_status | DEFAULT 'active' | active, archived, suspended, deleted |
| settings | JSONB | DEFAULT '{}' | Community-level settings |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| member_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| content_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| created_by | UUID | NOT NULL | Creator user ID |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |
| search_vector | TSVECTOR | GENERATED | Full-text search vector |

**Indexes:**
- `idx_communities_slug` on (slug)
- `idx_communities_visibility` on (visibility) WHERE deleted_at IS NULL
- `idx_communities_status` on (status) WHERE deleted_at IS NULL
- `idx_communities_created_by` on (created_by)
- `idx_communities_metadata_gin` GIN on (metadata jsonb_path_ops)
- `idx_communities_settings_gin` GIN on (settings jsonb_path_ops)
- `idx_communities_search` GIN on (search_vector)

### tiers

Membership tiers/pricing levels within a community.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| slug | VARCHAR(100) | NOT NULL | URL-friendly identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| description | TEXT | DEFAULT '' | Tier description |
| price_cents | INTEGER | DEFAULT 0, CHECK >= 0 | Price in cents |
| currency | VARCHAR(3) | DEFAULT 'USD' | ISO 4217 currency code |
| billing_period | tier_billing_period | DEFAULT 'monthly' | monthly, quarterly, yearly, lifetime |
| is_public | BOOLEAN | DEFAULT true | Visible to non-members |
| is_active | BOOLEAN | DEFAULT true | Accepting subscribers |
| sort_order | INTEGER | DEFAULT 0 | Display order |
| benefits | JSONB | DEFAULT '[]' | Array of benefits |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| subscriber_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |

**Indexes:**
- `idx_tiers_community_id` on (community_id) WHERE deleted_at IS NULL
- `idx_tiers_is_public` on (is_public) WHERE deleted_at IS NULL
- `idx_tiers_is_active` on (is_active) WHERE deleted_at IS NULL
- `idx_tiers_benefits_gin` GIN on (benefits jsonb_path_ops)

### members

Community membership records linking users to communities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| user_id | UUID | NOT NULL | User identifier |
| tier_id | UUID | FK → tiers, ON DELETE SET NULL | Membership tier |
| role | member_role | DEFAULT 'member' | owner, admin, moderator, member, guest |
| status | member_status | DEFAULT 'invited' | active, invited, banned, suspended, removed |
| display_name | VARCHAR(255) | | Display name in community |
| bio | TEXT | DEFAULT '' | Member bio |
| avatar_url | TEXT | | Avatar image URL |
| joined_at | TIMESTAMPTZ | | When member joined |
| invited_at | TIMESTAMPTZ | | When member was invited |
| banned_at | TIMESTAMPTZ | | When member was banned |
| banned_reason | TEXT | | Reason for ban |
| tier_expires_at | TIMESTAMPTZ | | Tier subscription expiry |
| last_active_at | TIMESTAMPTZ | | Last activity timestamp |
| notification_prefs | JSONB | DEFAULT '{}' | Notification preferences |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |

**Indexes:**
- `idx_members_community_id` on (community_id) WHERE deleted_at IS NULL
- `idx_members_user_id` on (user_id) WHERE deleted_at IS NULL
- `idx_members_tier_id` on (tier_id) WHERE deleted_at IS NULL
- `idx_members_role` on (role) WHERE deleted_at IS NULL
- `idx_members_status` on (status) WHERE deleted_at IS NULL
- `idx_members_last_active` on (last_active_at DESC) WHERE deleted_at IS NULL
- `idx_members_metadata_gin` GIN on (metadata jsonb_path_ops)
- `idx_members_notification_prefs_gin` GIN on (notification_prefs jsonb_path_ops)

### content

User-generated content (posts, comments, replies, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| author_id | UUID | FK → members, ON DELETE CASCADE | Content author |
| parent_id | UUID | FK → content, ON DELETE SET NULL | Parent content (for replies) |
| content_type | content_type | DEFAULT 'post' | post, comment, reply, poll, event, media |
| status | content_status | DEFAULT 'draft' | draft, published, edited, archived, deleted, flagged |
| title | VARCHAR(500) | | Content title |
| body | TEXT | DEFAULT '' | Content body |
| body_rendered | TEXT | DEFAULT '' | Rendered HTML body |
| media_urls | JSONB | DEFAULT '[]' | Array of media URLs |
| tags | JSONB | DEFAULT '[]' | Array of tags |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| like_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| comment_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| share_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| view_count | INTEGER | DEFAULT 0, CHECK >= 0 | Denormalized count |
| is_pinned | BOOLEAN | DEFAULT false | Pinned content |
| is_locked | BOOLEAN | DEFAULT false | Locked for comments |
| published_at | TIMESTAMPTZ | | Publication timestamp |
| edited_at | TIMESTAMPTZ | | Last edit timestamp |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |
| search_vector | TSVECTOR | GENERATED | Full-text search vector |

**Indexes:**
- `idx_content_community_id` on (community_id) WHERE deleted_at IS NULL
- `idx_content_author_id` on (author_id) WHERE deleted_at IS NULL
- `idx_content_parent_id` on (parent_id) WHERE deleted_at IS NULL
- `idx_content_type` on (content_type) WHERE deleted_at IS NULL
- `idx_content_status` on (status) WHERE deleted_at IS NULL
- `idx_content_published_at` on (published_at DESC) WHERE deleted_at IS NULL
- `idx_content_is_pinned` on (is_pinned, published_at DESC) WHERE deleted_at IS NULL AND is_pinned = true
- `idx_content_tags_gin` GIN on (tags jsonb_path_ops)
- `idx_content_metadata_gin` GIN on (metadata jsonb_path_ops)
- `idx_content_media_urls_gin` GIN on (media_urls jsonb_path_ops)
- `idx_content_search` GIN on (search_vector)

### moderation_actions

Moderation actions taken against members or content.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| target_member_id | UUID | FK → members, ON DELETE CASCADE | Target member |
| target_content_id | UUID | FK → content, ON DELETE SET NULL | Target content |
| action_type | moderation_action_type | NOT NULL | Type of action |
| status | moderation_action_status | DEFAULT 'pending' | pending, applied, reversed, expired |
| reason | TEXT | NOT NULL | Action reason |
| details | JSONB | DEFAULT '{}' | Additional details |
| duration_hours | INTEGER | CHECK > 0 | Action duration |
| expires_at | TIMESTAMPTZ | | Action expiry |
| applied_by | UUID | FK → members, ON DELETE CASCADE | Moderator who applied |
| applied_at | TIMESTAMPTZ | | When action was applied |
| reversed_by | UUID | FK → members, ON DELETE SET NULL | Who reversed |
| reversed_at | TIMESTAMPTZ | | When reversed |
| reversal_reason | TEXT | | Reason for reversal |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |

**Indexes:**
- `idx_moderation_community_id` on (community_id)
- `idx_moderation_target_member` on (target_member_id)
- `idx_moderation_target_content` on (target_content_id)
- `idx_moderation_action_type` on (action_type)
- `idx_moderation_status` on (status)
- `idx_moderation_applied_by` on (applied_by)
- `idx_moderation_expires_at` on (expires_at) WHERE expires_at IS NOT NULL
- `idx_moderation_details_gin` GIN on (details jsonb_path_ops)

### reputation_scores

Per-member reputation scores within each community.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| member_id | UUID | FK → members, ON DELETE CASCADE | Member |
| score | INTEGER | DEFAULT 0 | Current score |
| total_earned | INTEGER | DEFAULT 0, CHECK >= 0 | Total points earned |
| total_deducted | INTEGER | DEFAULT 0, CHECK >= 0 | Total points deducted |
| breakdown | JSONB | DEFAULT '{}' | Score breakdown by category |
| last_event_at | TIMESTAMPTZ | | Last reputation event |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |

**Indexes:**
- `idx_reputation_community_id` on (community_id)
- `idx_reputation_member_id` on (member_id)
- `idx_reputation_score` on (score DESC)
- `idx_reputation_breakdown_gin` GIN on (breakdown jsonb_path_ops)

### escalations

Escalated reports requiring manual review.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| reporter_id | UUID | FK → members, ON DELETE CASCADE | Reporting member |
| target_member_id | UUID | FK → members, ON DELETE SET NULL | Target member |
| target_content_id | UUID | FK → content, ON DELETE SET NULL | Target content |
| category | escalation_category | NOT NULL | harassment, spam, hate_speech, etc. |
| priority | escalation_priority | DEFAULT 'medium' | low, medium, high, critical |
| status | escalation_status | DEFAULT 'open' | open, investigating, resolved, dismissed, escalated |
| subject | VARCHAR(500) | NOT NULL | Report subject |
| description | TEXT | NOT NULL | Report description |
| resolution_notes | TEXT | | Resolution notes |
| assigned_to | UUID | FK → members, ON DELETE SET NULL | Assigned moderator |
| resolved_by | UUID | FK → members, ON DELETE SET NULL | Resolving moderator |
| resolved_at | TIMESTAMPTZ | | Resolution timestamp |
| due_at | TIMESTAMPTZ | | Resolution deadline |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |

**Indexes:**
- `idx_escalations_community_id` on (community_id) WHERE deleted_at IS NULL
- `idx_escalations_reporter` on (reporter_id) WHERE deleted_at IS NULL
- `idx_escalations_target_member` on (target_member_id) WHERE deleted_at IS NULL
- `idx_escalations_target_content` on (target_content_id) WHERE deleted_at IS NULL
- `idx_escalations_category` on (category) WHERE deleted_at IS NULL
- `idx_escalations_priority` on (priority) WHERE deleted_at IS NULL
- `idx_escalations_status` on (status) WHERE deleted_at IS NULL
- `idx_escalations_assigned_to` on (assigned_to) WHERE deleted_at IS NULL
- `idx_escalations_due_at` on (due_at) WHERE deleted_at IS NULL AND due_at IS NOT NULL
- `idx_escalations_metadata_gin` GIN on (metadata jsonb_path_ops)

### compliance_reports

Compliance and legal reports (GDPR, DMCA, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | FK → communities, ON DELETE CASCADE | Parent community |
| reporter_id | UUID | FK → members, ON DELETE SET NULL | Reporting member |
| report_type | compliance_report_type | NOT NULL | gdpr_access, gdpr_deletion, dmca, etc. |
| status | compliance_report_status | DEFAULT 'pending' | pending, in_review, fulfilled, rejected, appealed |
| subject | VARCHAR(500) | NOT NULL | Report subject |
| description | TEXT | NOT NULL | Report description |
| evidence_urls | JSONB | DEFAULT '[]' | Array of evidence URLs |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata |
| reviewed_by | UUID | FK → members, ON DELETE SET NULL | Reviewing moderator |
| reviewed_at | TIMESTAMPTZ | | Review timestamp |
| review_notes | TEXT | | Review notes |
| external_ref | VARCHAR(255) | | External reference number |
| created_at | TIMESTAMPTZ | DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | | Soft delete timestamp |

**Indexes:**
- `idx_compliance_community_id` on (community_id) WHERE deleted_at IS NULL
- `idx_compliance_reporter` on (reporter_id) WHERE deleted_at IS NULL
- `idx_compliance_report_type` on (report_type) WHERE deleted_at IS NULL
- `idx_compliance_status` on (status) WHERE deleted_at IS NULL
- `idx_compliance_reviewed_by` on (reviewed_by) WHERE deleted_at IS NULL
- `idx_compliance_external_ref` on (external_ref) WHERE external_ref IS NOT NULL
- `idx_compliance_evidence_gin` GIN on (evidence_urls jsonb_path_ops)
- `idx_compliance_metadata_gin` GIN on (metadata jsonb_path_ops)

### analytics_events

Partitioned analytics events for tracking user behavior.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK (composite), DEFAULT gen_random_uuid() | Primary key |
| community_id | UUID | NOT NULL | Community identifier |
| user_id | UUID | | User identifier |
| session_id | VARCHAR(255) | | Session identifier |
| event_type | analytics_event_type | NOT NULL | Type of event |
| event_data | JSONB | DEFAULT '{}' | Event-specific data |
| ip_address | INET | | Client IP address |
| user_agent | TEXT | | Client user agent |
| referrer_url | TEXT | | Referrer URL |
| page_url | TEXT | | Page URL |
| created_at | TIMESTAMPTZ | PK (composite), DEFAULT now() | Event timestamp |

**Partitioning:** Range partitioning on `created_at` (monthly)

**Indexes:**
- `idx_analytics_community_id` on (community_id)
- `idx_analytics_user_id` on (user_id)
- `idx_analytics_event_type` on (event_type)
- `idx_analytics_created_at` on (created_at DESC)
- `idx_analytics_session_id` on (session_id)
- `idx_analytics_event_data_gin` GIN on (event_data jsonb_path_ops)
- `idx_analytics_community_event` on (community_id, event_type, created_at DESC)

### audit_log

Audit trail for all changes to core tables.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PK, AUTO_INCREMENT | Primary key |
| table_name | VARCHAR(128) | NOT NULL | Affected table |
| record_id | UUID | NOT NULL | Affected record ID |
| action | audit_action | NOT NULL | INSERT, UPDATE, DELETE, etc. |
| old_data | JSONB | | Previous data |
| new_data | JSONB | | New data |
| changed_fields | JSONB | | Changed field names |
| performed_by | UUID | | User who performed action |
| performed_by_type | VARCHAR(50) | DEFAULT 'user' | user, system, etc. |
| ip_address | INET | | Client IP address |
| user_agent | TEXT | | Client user agent |
| session_id | VARCHAR(255) | | Session identifier |
| request_id | VARCHAR(255) | | Request identifier |
| created_at | TIMESTAMPTZ | DEFAULT now() | Audit timestamp |

**Indexes:**
- `idx_audit_table_name` on (table_name)
- `idx_audit_record_id` on (record_id)
- `idx_audit_action` on (action)
- `idx_audit_performed_by` on (performed_by)
- `idx_audit_created_at` on (created_at DESC)
- `idx_audit_table_record` on (table_name, record_id)
- `idx_audit_old_data_gin` GIN on (old_data jsonb_path_ops)
- `idx_audit_new_data_gin` GIN on (new_data jsonb_path_ops)

## Views

### v_community_summary

Aggregated community statistics including active members, tiers, and content counts.

### v_member_detail

Member details with community info, tier info, and reputation score.

### v_content_detail

Content details with community slug and author name.

## Functions & Triggers

### update_updated_at_column()

Automatically updates the `updated_at` timestamp on UPDATE operations.

**Applied to:** communities, tiers, members, content, moderation_actions, reputation_scores, escalations, compliance_reports

### audit_trigger_func()

Automatically logs INSERT, UPDATE, and DELETE operations to the audit_log table.

**Applied to:** communities, members, content, moderation_actions, escalations, compliance_reports

## Getting Started

### Prerequisites

- PostgreSQL 16+
- `pgcrypto` extension
- `uuid-ossp` extension
- `pg_trgm` extension
- `btree_gin` extension

### Quick Start

```bash
# Create database
createdb gated_communities

# Run schema
psql -d gated_communities -f schema.sql

# Run seed data (optional)
psql -d gated_communities -f seed.sql
```

### Using Migrations

```bash
# Install dependencies
pip install alembic psycopg2-binary

# Configure database URL
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/gated_communities"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations.

### Migration Files

- `migrations/versions/0001_initial_schema.py` — Initial schema creation

### Configuration

- `migrations/alembic.ini` — Alembic configuration
- `migrations/env.py` — Migration environment setup
- `migrations/script.py.mako` — Migration template

### Creating New Migrations

```bash
# Create a new migration
alembic revision -m "add new feature"

# Edit the generated file, then run
alembic upgrade head
```

## License

MIT
