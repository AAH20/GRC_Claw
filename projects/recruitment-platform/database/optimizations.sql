-- ============================================================================
-- Recruitment Platform Database Optimizations
-- PostgreSQL 16+
-- ============================================================================

-- ============================================================================
-- 1. QUERY OPTIMIZATION — ADD MISSING INDEXES
-- ============================================================================

-- Composite index for common job search queries (active + published + department)
CREATE INDEX IF NOT EXISTS idx_jobs_active_published_department
    ON jobs (is_active, published_at DESC, department)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- Composite index for candidate search by location and experience
CREATE INDEX IF NOT EXISTS idx_candidates_location_experience
    ON candidates (current_location, years_experience)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- Composite index for application status transitions
CREATE INDEX IF NOT EXISTS idx_applications_status_applied
    ON applications (status, applied_at DESC)
    WHERE deleted_at IS NULL;

-- Index for interview scheduling queries
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_status
    ON interviews (scheduled_at, status)
    WHERE deleted_at IS NULL AND status IN ('scheduled', 'confirmed');

-- Index for assessment due date queries
CREATE INDEX IF NOT EXISTS idx_assessments_due_status
    ON assessments (due_at, status)
    WHERE deleted_at IS NULL AND status IN ('pending', 'in_progress');

-- Index for talent pool member lookups
CREATE INDEX IF NOT EXISTS idx_talent_pool_members_pool_candidate
    ON talent_pool_members (talent_pool_id, candidate_id);

-- Index for candidate skill lookups by proficiency
CREATE INDEX IF NOT EXISTS idx_candidate_skills_candidate_proficiency
    ON candidate_skills (candidate_id, proficiency_level DESC);

-- Index for experience date range queries
CREATE INDEX IF NOT EXISTS idx_experiences_candidate_dates
    ON experiences (candidate_id, start_date DESC, end_date DESC);

-- Index for education date range queries
CREATE INDEX IF NOT EXISTS idx_education_candidate_dates
    ON education (candidate_id, start_date DESC, end_date DESC);

-- Partial index for active employers
CREATE INDEX IF NOT EXISTS idx_employers_active_verified
    ON employers (is_active, is_verified)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- Index for recruiter employer lookups
CREATE INDEX IF NOT EXISTS idx_recruiters_employer_active
    ON recruiters (employer_id, is_active)
    WHERE deleted_at IS NULL;

-- ============================================================================
-- 2. PARTITIONING — ANALYTICS_EVENTS (already partitioned, add future partitions)
-- ============================================================================

-- Add partitions for 2028
CREATE TABLE IF NOT EXISTS analytics_events_2028_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-01-01') TO ('2028-02-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_02 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-02-01') TO ('2028-03-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_03 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-03-01') TO ('2028-04-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_04 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-04-01') TO ('2028-05-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_05 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-05-01') TO ('2028-06-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_06 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-06-01') TO ('2028-07-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_07 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-07-01') TO ('2028-08-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_08 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-08-01') TO ('2028-09-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_09 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-09-01') TO ('2028-10-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_10 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-10-01') TO ('2028-11-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_11 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-11-01') TO ('2028-12-01');
CREATE TABLE IF NOT EXISTS analytics_events_2028_12 PARTITION OF analytics_events
    FOR VALUES FROM ('2028-12-01') TO ('2029-01-01');

-- ============================================================================
-- 3. CONSTRAINTS — ADD CHECK AND UNIQUE CONSTRAINTS
-- ============================================================================

-- Employers: founded_year must be reasonable
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_employers_founded_year'
    ) THEN
        ALTER TABLE employers ADD CONSTRAINT chk_employers_founded_year
            CHECK (founded_year IS NULL OR (founded_year >= 1800 AND founded_year <= 2100));
    END IF;
END $$;

-- Employers: slug must be lowercase alphanumeric with hyphens
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_employers_slug_format'
    ) THEN
        ALTER TABLE employers ADD CONSTRAINT chk_employers_slug_format
            CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$');
    END IF;
END $$;

-- Jobs: openings must be positive
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_openings_positive'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_openings_positive
            CHECK (openings > 0);
    END IF;
END $$;

-- Jobs: views_count and applications_count must be non-negative
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_views_count_non_negative'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_views_count_non_negative
            CHECK (views_count >= 0);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_applications_count_non_negative'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_applications_count_non_negative
            CHECK (applications_count >= 0);
    END IF;
END $$;

-- Jobs: expires_at must be after published_at if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_expires_after_published'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_expires_after_published
            CHECK (expires_at IS NULL OR published_at IS NULL OR expires_at > published_at);
    END IF;
END $$;

-- Jobs: closed_at must be after published_at if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_closed_after_published'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_closed_after_published
            CHECK (closed_at IS NULL OR published_at IS NULL OR closed_at > published_at);
    END IF;
