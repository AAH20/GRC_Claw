# Recruitment Platform Database Schema

## Overview

PostgreSQL database schema for a full-featured recruitment platform. Supports job postings, candidate management, application tracking, interviews, assessments, skill matching, talent pooling, analytics, and comprehensive audit logging.

## Architecture Highlights

- **UUID Primary Keys** — All tables use `UUID` v4 primary keys for distributed-system safety
- **JSONB Flexible Data** — Locations, preferences, settings, and metadata stored as JSONB
- **Full-Text Search** — `tsvector` columns with GIN indexes on employers, recruiters, candidates, and jobs
- **Partitioned Analytics** — `analytics_events` uses monthly RANGE partitioning on `created_at`
- **Soft Deletes** — `deleted_at` columns with partial indexes on active records
- **Audit Trail** — Automatic audit logging via database triggers
- **Enum Types** — Strongly-typed status and type fields
- **Materialized Views** — Pre-computed views for active jobs, pipelines, and candidate summaries

## Entity-Relationship Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    employers     │     │   recruiters     │     │   candidates     │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK, UUID)    │◄────│ employer_id (FK) │     │ id (PK, UUID)    │
│ name             │     │ id (PK, UUID)    │     │ email            │
│ slug (unique)    │     │ email            │     │ first_name       │
│ industry         │     │ first_name       │     │ last_name        │
│ company_size     │     │ last_name        │     │ current_title    │
│ headquarters     │     │ title            │     │ current_company  │
│ logo_url         │     │ department       │     │ current_location │
│ is_verified      │     │ is_admin         │     │ address (JSONB)  │
│ is_active        │     │ is_active        │     │ social_profiles  │
│ search_vector    │     │ search_vector    │     │ resume_url       │
│ created_at       │     │ created_at       │     │ resume_text      │
│ updated_at       │     │ updated_at       │     │ preferred_salary │
│ deleted_at       │     │ deleted_at       │     │ languages        │
└───────┬──────────┘     └───────┬──────────┘     │ certifications   │
        │                        │                │ is_active        │
        │                        │                │ search_vector    │
        │    ┌───────────────────┘                │ created_at       │
        │    │                                    │ updated_at       │
        │    │                                    │ deleted_at       │
        │    │                                    └───────┬──────────┘
        │    │                                            │
        │    │    ┌──────────────────┐                    │
        │    │    │      jobs        │                    │
        │    │    ├──────────────────┤                    │
        └────┼───►│ id (PK, UUID)    │◄───────────────────┤
             │    │ employer_id (FK) │                    │
             │    │ posted_by (FK)   │                    │
             │    │ title            │                    │
             │    │ slug (unique)    │                    │
             │    │ description      │                    │
             │    │ requirements     │                    │
             │    │ employment_type  │                    │
             │    │ location_type    │                    │
             │    │ location (JSONB) │                    │
             │    │ salary_range     │                    │
             │    │ skills_required  │                    │
             │    │ is_remote        │                    │
             │    │ is_featured      │                    │
             │    │ is_active        │                    │
             │    │ search_vector    │                    │
             │    │ created_at       │                    │
             │    │ updated_at       │                    │
             │    │ deleted_at       │                    │
             │    └───────┬──────────┘                    │
             │            │                               │
             │            │    ┌──────────────────┐       │
             │            │    │  applications    │       │
             │            │    ├──────────────────┤       │
             │            └───►│ id (PK, UUID)    │       │
             │                 │ candidate_id (FK)│◄──────┘
             │                 │ job_id (FK)      │
             └────────────────►│ recruiter_id (FK) │
                               │ status           │
                               │ status_history   │
                               │ cover_letter     │
                               │ custom_answers   │
                               │ source           │
                               │ rating           │
                               │ offer_details    │
                               │ applied_at       │
                               │ created_at       │
                               │ updated_at       │
                               │ deleted_at       │
                               └───────┬──────────┘
                                       │
             ┌─────────────────────────┼─────────────────────────┐
             │                         │                         │
             │    ┌──────────────────┐ │ ┌──────────────────┐    │
             │    │   interviews     │ │ │  assessments     │    │
             │    ├──────────────────┤ │ ├──────────────────┤    │
             │    │ id (PK, UUID)    │ │ │ id (PK, UUID)    │    │
             │    │ application_id   │◄┘ │ application_id   │◄───┘
             │    │ interviewer_id   │   │ assessment_type  │
             │    │ interview_type   │   │ status           │
             │    │ status           │   │ title            │
             │    │ scheduled_at     │   │ questions        │
             │    │ duration_minutes │   │ candidate_answers│
             │    │ meeting_url      │   │ score            │
             │    │ feedback         │   │ evaluator_id     │
             │    │ overall_rating   │   │ due_at           │
             │    │ created_at       │   │ created_at       │
             │    │ updated_at       │   │ updated_at       │
             │    │ deleted_at       │   │ deleted_at       │
             │    └──────────────────┘   └──────────────────┘
             │
             │    ┌──────────────────┐     ┌──────────────────┐
             │    │  talent_pools    │     │  talent_pool_    │
             │    ├──────────────────┤     │    members       │
             │    │ id (PK, UUID)    │◄────├──────────────────┤
             │    │ employer_id (FK) │     │ id (PK, UUID)    │
             │    │ created_by (FK)  │     │ talent_pool_id   │
             │    │ name             │     │ candidate_id     │
             │    │ pool_type        │     │ added_by         │
             │    │ criteria         │     │ created_at       │
             │    │ is_active        │     └──────────────────┘
             │    │ created_at       │
             │    │ updated_at       │     ┌──────────────────┐
             │    │ deleted_at       │     │ candidate_skills │
             │    └──────────────────┘     ├──────────────────┤
             │                            │ id (PK, UUID)    │
             │    ┌──────────────────┐     │ candidate_id     │
             │    │     skills       │◄────│ skill_id         │
             │    ├──────────────────┤     │ proficiency_level│
             │    │ id (PK, UUID)    │     │ years_experience │
             │    │ name (unique)    │     │ is_primary       │
             │    │ slug (unique)    │     │ created_at       │
             │    │ category         │     │ updated_at       │
             │    │ subcategory      │     └──────────────────┘
             │    │ aliases          │
             │    │ is_active        │     ┌──────────────────┐
             │    │ created_at       │     │   experiences    │
             │    │ updated_at       │     ├──────────────────┤
             │    └──────────────────┘     │ id (PK, UUID)    │
             │                            │ candidate_id     │
             │    ┌──────────────────┐     │ company_name     │
             │    │    education     │     │ title            │
             │    ├──────────────────┤     │ employment_type  │
             │    │ id (PK, UUID)    │     │ start_date       │
             │    │ candidate_id     │     │ end_date         │
             │    │ institution_name │     │ is_current       │
             │    │ degree           │     │ description      │
             │    │ field_of_study   │     │ skills_used      │
             │    │ education_level  │     │ created_at       │
             │    │ gpa              │     │ updated_at       │
             │    │ created_at       │     │ deleted_at       │
             │    │ updated_at       │     └──────────────────┘
             │    │ deleted_at       │
             │    └──────────────────┘
             │
             │    ┌──────────────────┐     ┌──────────────────┐
             │    │ analytics_events │     │    audit_log     │
             │    │ (PARTITIONED)    │     ├──────────────────┤
             │    ├──────────────────┤     │ id (PK, UUID)    │
             │    │ id (PK, UUID)    │     │ table_name       │
             │    │ event_type       │     │ record_id        │
             │    │ event_name       │     │ action           │
             │    │ session_id       │     │ old_values       │
             │    │ candidate_id     │     │ new_values       │
             │    │ job_id           │     │ changed_fields   │
             │    │ application_id   │     │ performed_by     │
             │    │ interview_id     │     │ created_at       │
             │    │ assessment_id    │     └──────────────────┘
             │    │ recruiter_id     │
             │    │ ip_address       │
             │    │ user_agent       │
             │    │ metadata (JSONB) │
             │    │ properties (JSONB)│
             │    │ created_at       │
             │    └──────────────────┘
