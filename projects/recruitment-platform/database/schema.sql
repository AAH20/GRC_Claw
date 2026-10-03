-- ============================================================================
-- Recruitment Platform Database Schema
-- PostgreSQL 16+
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE application_status AS ENUM (
    'draft', 'submitted', 'screening', 'interview', 'assessment',
    'offer', 'hired', 'rejected', 'withdrawn'
);

CREATE TYPE interview_status AS ENUM (
    'scheduled', 'confirmed', 'in_progress', 'completed',
    'cancelled', 'no_show', 'rescheduled'
);

CREATE TYPE interview_type AS ENUM (
    'phone_screen', 'video', 'onsite', 'technical', 'behavioral', 'panel'
);

CREATE TYPE assessment_status AS ENUM (
    'pending', 'in_progress', 'submitted', 'evaluated', 'expired'
);

CREATE TYPE assessment_type AS ENUM (
    'coding', 'personality', 'cognitive', 'technical_quiz', 'case_study', 'take_home'
);

CREATE TYPE talent_pool_type AS ENUM (
    'active', 'passive', 'alumni', 'referred', 'custom'
);

CREATE TYPE employment_type AS ENUM (
    'full_time', 'part_time', 'contract', 'internship', 'freelance'
);

CREATE TYPE experience_type AS ENUM (
    'full_time', 'part_time', 'contract', 'internship', 'freelance', 'volunteer'
);

CREATE TYPE education_level AS ENUM (
    'high_school', 'associate', 'bachelor', 'master', 'doctorate', 'postdoc', 'certificate', 'bootcamp'
);

CREATE TYPE event_type AS ENUM (
    'page_view', 'job_view', 'job_apply_start', 'job_apply_complete',
    'candidate_signup', 'candidate_login', 'search_query', 'filter_applied',
    'email_open', 'email_click', 'interview_scheduled', 'interview_completed',
    'assessment_started', 'assessment_completed', 'offer_extended', 'offer_accepted', 'offer_declined'
);

CREATE TYPE audit_action AS ENUM (
    'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'LOGIN', 'LOGOUT', 'EXPORT'
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- ---------------------------------------------------------------------------
-- employers
-- ---------------------------------------------------------------------------
CREATE TABLE employers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(255) NOT NULL UNIQUE,
    description         TEXT,
    website             VARCHAR(500),
    industry            VARCHAR(100),
    company_size        VARCHAR(50),
    founded_year        INTEGER,
    logo_url            VARCHAR(1000),
    headquarters        JSONB DEFAULT '{}',
    social_links        JSONB DEFAULT '{}',
    settings            JSONB DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    search_vector       TSVECTOR
);