END $$;

-- Jobs: slug must be lowercase alphanumeric with hyphens
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_slug_format'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_slug_format
            CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$');
    END IF;
END $$;

-- Candidates: years_experience must be non-negative
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_years_experience_non_negative'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_years_experience_non_negative
            CHECK (years_experience IS NULL OR years_experience >= 0);
    END IF;
END $$;

-- Candidates: notice_period_days must be non-negative
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_notice_period_non_negative'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_notice_period_non_negative
            CHECK (notice_period_days IS NULL OR notice_period_days >= 0);
    END IF;
END $$;

-- Candidates: profile_completeness must be between 0 and 100
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_profile_completeness_range'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_profile_completeness_range
            CHECK (profile_completeness >= 0 AND profile_completeness <= 100);
    END IF;
END $$;

-- Candidates: date_of_birth must be in the past
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_dob_past'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_dob_past
            CHECK (date_of_birth IS NULL OR date_of_birth < CURRENT_DATE);
    END IF;
END $$;

-- Interviews: duration_minutes must be positive
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_interviews_duration_positive'
    ) THEN
        ALTER TABLE interviews ADD CONSTRAINT chk_interviews_duration_positive
            CHECK (duration_minutes > 0);
    END IF;
END $$;

-- Interviews: overall_rating must be between 1 and 5 (if not null)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_interviews_rating_range'
    ) THEN
        ALTER TABLE interviews ADD CONSTRAINT chk_interviews_rating_range
            CHECK (overall_rating IS NULL OR (overall_rating >= 1 AND overall_rating <= 5));
    END IF;
END $$;

-- Assessments: max_score must be positive
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_assessments_max_score_positive'
    ) THEN
        ALTER TABLE assessments ADD CONSTRAINT chk_assessments_max_score_positive
            CHECK (max_score IS NULL OR max_score > 0);
    END IF;
END $$;

-- Assessments: passing_score must be non-negative and <= max_score
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_assessments_passing_score_range'
    ) THEN
        ALTER TABLE assessments ADD CONSTRAINT chk_assessments_passing_score_range
            CHECK (passing_score IS NULL OR (passing_score >= 0 AND (max_score IS NULL OR passing_score <= max_score)));
    END IF;
END $$;

-- Assessments: score must be between 0 and max_score
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_assessments_score_range'
    ) THEN
        ALTER TABLE assessments ADD CONSTRAINT chk_assessments_score_range
            CHECK (score IS NULL OR (score >= 0 AND (max_score IS NULL OR score <= max_score)));
    END IF;
END $$;

-- Assessments: duration_minutes must be positive if set
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_assessments_duration_positive'
    ) THEN
        ALTER TABLE assessments ADD CONSTRAINT chk_assessments_duration_positive
            CHECK (duration_minutes IS NULL OR duration_minutes > 0);
    END IF;
END $$;

-- Experiences: end_date must be after start_date if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_experiences_end_after_start'
    ) THEN
        ALTER TABLE experiences ADD CONSTRAINT chk_experiences_end_after_start
            CHECK (end_date IS NULL OR end_date >= start_date);
    END IF;
END $$;

-- Experiences: is_current should be true when end_date is null
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_experiences_current_no_end'
    ) THEN
        ALTER TABLE experiences ADD CONSTRAINT chk_experiences_current_no_end
            CHECK (is_current = FALSE OR end_date IS NULL);
    END IF;
END $$;

-- Education: end_date must be after start_date if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_education_end_after_start'
    ) THEN
        ALTER TABLE education ADD CONSTRAINT chk_education_end_after_start
            CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date);
    END IF;
END $$;

-- Education: gpa must be <= max_gpa if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_education_gpa_lte_max'
    ) THEN
        ALTER TABLE education ADD CONSTRAINT chk_education_gpa_lte_max
            CHECK (gpa IS NULL OR max_gpa IS NULL OR gpa <= max_gpa);
    END IF;
END $$;

-- Talent pools: member_count must be non-negative
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_talent_pools_member_count_non_negative'
    ) THEN
        ALTER TABLE talent_pools ADD CONSTRAINT chk_talent_pools_member_count_non_negative
            CHECK (member_count >= 0);
    END IF;
END $$;

-- Applications: reviewed_at must be after applied_at if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_applications_reviewed_after_applied'
    ) THEN
        ALTER TABLE applications ADD CONSTRAINT chk_applications_reviewed_after_applied
            CHECK (reviewed_at IS NULL OR reviewed_at >= applied_at);
    END IF;
END $$;

-- Applications: decided_at must be after reviewed_at if both exist
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_applications_decided_after_reviewed'
    ) THEN
        ALTER TABLE applications ADD CONSTRAINT chk_applications_decided_after_reviewed
            CHECK (decided_at IS NULL OR reviewed_at IS NULL OR decided_at >= reviewed_at);
    END IF;