```

## Table Descriptions

### Core Tables

| Table | Description | Key Features |
|-------|-------------|--------------|
| `employers` | Companies posting jobs | JSONB headquarters, social links, settings; full-text search |
| `recruiters` | Recruiting users | FK to employers; admin flag; specialties JSONB |
| `candidates` | Job seekers | Rich profile with resume text, social links, languages, certifications |
| `jobs` | Job postings | JSONB salary_range, benefits, skills; location_type; featured/urgent flags |
| `applications` | Job applications | Status history JSONB; offer details; unique candidate+job constraint |
| `interviews` | Interview sessions | Self-referencing for rescheduling; feedback JSONB; ratings |
| `assessments` | Tests & evaluations | JSONB questions/answers; scoring with details |
| `skills` | Master skill list | Aliases JSONB; category/subcategory hierarchy |
| `experiences` | Work history | JSONB achievements and skills_used |
| `education` | Education history | GPA validation; coursework JSONB |
| `talent_pools` | Curated candidate groups | JSONB criteria for smart pools |
| `talent_pool_members` | Pool membership | Unique pool+candidate constraint |
| `candidate_skills` | Skill proficiency | 1-5 proficiency scale; verification tracking |
| `analytics_events` | Event tracking | Monthly RANGE partitioning; JSONB metadata/properties |
| `audit_log` | Change tracking | Old/new values; changed fields; performer tracking |

## Indexing Strategy

### B-Tree Indexes
- Primary keys (UUID)
- Foreign keys for join performance
- Status fields for filtering
- Date ranges for sorting and range queries
- Unique constraints (email, slug, candidate+job)

### GIN Indexes
- JSONB columns: `location`, `salary_range`, `preferences`, `metadata`, `properties`
- Array columns: `languages`, `certifications`, `skills_required`, `skills_preferred`
- Full-text search: `search_vector` columns
- Trigram: name fields for fuzzy matching

### Partial Indexes
- `is_active = TRUE` on all major tables
- `is_current = TRUE` on experiences and education
- `is_remote = TRUE` on jobs
- `is_featured = TRUE` on jobs

## Partitioning

### analytics_events
- **Strategy**: RANGE partitioning on `created_at`
- **Granularity**: Monthly partitions
- **Coverage**: 2026-01 through 2027-12 (24 partitions)
- **Default**: Catch-all partition for out-of-range dates
- **Automation**: Use `pg_partman` or cron-based scripts for ongoing partition management

## Views

| View | Purpose |
|------|---------|
| `v_active_jobs` | Published, non-expired jobs with employer details |
| `v_candidate_applications` | Applications with candidate and job denormalized |
| `v_recruiter_pipeline` | Aggregated pipeline metrics per recruiter |

## Setup Instructions

### 1. Create Database
```bash
createdb recruitment_platform
```

### 2. Run Schema
```bash
psql -d recruitment_platform -f schema.sql
```

### 3. Run Migrations (optional, for Alembic)
```bash
cd migrations
alembic upgrade head
```

### 4. Seed Data (optional, for development)
```bash
psql -d recruitment_platform -f seed.sql
```

### 5. Verify
```bash
psql -d recruitment_platform -c "\dt"
psql -d recruitment_platform -c "\d+ jobs"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/recruitment_platform` | Full connection string |

## Migration Workflow

```bash
# Generate new migration
alembic revision --autogenerate -m "add new feature"

# Review generated migration in migrations/versions/

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history --verbose
```

## Backup & Restore

See `backup/` directory for disaster recovery scripts and procedures.

## Performance Considerations

1. **Connection Pooling**: Use PgBouncer for high-traffic deployments
2. **Partition Maintenance**: Automate monthly partition creation
3. **Index Maintenance**: Regular `REINDEX` and `ANALYZE` during low-traffic periods
4. **Query Optimization**: Use `EXPLAIN ANALYZE` for slow queries; consider materialized views for complex aggregations
5. **Archiving**: Move old analytics events to cold storage; drop old partitions

## Security Notes

- Passwords stored as bcrypt hashes (application-level)
- Audit log tracks all data changes
- Soft deletes preserve data integrity
- Row-Level Security (RLS) can be enabled per-table (see commented DDL in schema.sql)
- Use prepared statements to prevent SQL injection
- Restrict database user permissions following principle of least privilege