CREATE INDEX idx_employers_name ON employers USING GIN (name gin_trgm_ops);
CREATE INDEX idx_employers_slug ON employers (slug);
CREATE INDEX idx_employers_industry ON employers (industry);
CREATE INDEX idx_employers_is_active ON employers (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_employers_search ON employers USING GIN (search_vector);
CREATE INDEX idx_employers_headquarters ON employers USING GIN (headquarters);
CREATE INDEX idx_employers_social_links ON employers USING GIN (social_links);
CREATE INDEX idx_employers_settings ON employers USING GIN (settings);

-- ---------------------------------------------------------------------------
-- recruiters
-- ---------------------------------------------------------------------------
CREATE TABLE recruiters (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employer_id         UUID NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
    user_id             UUID,
    email               VARCHAR(255) NOT NULL UNIQUE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    title               VARCHAR(150),
    department          VARCHAR(100),
    phone               VARCHAR(50),
    avatar_url          VARCHAR(1000),
    bio                 TEXT,
    specialties         JSONB DEFAULT '[]',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin            BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    search_vector       TSVECTOR
);

CREATE INDEX idx_recruiters_employer_id ON recruiters (employer_id);
CREATE INDEX idx_recruiters_email ON recruiters (email);
CREATE INDEX idx_recruiters_user_id ON recruiters (user_id);
CREATE INDEX idx_recruiters_name ON recruiters USING GIN ((first_name || ' ' || last_name) gin_trgm_ops);
CREATE INDEX idx_recruiters_is_active ON recruiters (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_recruiters_search ON recruiters USING GIN (search_vector);
CREATE INDEX idx_recruiters_specialties ON recruiters USING GIN (specialties);

-- ---------------------------------------------------------------------------
-- candidates
-- ---------------------------------------------------------------------------
CREATE TABLE candidates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    phone               VARCHAR(50),
    date_of_birth       DATE,
    gender              VARCHAR(50),
    nationality         VARCHAR(100),
    current_title       VARCHAR(200),
    current_company     VARCHAR(200),
    current_location    VARCHAR(200),
    address             JSONB DEFAULT '{}',
    social_profiles     JSONB DEFAULT '{}',
    resume_url          VARCHAR(1000),
    resume_text         TEXT,
    cover_letter        TEXT,
    portfolio_url       VARCHAR(1000),
    linkedin_url        VARCHAR(1000),
    github_url          VARCHAR(1000),
    website_url         VARCHAR(1000),
    preferred_location  VARCHAR(200),
    preferred_salary    JSONB DEFAULT '{}',
    notice_period_days  INTEGER,
    years_experience    NUMERIC(4,1),
    summary             TEXT,
    languages           JSONB '[]',
    certifications      JSONB '[]',
    preferences         JSONB DEFAULT '{}',
    source              VARCHAR(100),
    referral_code       VARCHAR(100),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_anonymous        BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    profile_completeness INTEGER DEFAULT 0,
    last_active_at      TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    search_vector       TSVECTOR
);

CREATE INDEX idx_candidates_email ON candidates (email);
CREATE INDEX idx_candidates_name ON candidates USING GIN ((first_name || ' ' || last_name) gin_trgm_ops);
CREATE INDEX idx_candidates_current_title ON candidates USING GIN (current_title gin_trgm_ops);
CREATE INDEX idx_candidates_current_company ON candidates USING GIN (current_company gin_trgm_ops);
CREATE INDEX idx_candidates_current_location ON candidates USING GIN (current_location gin_trgm_ops);
CREATE INDEX idx_candidates_is_active ON candidates (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_candidates_source ON candidates (source);
CREATE INDEX idx_candidates_created_at ON candidates (created_at DESC);
CREATE INDEX idx_candidates_last_active_at ON candidates (last_active_at DESC);
CREATE INDEX idx_candidates_search ON candidates USING GIN (search_vector);
CREATE INDEX idx_candidates_address ON candidates USING GIN (address);
CREATE INDEX idx_candidates_social_profiles ON candidates USING GIN (social_profiles);
CREATE INDEX idx_candidates_preferred_salary ON candidates USING GIN (preferred_salary);
CREATE INDEX idx_candidates_languages ON candidates USING GIN (languages);
CREATE INDEX idx_candidates_certifications ON candidates USING GIN (certifications);
CREATE INDEX idx_candidates_preferences ON candidates USING GIN (preferences);
CREATE INDEX idx_candidates_years_experience ON candidates (years_experience);

-- ---------------------------------------------------------------------------
-- jobs
-- ---------------------------------------------------------------------------
CREATE TABLE jobs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employer_id         UUID NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
    posted_by           UUID NOT NULL REFERENCES recruiters(id) ON DELETE RESTRICT,
    title               VARCHAR(300) NOT NULL,
    slug                VARCHAR(350) NOT NULL UNIQUE,
    description         TEXT NOT NULL,
    responsibilities    TEXT,
    requirements        TEXT,
    nice_to_have        TEXT,
    employment_type     employment_type NOT NULL DEFAULT 'full_time',
    experience_level    VARCHAR(50),
    department          VARCHAR(100),
    location_type       VARCHAR(50) NOT NULL DEFAULT 'onsite',
    location            JSONB DEFAULT '{}',
    salary_range        JSONB DEFAULT '{}',
    benefits            JSONB DEFAULT '[]',
    skills_required     JSONB DEFAULT '[]',
    skills_preferred    JSONB DEFAULT '[]',
    application_url     VARCHAR(1000),
    application_email   VARCHAR(255),
    openings            INTEGER NOT NULL DEFAULT 1,
    is_remote           BOOLEAN NOT NULL DEFAULT FALSE,
    is_featured         BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_urgent           BOOLEAN NOT NULL DEFAULT FALSE,
    views_count         INTEGER NOT NULL DEFAULT 0,
    applications_count  INTEGER NOT NULL DEFAULT 0,
    published_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    closed_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    search_vector       TSVECTOR
);

CREATE INDEX idx_jobs_employer_id ON jobs (employer_id);
CREATE INDEX idx_jobs_posted_by ON jobs (posted_by);
CREATE INDEX idx_jobs_slug ON jobs (slug);
CREATE INDEX idx_jobs_title ON jobs USING GIN (title gin_trgm_ops);
CREATE INDEX idx_jobs_department ON jobs (department);
CREATE INDEX idx_jobs_employment_type ON jobs (employment_type);
CREATE INDEX idx_jobs_experience_level ON jobs (experience_level);
CREATE INDEX idx_jobs_is_active ON jobs (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_jobs_is_featured ON jobs (is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_jobs_is_remote ON jobs (is_remote) WHERE is_remote = TRUE;
CREATE INDEX idx_jobs_published_at ON jobs (published_at DESC);
CREATE INDEX idx_jobs_expires_at ON jobs (expires_at);
CREATE INDEX idx_jobs_created_at ON jobs (created_at DESC);
CREATE INDEX idx_jobs_views_count ON jobs (views_count DESC);
CREATE INDEX idx_jobs_applications_count ON jobs (applications_count DESC);
CREATE INDEX idx_jobs_search ON jobs USING GIN (search_vector);
CREATE INDEX idx_jobs_location ON jobs USING GIN (location);
CREATE INDEX idx_jobs_salary_range ON jobs USING GIN (salary_range);
CREATE INDEX idx_jobs_benefits ON jobs USING GIN (benefits);
CREATE INDEX idx_jobs_skills_required ON jobs USING GIN (skills_required);
CREATE INDEX idx_jobs_skills_preferred ON jobs USING GIN (skills_preferred);

-- ---------------------------------------------------------------------------
-- applications
-- ---------------------------------------------------------------------------
CREATE TABLE applications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id              UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    recruiter_id        UUID REFERENCES recruiters(id) ON DELETE SET NULL,
    status              application_status NOT NULL DEFAULT 'submitted',
    status_history      JSONB DEFAULT '[]',
    cover_letter        TEXT,
    custom_answers      JSONB DEFAULT '{}',
    source              VARCHAR(100),
    referral_code       VARCHAR(100),
    rating              INTEGER CHECK (rating >= 1 AND rating <= 5),
    internal_notes      TEXT,
    rejection_reason    TEXT,
    rejection_category  VARCHAR(100),
    offer_details       JSONB DEFAULT '{}',
    applied_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at         TIMESTAMPTZ,
    decided_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    UNIQUE (candidate_id, job_id)
);

CREATE INDEX idx_applications_candidate_id ON applications (candidate_id);
CREATE INDEX idx_applications_job_id ON applications (job_id);
CREATE INDEX idx_applications_recruiter_id ON applications (recruiter_id);
CREATE INDEX idx_applications_status ON applications (status);
CREATE INDEX idx_applications_applied_at ON applications (applied_at DESC);
CREATE INDEX idx_applications_reviewed_at ON applications (reviewed_at DESC);
CREATE INDEX idx_applications_decided_at ON applications (decided_at DESC);
CREATE INDEX idx_applications_source ON applications (source);
CREATE INDEX idx_applications_rating ON applications (rating);
CREATE INDEX idx_applications_status_history ON applications USING GIN (status_history);
CREATE INDEX idx_applications_custom_answers ON applications USING GIN (custom_answers);
CREATE INDEX idx_applications_offer_details ON applications USING GIN (offer_details);
CREATE INDEX idx_applications_candidate_job ON applications (candidate_id, job_id);
CREATE INDEX idx_applications_job_status ON applications (job_id, status);

-- ---------------------------------------------------------------------------
-- interviews
-- ---------------------------------------------------------------------------
CREATE TABLE interviews (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    interviewer_id      UUID NOT NULL REFERENCES recruiters(id) ON DELETE RESTRICT,
    interview_type       interview_type NOT NULL,
    status              interview_status NOT NULL DEFAULT 'scheduled',
    scheduled_at        TIMESTAMPTZ NOT NULL,
    duration_minutes    INTEGER NOT NULL DEFAULT 60,
    timezone            VARCHAR(50) NOT NULL DEFAULT 'UTC',
    location            VARCHAR(500),
    meeting_url         VARCHAR(1000),
    meeting_id          VARCHAR(255),
    feedback            JSONB DEFAULT '{}',
    overall_rating      INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    recommendation      VARCHAR(50),
    notes               TEXT,
    candidate_notes     TEXT,
    no_show_reason      TEXT,
    rescheduled_from    UUID REFERENCES interviews(id) ON DELETE SET NULL,
    reminder_sent_at    TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_interviews_application_id ON interviews (application_id);
CREATE INDEX idx_interviews_interviewer_id ON interviews (interviewer_id);
CREATE INDEX idx_interviews_status ON interviews (status);
CREATE INDEX idx_interviews_scheduled_at ON interviews (scheduled_at);
CREATE INDEX idx_interviews_interview_type ON interviews (interview_type);
CREATE INDEX idx_interviews_overall_rating ON interviews (overall_rating);
CREATE INDEX idx_interviews_feedback ON interviews USING GIN (feedback);
CREATE INDEX idx_interviews_application_scheduled ON interviews (application_id, scheduled_at DESC);

-- ---------------------------------------------------------------------------
-- assessments
-- ---------------------------------------------------------------------------
CREATE TABLE assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    assessment_type     assessment_type NOT NULL,
    status              assessment_status NOT NULL DEFAULT 'pending',
    title               VARCHAR(300) NOT NULL,
    description         TEXT,
    instructions        TEXT,
    duration_minutes    INTEGER,
    max_score           NUMERIC(6,2),
    passing_score       NUMERIC(6,2),
    questions           JSONB DEFAULT '[]',
    candidate_answers   JSONB DEFAULT '{}',
    score               NUMERIC(6,2),
    score_details       JSONB DEFAULT '{}',
    evaluator_id        UUID REFERENCES recruiters(id) ON DELETE SET NULL,
    evaluation_notes    TEXT,
    started_at          TIMESTAMPTZ,
    submitted_at        TIMESTAMPTZ,
    evaluated_at        TIMESTAMPTZ,
    due_at              TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_assessments_application_id ON assessments (application_id);
CREATE INDEX idx_assessments_assessment_type ON assessments (assessment_type);
CREATE INDEX idx_assessments_status ON assessments (status);
CREATE INDEX idx_assessments_evaluator_id ON assessments (evaluator_id);
CREATE INDEX idx_assessments_due_at ON assessments (due_at);
CREATE INDEX idx_assessments_submitted_at ON assessments (submitted_at DESC);
CREATE INDEX idx_assessments_evaluated_at ON assessments (evaluated_at DESC);
CREATE INDEX idx_assessments_questions ON assessments USING GIN (questions);
CREATE INDEX idx_assessments_candidate_answers ON assessments USING GIN (candidate_answers);
CREATE INDEX idx_assessments_score_details ON assessments USING GIN (score_details);
CREATE INDEX idx_assessments_application_type ON assessments (application_id, assessment_type);

-- ---------------------------------------------------------------------------
-- skills
-- ---------------------------------------------------------------------------
CREATE TABLE skills (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(150) NOT NULL UNIQUE,
    slug                VARCHAR(150) NOT NULL UNIQUE,
    category            VARCHAR(100),
    subcategory         VARCHAR(100),
    description         TEXT,
    aliases             JSONB DEFAULT '[]',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skills_name ON skills USING GIN (name gin_trgm_ops);
CREATE INDEX idx_skills_slug ON skills (slug);
CREATE INDEX idx_skills_category ON skills (category);
CREATE INDEX idx_skills_subcategory ON skills (subcategory);
CREATE INDEX idx_skills_is_active ON skills (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_skills_aliases ON skills USING GIN (aliases);

-- ---------------------------------------------------------------------------
-- experiences
-- ---------------------------------------------------------------------------
CREATE TABLE experiences (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    company_name        VARCHAR(200) NOT NULL,
    company_logo_url    VARCHAR(1000),
    title               VARCHAR(200) NOT NULL,
    employment_type     experience_type NOT NULL DEFAULT 'full_time',
    department          VARCHAR(100),
    location            VARCHAR(200),
    is_remote          BOOLEAN NOT NULL DEFAULT FALSE,
    start_date          DATE NOT NULL,
    end_date            DATE,
    is_current          BOOLEAN NOT NULL DEFAULT FALSE,
    description         TEXT,
    achievements        JSONB DEFAULT '[]',
    skills_used         JSONB DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_experiences_candidate_id ON experiences (candidate_id);
CREATE INDEX idx_experiences_company_name ON experiences USING GIN (company_name gin_trgm_ops);
CREATE INDEX idx_experiences_title ON experiences USING GIN (title gin_trgm_ops);
CREATE INDEX idx_experiences_employment_type ON experiences (employment_type);
CREATE INDEX idx_experiences_start_date ON experiences (start_date DESC);
CREATE INDEX idx_experiences_end_date ON experiences (end_date DESC);
CREATE INDEX idx_experiences_is_current ON experiences (is_current) WHERE is_current = TRUE;
CREATE INDEX idx_experiences_achievements ON experiences USING GIN (achievements);
CREATE INDEX idx_experiences_skills_used ON experiences USING GIN (skills_used);
CREATE INDEX idx_experiences_candidate_current ON experiences (candidate_id, is_current);

-- ---------------------------------------------------------------------------
-- education
-- ---------------------------------------------------------------------------
CREATE TABLE education (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    institution_name    VARCHAR(300) NOT NULL,
    institution_logo_url VARCHAR(1000),
    degree              VARCHAR(200) NOT NULL,
    field_of_study      VARCHAR(200),
    education_level     education_level NOT NULL,
    start_date          DATE,
    end_date            DATE,
    is_current          BOOLEAN NOT NULL DEFAULT FALSE,
    gpa                 NUMERIC(3,2) CHECK (gpa >= 0.00 AND gpa <= 4.00),
    max_gpa             NUMERIC(3,2) CHECK (max_gpa >= 0.00 AND max_gpa <= 4.00),
    honors              VARCHAR(200),
    activities          TEXT,
    coursework          JSONB DEFAULT '[]',
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_education_candidate_id ON education (candidate_id);
CREATE INDEX idx_education_institution_name ON education USING GIN (institution_name gin_trgm_ops);
CREATE INDEX idx_education_degree ON education USING GIN (degree gin_trgm_ops);
CREATE INDEX idx_education_field_of_study ON education USING GIN (field_of_study gin_trgm_ops);
CREATE INDEX idx_education_education_level ON education (education_level);
CREATE INDEX idx_education_start_date ON education (start_date DESC);
CREATE INDEX idx_education_end_date ON education (end_date DESC);
CREATE INDEX idx_education_is_current ON education (is_current) WHERE is_current = TRUE;
CREATE INDEX idx_education_coursework ON education USING GIN (coursework);
CREATE INDEX idx_education_candidate_level ON education (candidate_id, education_level);

-- ---------------------------------------------------------------------------
-- talent_pools
-- ---------------------------------------------------------------------------
CREATE TABLE talent_pools (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employer_id         UUID NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
    created_by          UUID NOT NULL REFERENCES recruiters(id) ON DELETE RESTRICT,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    pool_type           talent_pool_type NOT NULL DEFAULT 'custom',
    criteria            JSONB DEFAULT '{}',
    member_count        INTEGER NOT NULL DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_talent_pools_employer_id ON talent_pools (employer_id);
CREATE INDEX idx_talent_pools_created_by ON talent_pools (created_by);
CREATE INDEX idx_talent_pools_pool_type ON talent_pools (pool_type);
CREATE INDEX idx_talent_pools_is_active ON talent_pools (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_talent_pools_criteria ON talent_pools USING GIN (criteria);
CREATE INDEX idx_talent_pools_name ON talent_pools USING GIN (name gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- talent_pool_members (junction table)
-- ---------------------------------------------------------------------------
CREATE TABLE talent_pool_members (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    talent_pool_id      UUID NOT NULL REFERENCES talent_pools(id) ON DELETE CASCADE,
    candidate_id        UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    added_by            UUID NOT NULL REFERENCES recruiters(id) ON DELETE RESTRICT,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (talent_pool_id, candidate_id)
);

CREATE INDEX idx_talent_pool_members_pool_id ON talent_pool_members (talent_pool_id);
CREATE INDEX idx_talent_pool_members_candidate_id ON talent_pool_members (candidate_id);
CREATE INDEX idx_talent_pool_members_added_by ON talent_pool_members (added_by);
CREATE INDEX idx_talent_pool_members_created_at ON talent_pool_members (created_at DESC);

-- ---------------------------------------------------------------------------
-- candidate_skills (junction table)
-- ---------------------------------------------------------------------------
CREATE TABLE candidate_skills (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id            UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level   INTEGER NOT NULL DEFAULT 1 CHECK (proficiency_level >= 1 AND proficiency_level <= 5),
    years_experience    NUMERIC(4,1),
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    verified_by         UUID REFERENCES recruiters(id) ON DELETE SET NULL,
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (candidate_id, skill_id)
);

CREATE INDEX idx_candidate_skills_candidate_id ON candidate_skills (candidate_id);
CREATE INDEX idx_candidate_skills_skill_id ON candidate_skills (skill_id);
CREATE INDEX idx_candidate_skills_proficiency ON candidate_skills (proficiency_level);
CREATE INDEX idx_candidate_skills_is_primary ON candidate_skills (is_primary) WHERE is_primary = TRUE;
CREATE INDEX idx_candidate_skills_verified_by ON candidate_skills (verified_by);

-- ---------------------------------------------------------------------------
-- analytics_events (PARTITIONED TABLE)
-- ---------------------------------------------------------------------------
CREATE TABLE analytics_events (
    id                  UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type          event_type NOT NULL,
    event_name          VARCHAR(200) NOT NULL,
    session_id          VARCHAR(255),
    user_id             UUID,
    candidate_id        UUID REFERENCES candidates(id) ON DELETE SET NULL,
    employer_id         UUID REFERENCES employers(id) ON DELETE SET NULL,
    job_id              UUID REFERENCES jobs(id) ON DELETE SET NULL,
    application_id      UUID REFERENCES applications(id) ON DELETE SET NULL,
    interview_id        UUID REFERENCES interviews(id) ON DELETE SET NULL,
    assessment_id       UUID REFERENCES assessments(id) ON DELETE SET NULL,
    recruiter_id        UUID REFERENCES recruiters(id) ON DELETE SET NULL,
    ip_address          INET,
    user_agent          TEXT,
    referrer            VARCHAR(1000),
    url                 VARCHAR(2000),
    page_title          VARCHAR(500),
    metadata            JSONB DEFAULT '{}',
    properties          JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for the current and next 12 months
-- Note: In production, use pg_partman or similar for automatic partition management
CREATE TABLE analytics_events_2026_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE analytics_events_2026_02 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE analytics_events_2026_03 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE analytics_events_2026_04 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE analytics_events_2026_05 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE analytics_events_2026_06 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE analytics_events_2026_07 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE analytics_events_2026_08 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE analytics_events_2026_09 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE analytics_events_2026_10 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE analytics_events_2026_11 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE analytics_events_2026_12 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE analytics_events_2027_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE analytics_events_2027_02 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE analytics_events_2027_03 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE analytics_events_2027_04 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');
CREATE TABLE analytics_events_2027_05 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-05-01') TO ('2027-06-01');
CREATE TABLE analytics_events_2027_06 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-06-01') TO ('2027-07-01');
CREATE TABLE analytics_events_2027_07 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-07-01') TO ('2027-08-01');
CREATE TABLE analytics_events_2027_08 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-08-01') TO ('2027-09-01');
CREATE TABLE analytics_events_2027_09 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-09-01') TO ('2027-10-01');
CREATE TABLE analytics_events_2027_10 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-10-01') TO ('2027-11-01');
CREATE TABLE analytics_events_2027_11 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-11-01') TO ('2027-12-01');
CREATE TABLE analytics_events_2027_12 PARTITION OF analytics_events
    FOR VALUES FROM ('2027-12-01') TO ('2028-01-01');

-- Default partition for any dates outside the defined ranges
CREATE TABLE analytics_events_default PARTITION OF analytics_events DEFAULT;

-- Indexes on partitioned table (inherited by all partitions)
CREATE INDEX idx_analytics_events_event_type ON analytics_events (event_type);
CREATE INDEX idx_analytics_events_event_name ON analytics_events (event_name);
CREATE INDEX idx_analytics_events_session_id ON analytics_events (session_id);
CREATE INDEX idx_analytics_events_user_id ON analytics_events (user_id);
CREATE INDEX idx_analytics_events_candidate_id ON analytics_events (candidate_id);
CREATE INDEX idx_analytics_events_employer_id ON analytics_events (employer_id);
CREATE INDEX idx_analytics_events_job_id ON analytics_events (job_id);
CREATE INDEX idx_analytics_events_application_id ON analytics_events (application_id);
CREATE INDEX idx_analytics_events_created_at ON analytics_events (created_at DESC);
CREATE INDEX idx_analytics_events_metadata ON analytics_events USING GIN (metadata);
CREATE INDEX idx_analytics_events_properties ON analytics_events USING GIN (properties);
CREATE INDEX idx_analytics_events_event_type_created ON analytics_events (event_type, created_at DESC);
CREATE INDEX idx_analytics_events_user_created ON analytics_events (user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- audit_log
-- ---------------------------------------------------------------------------
CREATE TABLE audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name          VARCHAR(100) NOT NULL,
    record_id           UUID NOT NULL,
    action              audit_action NOT NULL,
    old_values          JSONB,
    new_values          JSONB,
    changed_fields      JSONB,
    performed_by        UUID,
    performed_by_type   VARCHAR(50),
    ip_address          INET,
    user_agent          TEXT,
    session_id          VARCHAR(255),
    reason              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_table_name ON audit_log (table_name);
CREATE INDEX idx_audit_log_record_id ON audit_log (record_id);
CREATE INDEX idx_audit_log_action ON audit_log (action);
CREATE INDEX idx_audit_log_performed_by ON audit_log (performed_by);
CREATE INDEX idx_audit_log_created_at ON audit_log (created_at DESC);
CREATE INDEX idx_audit_log_table_record ON audit_log (table_name, record_id);
CREATE INDEX idx_audit_log_old_values ON audit_log USING GIN (old_values);
CREATE INDEX idx_audit_log_new_values ON audit_log USING GIN (new_values);
CREATE INDEX idx_audit_log_changed_fields ON audit_log USING GIN (changed_fields);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Updated_at trigger function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER trg_employers_updated_at
    BEFORE UPDATE ON employers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_recruiters_updated_at
    BEFORE UPDATE ON recruiters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_interviews_updated_at
    BEFORE UPDATE ON interviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_assessments_updated_at
    BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_skills_updated_at
    BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_experiences_updated_at
    BEFORE UPDATE ON experiences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_education_updated_at
    BEFORE UPDATE ON education
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_talent_pools_updated_at
    BEFORE UPDATE ON talent_pools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_candidate_skills_updated_at
    BEFORE UPDATE ON candidate_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ---------------------------------------------------------------------------
-- Full-text search update trigger function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'employers' THEN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.industry, '')), 'C');
    ELSIF TG_TABLE_NAME = 'recruiters' THEN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.first_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.last_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.department, '')), 'C');
    ELSIF TG_TABLE_NAME = 'candidates' THEN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.first_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.last_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.current_title, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.current_company, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(NEW.resume_text, '')), 'D');
    ELSIF TG_TABLE_NAME = 'jobs' THEN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.requirements, '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(NEW.responsibilities, '')), 'C');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_employers_search_vector
    BEFORE INSERT OR UPDATE ON employers
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

CREATE TRIGGER trg_recruiters_search_vector
    BEFORE INSERT OR UPDATE ON recruiters
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

CREATE TRIGGER trg_candidates_search_vector
    BEFORE INSERT OR UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

CREATE TRIGGER trg_jobs_search_vector
    BEFORE INSERT OR UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- ---------------------------------------------------------------------------
-- Audit log trigger function
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields JSONB;
    key TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        old_data = to_jsonb(OLD);
        new_data = NULL;
        changed_fields = NULL;
    ELSIF TG_OP = 'INSERT' THEN
        old_data = NULL;
        new_data = to_jsonb(NEW);
        changed_fields = NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);
        changed_fields = '{}'::JSONB;
        FOR key IN SELECT jsonb_object_keys(new_data) LOOP
            IF old_data->key IS DISTINCT FROM new_data->key THEN
                changed_fields = changed_fields || jsonb_build_object(key, true);
            END IF;
        END LOOP;
    END IF;

    INSERT INTO audit_log (
        table_name, record_id, action, old_values, new_values,
        changed_fields, performed_by, performed_by_type, ip_address,
        user_agent, session_id, reason
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP::audit_action,
        old_data,
        new_data,
        changed_fields,
        NULL, -- Set by application
        'system',
        NULL,
        NULL,
        NULL,
        NULL
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to core tables
CREATE TRIGGER trg_audit_employers
    AFTER INSERT OR UPDATE OR DELETE ON employers
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_recruiters
    AFTER INSERT OR UPDATE OR DELETE ON recruiters
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_candidates
    AFTER INSERT OR UPDATE OR DELETE ON candidates
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_jobs
    AFTER INSERT OR UPDATE OR DELETE ON jobs
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_applications
    AFTER INSERT OR UPDATE OR DELETE ON applications
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_interviews
    AFTER INSERT OR UPDATE OR DELETE ON interviews
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_assessments
    AFTER INSERT OR UPDATE OR DELETE ON assessments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_talent_pools
    AFTER INSERT OR UPDATE OR DELETE ON talent_pools
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active jobs with employer info
CREATE VIEW v_active_jobs AS
SELECT
    j.*,
    e.name AS employer_name,
    e.slug AS employer_slug,
    e.logo_url AS employer_logo_url,
    e.website AS employer_website
FROM jobs j
JOIN employers e ON j.employer_id = e.id
WHERE j.is_active = TRUE
    AND j.deleted_at IS NULL
    AND (j.expires_at IS NULL OR j.expires_at > NOW());

-- Candidate application summary
CREATE VIEW v_candidate_applications AS
SELECT
    a.*,
    c.first_name AS candidate_first_name,
    c.last_name AS candidate_last_name,
    c.email AS candidate_email,
    j.title AS job_title,
    j.slug AS job_slug,
    e.name AS employer_name,
    e.slug AS employer_slug
FROM applications a
JOIN candidates c ON a.candidate_id = c.id
JOIN jobs j ON a.job_id = j.id
JOIN employers e ON j.employer_id = e.id
WHERE a.deleted_at IS NULL;

-- Recruiter pipeline summary
CREATE VIEW v_recruiter_pipeline AS
SELECT
    r.id AS recruiter_id,
    r.first_name || ' ' || r.last_name AS recruiter_name,
    r.email AS recruiter_email,
    e.name AS employer_name,
    COUNT(DISTINCT a.id) AS total_applications,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'submitted') AS new_applications,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'interview') AS in_interview,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'offer') AS in_offer,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS hired,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') AS rejected,
    COUNT(DISTINCT i.id) AS total_interviews,
    COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'scheduled') AS upcoming_interviews