END $$;

-- Applications: rating must be between 1 and 5 (if not null)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_applications_rating_range'
    ) THEN
        ALTER TABLE applications ADD CONSTRAINT chk_applications_rating_range
            CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));
    END IF;
END $$;

-- ============================================================================
-- 4. TRIGGERS — ADD AUDIT TRIGGERS FOR MISSING TABLES
-- ============================================================================

-- Audit trigger for experiences
CREATE OR REPLACE FUNCTION audit_trigger_func_experiences()
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
        NULL,
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

-- Audit trigger for education
CREATE OR REPLACE FUNCTION audit_trigger_func_education()
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
        NULL,
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

-- Audit trigger for skills
CREATE OR REPLACE FUNCTION audit_trigger_func_skills()
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
        NULL,
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

-- Audit trigger for candidate_skills
CREATE OR REPLACE FUNCTION audit_trigger_func_candidate_skills()
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
        NULL,
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

-- Audit trigger for talent_pool_members
CREATE OR REPLACE FUNCTION audit_trigger_func_talent_pool_members()
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
        NULL,
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

-- Apply audit triggers to tables that don't have them
DROP TRIGGER IF EXISTS trg_audit_experiences ON experiences;
CREATE TRIGGER trg_audit_experiences
    AFTER INSERT OR UPDATE OR DELETE ON experiences
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func_experiences();

DROP TRIGGER IF EXISTS trg_audit_education ON education;
CREATE TRIGGER trg_audit_education
    AFTER INSERT OR UPDATE OR DELETE ON education
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func_education();

DROP TRIGGER IF EXISTS trg_audit_skills ON skills;
CREATE TRIGGER trg_audit_skills
    AFTER INSERT OR UPDATE OR DELETE ON skills
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func_skills();

DROP TRIGGER IF EXISTS trg_audit_candidate_skills ON candidate_skills;
CREATE TRIGGER trg_audit_candidate_skills
    AFTER INSERT OR UPDATE OR DELETE ON candidate_skills
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func_candidate_skills();

DROP TRIGGER IF EXISTS trg_audit_talent_pool_members ON talent_pool_members;
CREATE TRIGGER trg_audit_talent_pool_members
    AFTER INSERT OR UPDATE OR DELETE ON talent_pool_members
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func_talent_pool_members();

-- ============================================================================
-- 5. VIEWS — CREATE MATERIALIZED VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Materialized view: Job application statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_job_application_stats AS
SELECT
    j.id AS job_id,
    j.title AS job_title,
    j.employer_id,
    e.name AS employer_name,
    j.is_active AS job_is_active,
    j.published_at,
    j.expires_at,
    COUNT(a.id) AS total_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'submitted') AS new_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'screening') AS screening_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'interview') AS interview_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'assessment') AS assessment_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'offer') AS offer_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'hired') AS hired_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'rejected') AS rejected_applications,
    COUNT(a.id) FILTER (WHERE a.status = 'withdrawn') AS withdrawn_applications,
    AVG(a.rating) FILTER (WHERE a.rating IS NOT NULL) AS avg_rating,
    MAX(a.applied_at) AS last_application_at
FROM jobs j
JOIN employers e ON j.employer_id = e.id
LEFT JOIN applications a ON a.job_id = j.id AND a.deleted_at IS NULL
WHERE j.deleted_at IS NULL
GROUP BY j.id, j.title, j.employer_id, e.name, j.is_active, j.published_at, j.expires_at;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_job_application_stats_job_id
    ON mv_job_application_stats (job_id);

-- Materialized view: Candidate pipeline summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_candidate_pipeline_summary AS
SELECT
    c.id AS candidate_id,
    c.first_name || ' ' || c.last_name AS candidate_name,
    c.email AS candidate_email,
    c.current_title,
    c.current_company,
    c.years_experience,
    c.source,
    COUNT(DISTINCT a.id) AS total_applications,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS hired_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') AS rejected_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status IN ('submitted', 'screening', 'interview', 'assessment', 'offer')) AS active_applications,
    COUNT(DISTINCT i.id) AS total_interviews,
    COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'completed') AS completed_interviews,
    COUNT(DISTINCT ass.id) AS total_assessments,
    COUNT(DISTINCT ass.id) FILTER (WHERE ass.status = 'evaluated') AS evaluated_assessments,
    MAX(a.applied_at) AS last_application_at,
    MAX(i.scheduled_at) AS last_interview_at
FROM candidates c
LEFT JOIN applications a ON a.candidate_id = c.id AND a.deleted_at IS NULL
LEFT JOIN interviews i ON i.application_id = a.id AND i.deleted_at IS NULL
LEFT JOIN assessments ass ON ass.application_id = a.id AND ass.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.first_name, c.last_name, c.email, c.current_title, c.current_company, c.years_experience, c.source;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_candidate_pipeline_summary_candidate_id
    ON mv_candidate_pipeline_summary (candidate_id);

-- Materialized view: Employer recruitment metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_employer_recruitment_metrics AS
SELECT
    e.id AS employer_id,
    e.name AS employer_name,
    e.industry,
    COUNT(DISTINCT j.id) AS total_jobs,
    COUNT(DISTINCT j.id) FILTER (WHERE j.is_active = TRUE AND j.deleted_at IS NULL) AS active_jobs,
    COUNT(DISTINCT a.id) AS total_applications,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS total_hired,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') AS total_rejected,
    COUNT(DISTINCT i.id) AS total_interviews,
    COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'completed') AS completed_interviews,
    COUNT(DISTINCT ass.id) AS total_assessments,
    COUNT(DISTINCT ass.id) FILTER (WHERE ass.status = 'evaluated') AS evaluated_assessments,
    COUNT(DISTINCT r.id) AS total_recruiters,
    AVG(a.rating) FILTER (WHERE a.rating IS NOT NULL) AS avg_application_rating
FROM employers e
LEFT JOIN jobs j ON j.employer_id = e.id AND j.deleted_at IS NULL
LEFT JOIN applications a ON a.job_id = j.id AND a.deleted_at IS NULL
LEFT JOIN interviews i ON i.application_id = a.id AND i.deleted_at IS NULL
LEFT JOIN assessments ass ON ass.application_id = a.id AND ass.deleted_at IS NULL
LEFT JOIN recruiters r ON r.employer_id = e.id AND r.deleted_at IS NULL
WHERE e.deleted_at IS NULL
GROUP BY e.id, e.name, e.industry;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_employer_recruitment_metrics_employer_id
    ON mv_employer_recruitment_metrics (employer_id);

-- Materialized view: Daily analytics summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_analytics_summary AS
SELECT
    DATE(created_at) AS event_date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT session_id) AS unique_sessions,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT candidate_id) AS unique_candidates,
    COUNT(DISTINCT employer_id) AS unique_employers,
    COUNT(DISTINCT job_id) AS unique_jobs
FROM analytics_events
GROUP BY DATE(created_at), event_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_analytics_summary_date_type
    ON mv_daily_analytics_summary (event_date, event_type);

-- Materialized view: Talent pool statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_talent_pool_stats AS
SELECT
    tp.id AS talent_pool_id,
    tp.name AS talent_pool_name,
    tp.pool_type,
    tp.employer_id,
    e.name AS employer_name,
    tp.member_count,
    COUNT(tpm.candidate_id) AS actual_member_count,
    AVG(c.years_experience) AS avg_member_experience,
    COUNT(DISTINCT a.id) AS total_applications_from_pool,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS hired_from_pool
FROM talent_pools tp
JOIN employers e ON tp.employer_id = e.id
LEFT JOIN talent_pool_members tpm ON tpm.talent_pool_id = tp.id
LEFT JOIN candidates c ON tpm.candidate_id = c.id
LEFT JOIN applications a ON a.candidate_id = c.id AND a.deleted_at IS NULL
WHERE tp.deleted_at IS NULL
GROUP BY tp.id, tp.name, tp.pool_type, tp.employer_id, e.name, tp.member_count;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_talent_pool_stats_pool_id
    ON mv_talent_pool_stats (talent_pool_id);

-- ============================================================================
-- 6. FUNCTIONS — CREATE STORED PROCEDURES FOR COMPLEX OPERATIONS
-- ============================================================================

-- Function: Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_job_application_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_candidate_pipeline_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_employer_recruitment_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_analytics_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_talent_pool_stats;
END;
$$ LANGUAGE plpgsql;