FROM recruiters r
JOIN employers e ON r.employer_id = e.id
LEFT JOIN applications a ON a.recruiter_id = r.id AND a.deleted_at IS NULL
LEFT JOIN interviews i ON i.application_id = a.id AND i.deleted_at IS NULL
WHERE r.is_active = TRUE
GROUP BY r.id, r.first_name, r.last_name, r.email, e.name;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE employers IS 'Companies posting jobs on the platform';
COMMENT ON TABLE recruiters IS 'Recruiter users belonging to employers';
COMMENT ON TABLE candidates IS 'Job seekers and candidate profiles';
COMMENT ON TABLE jobs IS 'Job postings created by employers';
COMMENT ON TABLE applications IS 'Job applications linking candidates to jobs';
COMMENT ON TABLE interviews IS 'Scheduled interviews for applications';
COMMENT ON TABLE assessments IS 'Assessments and tests for applications';
COMMENT ON TABLE skills IS 'Master list of skills for matching';
COMMENT ON TABLE experiences IS 'Candidate work experience history';
COMMENT ON TABLE education IS 'Candidate education history';
COMMENT ON TABLE talent_pools IS 'Curated groups of candidates';
COMMENT ON TABLE talent_pool_members IS 'Junction table for talent pool membership';
COMMENT ON TABLE candidate_skills IS 'Junction table linking candidates to skills';
COMMENT ON TABLE analytics_events IS 'Partitioned table for all analytics events';
COMMENT ON TABLE audit_log IS 'Audit trail for all data changes';