-- Function: Get candidate full profile
CREATE OR REPLACE FUNCTION get_candidate_full_profile(p_candidate_id UUID)
RETURNS TABLE (
    candidate_id UUID,
    email VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    current_title VARCHAR,
    current_company VARCHAR,
    years_experience NUMERIC,
    skills JSONB,
    experiences JSONB,
    education JSONB,
    applications JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.email,
        c.first_name,
        c.last_name,
        c.phone,
        c.current_title,
        c.current_company,
        c.years_experience,
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'skill_id', s.id,
                'skill_name', s.name,
                'proficiency', cs.proficiency_level,
                'is_primary', cs.is_primary
            ))
            FROM candidate_skills cs
            JOIN skills s ON cs.skill_id = s.id
            WHERE cs.candidate_id = c.id),
            '[]'::jsonb
        ) AS skills,
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'id', e.id,
                'company', e.company_name,
                'title', e.title,
                'start_date', e.start_date,
                'end_date', e.end_date,
                'is_current', e.is_current
            ) ORDER BY e.start_date DESC)
            FROM experiences e
            WHERE e.candidate_id = c.id AND e.deleted_at IS NULL),
            '[]'::jsonb
        ) AS experiences,
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'id', ed.id,
                'institution', ed.institution_name,
                'degree', ed.degree,
                'field_of_study', ed.field_of_study,
                'start_date', ed.start_date,
                'end_date', ed.end_date,
                'gpa', ed.gpa
            ) ORDER BY ed.start_date DESC)
            FROM education ed
            WHERE ed.candidate_id = c.id AND ed.deleted_at IS NULL),
            '[]'::jsonb
        ) AS education,
        COALESCE(
            (SELECT jsonb_agg(jsonb_build_object(
                'id', a.id,
                'job_title', j.title,
                'employer_name', e.name,
                'status', a.status,
                'applied_at', a.applied_at
            ) ORDER BY a.applied_at DESC)
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN employers e ON j.employer_id = e.id
            WHERE a.candidate_id = c.id AND a.deleted_at IS NULL),
            '[]'::jsonb
        ) AS applications
    FROM candidates c
    WHERE c.id = p_candidate_id AND c.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function: Search candidates with filters
CREATE OR REPLACE FUNCTION search_candidates(
    p_search_query TEXT DEFAULT NULL,
    p_location TEXT DEFAULT NULL,
    p_min_experience NUMERIC DEFAULT NULL,
    p_max_experience NUMERIC DEFAULT NULL,
    p_skill_ids UUID[] DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    candidate_id UUID,
    full_name TEXT,
    email VARCHAR,
    current_title VARCHAR,
    current_company VARCHAR,
    years_experience NUMERIC,
    location VARCHAR,
    matching_skills BIGINT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.first_name || ' ' || c.last_name,
        c.email,
        c.current_title,
        c.current_company,
        c.years_experience,
        c.current_location,
        COUNT(DISTINCT cs.skill_id) AS matching_skills,
        ts_rank(c.search_vector, plainto_tsquery('english', COALESCE(p_search_query, ''))) AS rank
    FROM candidates c
    LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
        AND (p_skill_ids IS NULL OR cs.skill_id = ANY(p_skill_ids))
    WHERE c.deleted_at IS NULL
        AND c.is_active = TRUE
        AND (p_search_query IS NULL OR c.search_vector @@ plainto_tsquery('english', p_search_query))
        AND (p_location IS NULL OR c.current_location ILIKE '%' || p_location || '%')
        AND (p_min_experience IS NULL OR c.years_experience >= p_min_experience)
        AND (p_max_experience IS NULL OR c.years_experience <= p_max_experience)
    GROUP BY c.id, c.first_name, c.last_name, c.email, c.current_title, c.current_company,
             c.years_experience, c.current_location, c.search_vector
    ORDER BY rank DESC, matching_skills DESC, c.years_experience DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function: Get recruiter dashboard data
CREATE OR REPLACE FUNCTION get_recruiter_dashboard(p_recruiter_id UUID)
RETURNS TABLE (
    total_applications BIGINT,
    new_applications BIGINT,
    in_interview BIGINT,
    in_offer BIGINT,
    hired BIGINT,
    rejected BIGINT,
    upcoming_interviews BIGINT,
    active_jobs BIGINT,
    avg_rating NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT a.id) AS total_applications,
        COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'submitted') AS new_applications,
        COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'interview') AS in_interview,
        COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'offer') AS in_offer,
        COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'hired') AS hired,
        COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') AS rejected,
        COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'scheduled' AND i.scheduled_at > NOW()) AS upcoming_interviews,
        COUNT(DISTINCT j.id) FILTER (WHERE j.is_active = TRUE AND j.deleted_at IS NULL) AS active_jobs,
        AVG(a.rating) FILTER (WHERE a.rating IS NOT NULL) AS avg_rating
    FROM recruiters r
    LEFT JOIN applications a ON a.recruiter_id = r.id AND a.deleted_at IS NULL
    LEFT JOIN interviews i ON i.application_id = a.id AND i.deleted_at IS NULL
    LEFT JOIN jobs j ON a.job_id = j.id
    WHERE r.id = p_recruiter_id AND r.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function: Update application status with history tracking
CREATE OR REPLACE FUNCTION update_application_status(
    p_application_id UUID,
    p_new_status application_status,
    p_changed_by UUID DEFAULT NULL,
    p_reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_status application_status;
    v_status_history JSONB;
BEGIN
    SELECT status, status_history INTO v_old_status, v_status_history
    FROM applications WHERE id = p_application_id AND deleted_at IS NULL;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF v_old_status = p_new_status THEN
        RETURN TRUE;
    END IF;

    v_status_history := COALESCE(v_status_history, '[]'::jsonb) || jsonb_build_object(
        'status', p_new_status,
        'changed_at', NOW(),
        'changed_by', p_changed_by,
        'reason', p_reason
    );

    UPDATE applications
    SET status = p_new_status,
        status_history = v_status_history,
        reviewed_at = CASE WHEN p_new_status IN ('screening', 'interview', 'assessment', 'offer', 'hired', 'rejected') THEN NOW() ELSE reviewed_at END,
        decided_at = CASE WHEN p_new_status IN ('hired', 'rejected', 'withdrawn') THEN NOW() ELSE decided_at END
    WHERE id = p_application_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function: Get job recommendations for candidate
CREATE OR REPLACE FUNCTION get_job_recommendations(
    p_candidate_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    job_id UUID,
    job_title VARCHAR,
    employer_name VARCHAR,
    match_score REAL,
    matching_skills BIGINT,
    total_required_skills BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        j.id,
        j.title,
        e.name,
        (COUNT(DISTINCT cs.skill_id)::REAL / NULLIF(jsonb_array_length(j.skills_required), 0))::REAL AS match_score,
        COUNT(DISTINCT cs.skill_id) AS matching_skills,
        jsonb_array_length(j.skills_required) AS total_required_skills
    FROM jobs j
    JOIN employers e ON j.employer_id = e.id
    LEFT JOIN candidate_skills cs ON cs.candidate_id = p_candidate_id
        AND cs.skill_id = ANY(ARRAY(SELECT jsonb_array_elements_text(j.skills_required)::UUID))
    WHERE j.is_active = TRUE
        AND j.deleted_at IS NULL
        AND (j.expires_at IS NULL OR j.expires_at > NOW())
        AND NOT EXISTS (
            SELECT 1 FROM applications a
            WHERE a.candidate_id = p_candidate_id AND a.job_id = j.id AND a.deleted_at IS NULL
        )
    GROUP BY j.id, j.title, e.name, j.skills_required
    HAVING COUNT(DISTINCT cs.skill_id) > 0
    ORDER BY match_score DESC, j.published_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate candidate match score for a job
CREATE OR REPLACE FUNCTION calculate_candidate_match_score(
    p_candidate_id UUID,
    p_job_id UUID
)
RETURNS NUMERIC(5,2) AS $$
DECLARE
    v_match_score NUMERIC(5,2) := 0;
    v_skill_match NUMERIC(5,2) := 0;
    v_experience_match NUMERIC(5,2) := 0;
    v_location_match NUMERIC(5,2) := 0;
    v_total_weight NUMERIC(5,2) := 0;
    v_candidate_exp NUMERIC;
    v_required_exp NUMERIC;
    v_matching_skills INTEGER;
    v_total_skills INTEGER;
BEGIN
    -- Skill match (50% weight)
    SELECT COUNT(DISTINCT cs.skill_id), array_length(j.skills_required, 1)
    INTO v_matching_skills, v_total_skills
    FROM jobs j
    LEFT JOIN candidate_skills cs ON cs.candidate_id = p_candidate_id
        AND cs.skill_id = ANY(ARRAY(SELECT jsonb_array_elements_text(j.skills_required)::UUID))
    WHERE j.id = p_job_id
    GROUP BY j.skills_required;

    IF v_total_skills > 0 THEN
        v_skill_match := (v_matching_skills::NUMERIC / v_total_skills) * 50;
    END IF;
    v_total_weight := v_total_weight + 50;

    -- Experience match (30% weight)
    SELECT c.years_experience, (j.salary_range->>'min_experience')::NUMERIC
    INTO v_candidate_exp, v_required_exp
    FROM candidates c, jobs j
    WHERE c.id = p_candidate_id AND j.id = p_job_id;

    IF v_candidate_exp IS NOT NULL AND v_required_exp IS NOT NULL THEN
        IF v_candidate_exp >= v_required_exp THEN
            v_experience_match := 30;
        ELSE
            v_experience_match := (v_candidate_exp / NULLIF(v_required_exp, 0)) * 30;
        END IF;
    END IF;
    v_total_weight := v_total_weight + 30;

    -- Location match (20% weight)
    SELECT CASE
        WHEN c.current_location ILIKE '%' || (j.location->>'city') || '%' THEN 20
        WHEN j.is_remote = TRUE THEN 15
        ELSE 0
    END
    INTO v_location_match
    FROM candidates c, jobs j
    WHERE c.id = p_candidate_id AND j.id = p_job_id;
    v_total_weight := v_total_weight + 20;

    v_match_score := ROUND(v_skill_match + v_experience_match + v_location_match, 2);
    RETURN LEAST(v_match_score, 100);
END;
$$ LANGUAGE plpgsql;

-- Function: Get analytics events for a specific time range
CREATE OR REPLACE FUNCTION get_analytics_events(
    p_start_date TIMESTAMPTZ,
    p_end_date TIMESTAMPTZ,
    p_event_type event_type DEFAULT NULL,
    p_limit INTEGER DEFAULT 1000
)
RETURNS TABLE (
    event_id UUID,
    event_type event_type,
    event_name VARCHAR,
    session_id VARCHAR,
    user_id UUID,
    candidate_id UUID,
    employer_id UUID,
    job_id UUID,
    created_at TIMESTAMPTZ,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.id,
        ae.event_type,
        ae.event_name,
        ae.session_id,
        ae.user_id,
        ae.candidate_id,
        ae.employer_id,
        ae.job_id,
        ae.created_at,
        ae.metadata
    FROM analytics_events ae
    WHERE ae.created_at BETWEEN p_start_date AND p_end_date
        AND (p_event_type IS NULL OR ae.event_type = p_event_type)
    ORDER BY ae.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Bulk insert analytics events
CREATE OR REPLACE FUNCTION bulk_insert_analytics_events(
    events JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    INSERT INTO analytics_events (event_type, event_name, session_id, user_id, candidate_id,
                                   employer_id, job_id, application_id, interview_id,
                                   assessment_id, recruiter_id, ip_address, user_agent,
                                   referrer, url, page_title, metadata, properties, created_at)
    SELECT
        (e->>'event_type')::event_type,
        e->>'event_name',
        e->>'session_id',
        (e->>'user_id')::UUID,
        (e->>'candidate_id')::UUID,
        (e->>'employer_id')::UUID,
        (e->>'job_id')::UUID,
        (e->>'application_id')::UUID,
        (e->>'interview_id')::UUID,
        (e->>'assessment_id')::UUID,
        (e->>'recruiter_id')::UUID,
        (e->>'ip_address')::INET,
        e->>'user_agent',
        e->>'referrer',
        e->>'url',
        e->>'page_title',
        COALESCE(e->'metadata', '{}'::jsonb),
        COALESCE(e->'properties', '{}'::jsonb),
        COALESCE((e->>'created_at')::TIMESTAMPTZ, NOW())
    FROM jsonb_array_elements(events) AS e;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Get interview feedback summary
CREATE OR REPLACE FUNCTION get_interview_feedback_summary(p_application_id UUID)
RETURNS TABLE (
    interview_id UUID,
    interview_type interview_type,
    status interview_status,
    scheduled_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    overall_rating INTEGER,
    recommendation VARCHAR,
    feedback JSONB,
    interviewer_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.interview_type,
        i.status,
        i.scheduled_at,
        i.duration_minutes,
        i.overall_rating,
        i.recommendation,
        i.feedback,
        r.first_name || ' ' || r.last_name
    FROM interviews i
    JOIN recruiters r ON i.interviewer_id = r.id
    WHERE i.application_id = p_application_id AND i.deleted_at IS NULL
    ORDER BY i.scheduled_at;
END;
$$ LANGUAGE plpgsql;

-- Function: Archive old analytics events
CREATE OR REPLACE FUNCTION archive_old_analytics_events(
    p_older_than TIMESTAMPTZ
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    -- In production, this would move data to an archive table
    -- For now, just count what would be archived
    SELECT COUNT(*) INTO v_count
    FROM analytics_events
    WHERE created_at < p_older_than;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. TEST DATA VALIDATION — VERIFY SEED DATA INTEGRITY
-- ============================================================================

-- View: Data quality checks
CREATE OR REPLACE VIEW v_data_quality_checks AS
SELECT
    'orphaned_applications' AS check_name,
    COUNT(*) AS issue_count,
    'Applications referencing non-existent candidates or jobs' AS description
FROM applications a
LEFT JOIN candidates c ON a.candidate_id = c.id
LEFT JOIN jobs j ON a.job_id = j.id
WHERE c.id IS NULL OR j.id IS NULL

UNION ALL

SELECT
    'orphaned_interviews',
    COUNT(*),
    'Interviews referencing non-existent applications'
FROM interviews i
LEFT JOIN applications a ON i.application_id = a.id
WHERE a.id IS NULL

UNION ALL

SELECT
    'orphaned_assessments',
    COUNT(*),
    'Assessments referencing non-existent applications'
FROM assessments ass
LEFT JOIN applications a ON ass.application_id = a.id
WHERE a.id IS NULL

UNION ALL

SELECT
    'orphaned_experiences',
    COUNT(*),
    'Experiences referencing non-existent candidates'
FROM experiences e
LEFT JOIN candidates c ON e.candidate_id = c.id
WHERE c.id IS NULL

UNION ALL

SELECT
    'orphaned_education',
    COUNT(*),
    'Education referencing non-existent candidates'
FROM education ed
LEFT JOIN candidates c ON ed.candidate_id = c.id
WHERE c.id IS NULL

UNION ALL

SELECT
    'orphaned_talent_pool_members',
    COUNT(*),
    'Talent pool members referencing non-existent pools or candidates'
FROM talent_pool_members tpm
LEFT JOIN talent_pools tp ON tpm.talent_pool_id = tp.id
LEFT JOIN candidates c ON tpm.candidate_id = c.id
WHERE tp.id IS NULL OR c.id IS NULL

UNION ALL

SELECT
    'duplicate_candidate_emails',
    COUNT(*) - COUNT(DISTINCT email),
    'Duplicate candidate emails'
FROM candidates
WHERE deleted_at IS NULL

UNION ALL

SELECT
    'duplicate_job_slugs',
    COUNT(*) - COUNT(DISTINCT slug),
    'Duplicate job slugs'
FROM jobs
WHERE deleted_at IS NULL

UNION ALL

SELECT
    'invalid_application_ratings',
    COUNT(*),
    'Applications with invalid rating values'
FROM applications
WHERE rating IS NOT NULL AND (rating < 1 OR rating > 5)

UNION ALL

SELECT
    'invalid_interview_ratings',
    COUNT(*),
    'Interviews with invalid overall_rating values'
FROM interviews
WHERE overall_rating IS NOT NULL AND (overall_rating < 1 OR overall_rating > 5)

UNION ALL

SELECT
    'jobs_with_negative_counts',
    COUNT(*),
    'Jobs with negative views_count or applications_count'
FROM jobs
WHERE views_count < 0 OR applications_count < 0

UNION ALL

SELECT
    'experiences_with_invalid_dates',
    COUNT(*),
    'Experiences where end_date is before start_date'
FROM experiences
WHERE end_date IS NOT NULL AND end_date < start_date

UNION ALL

SELECT
    'education_with_invalid_gpa',
    COUNT(*),
    'Education entries with invalid GPA values'
FROM education
WHERE (gpa IS NOT NULL AND (gpa < 0 OR gpa > 4.00))
   OR (max_gpa IS NOT NULL AND (max_gpa < 0 OR max_gpa > 4.00))

UNION ALL

SELECT
    'candidates_with_invalid_completeness',
    COUNT(*),
    'Candidates with profile_completeness outside 0-100'
FROM candidates
WHERE profile_completeness < 0 OR profile_completeness > 100

UNION ALL

SELECT
    'assessments_with_invalid_scores',
    COUNT(*),
    'Assessments with score > max_score'
FROM assessments
WHERE score IS NOT NULL AND max_score IS NOT NULL AND score > max_score;

-- ============================================================================
-- 8. PERFORMANCE BENCHMARK — EXPLAIN ANALYZE ON KEY QUERIES
-- ============================================================================

-- These queries are designed to be run with EXPLAIN ANALYZE to benchmark performance
-- They represent the most common query patterns in the recruitment platform

-- Query 1: Active jobs search with filters
-- EXPLAIN ANALYZE
-- SELECT * FROM v_active_jobs
-- WHERE department = 'Engineering'
-- ORDER BY published_at DESC
-- LIMIT 20;

-- Query 2: Candidate search with full-text and filters
-- EXPLAIN ANALYZE
-- SELECT * FROM search_candidates(
--     p_search_query => 'software engineer',
--     p_location => 'San Francisco',
--     p_min_experience => 3,
--     p_limit => 50
-- );

-- Query 3: Application pipeline for a job
-- EXPLAIN ANALYZE
-- SELECT * FROM mv_job_application_stats
-- WHERE job_id = 'some-uuid';

-- Query 4: Recruiter dashboard
-- EXPLAIN ANALYZE
-- SELECT * FROM get_recruiter_dashboard('some-uuid');

-- Query 5: Candidate full profile
-- EXPLAIN ANALYZE
-- SELECT * FROM get_candidate_full_profile('some-uuid');

-- Query 6: Analytics events for date range
-- EXPLAIN ANALYZE
-- SELECT * FROM get_analytics_events(
--     p_start_date => NOW() - INTERVAL '7 days',
--     p_end_date => NOW(),
--     p_event_type => 'job_view'
-- );

-- Query 7: Job recommendations
-- EXPLAIN ANALYZE
-- SELECT * FROM get_job_recommendations('some-uuid', 10);

-- Query 8: Data quality check
-- EXPLAIN ANALYZE
-- SELECT * FROM v_data_quality_checks;

-- ============================================================================
-- END OF OPTIMIZATIONS
-- ============================================================================
