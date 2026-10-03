-- ============================================================================
-- Recruitment Platform Database — Additional Optimizations
-- PostgreSQL 16+
-- ============================================================================

-- ============================================================================
-- 1. QUERY OPTIMIZATION — MISSING INDEXES
-- ============================================================================

-- Jobs: filter by location_type (onsite/remote/hybrid)
CREATE INDEX IF NOT EXISTS idx_jobs_location_type
    ON jobs (location_type)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- Jobs: urgent job filtering
CREATE INDEX IF NOT EXISTS idx_jobs_is_urgent
    ON jobs (is_urgent)
    WHERE is_urgent = TRUE AND deleted_at IS NULL;

-- Applications: filter by rejection category
CREATE INDEX IF NOT EXISTS idx_applications_rejection_category
    ON applications (rejection_category)
    WHERE deleted_at IS NULL;

-- Interviews: find interviews needing reminders
CREATE INDEX IF NOT EXISTS idx_interviews_reminder_sent_at
    ON interviews (reminder_sent_at)
    WHERE reminder_sent_at IS NULL AND status IN ('scheduled', 'confirmed');

-- Assessments: timing analysis
CREATE INDEX IF NOT EXISTS idx_assessments_started_at
    ON assessments (started_at)
    WHERE started_at IS NOT NULL;

-- Talent pools: active pools by employer
CREATE INDEX IF NOT EXISTS idx_talent_pools_employer_active
    ON talent_pools (employer_id, is_active)
    WHERE deleted_at IS NULL;

-- Candidates: referral code lookups
CREATE INDEX IF NOT EXISTS idx_candidates_referral_code
    ON candidates (referral_code)
    WHERE referral_code IS NOT NULL;

-- Applications: referral code lookups
CREATE INDEX IF NOT EXISTS idx_applications_referral_code
    ON applications (referral_code)
    WHERE referral_code IS NOT NULL;

-- Analytics events: recruiter-specific queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_recruiter_id
    ON analytics_events (recruiter_id);

-- Analytics events: interview-related queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_interview_id
    ON analytics_events (interview_id);

-- Analytics events: assessment-related queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_assessment_id
    ON analytics_events (assessment_id);

-- Audit log: filter by performer type
CREATE INDEX IF NOT EXISTS idx_audit_log_performed_by_type
    ON audit_log (performed_by_type);

-- ============================================================================
-- 2. PARTITIONING — AUTOMATIC PARTITION MANAGEMENT
-- ============================================================================

-- Function to create future partitions for analytics_events
CREATE OR REPLACE FUNCTION create_analytics_partitions(
    p_months_ahead INTEGER DEFAULT 12
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_start_date DATE;
    v_end_date DATE;
    v_partition_name TEXT;
BEGIN
    FOR i IN 1..p_months_ahead LOOP
        v_start_date := DATE_TRUNC('month', NOW() + (i || ' months')::INTERVAL);
        v_end_date := v_start_date + INTERVAL '1 month';
        v_partition_name := 'analytics_events_' || TO_CHAR(v_start_date, 'YYYY_MM');

        IF NOT EXISTS (
            SELECT 1 FROM pg_tables WHERE tablename = v_partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF analytics_events FOR VALUES FROM (%L) TO (%L)',
                v_partition_name, v_start_date, v_end_date
            );
            v_count := v_count + 1;
        END IF;
    END LOOP;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. CONSTRAINTS — CHECK AND UNIQUE CONSTRAINTS
-- ============================================================================

-- Employers: name must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_employers_name_not_empty'
    ) THEN
        ALTER TABLE employers ADD CONSTRAINT chk_employers_name_not_empty
            CHECK (name <> '');
    END IF;
END $$;

-- Jobs: title must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_title_not_empty'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_title_not_empty
            CHECK (title <> '');
    END IF;
END $$;

-- Jobs: description must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_jobs_description_not_empty'
    ) THEN
        ALTER TABLE jobs ADD CONSTRAINT chk_jobs_description_not_empty
            CHECK (description <> '');
    END IF;
END $$;

-- Candidates: first_name must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_first_name_not_empty'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_first_name_not_empty
            CHECK (first_name <> '');
    END IF;
END $$;

-- Candidates: last_name must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_candidates_last_name_not_empty'
    ) THEN
        ALTER TABLE candidates ADD CONSTRAINT chk_candidates_last_name_not_empty
            CHECK (last_name <> '');
    END IF;
END $$;

-- Interviews: timezone must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_interviews_timezone_not_empty'
    ) THEN
        ALTER TABLE interviews ADD CONSTRAINT chk_interviews_timezone_not_empty
            CHECK (timezone <> '');
    END IF;
END $$;

-- Assessments: title must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_assessments_title_not_empty'
    ) THEN
        ALTER TABLE assessments ADD CONSTRAINT chk_assessments_title_not_empty
            CHECK (title <> '');
    END IF;
END $$;

-- Talent pools: name must not be empty
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_talent_pools_name_not_empty'
    ) THEN
        ALTER TABLE talent_pools ADD CONSTRAINT chk_talent_pools_name_not_empty
            CHECK (name <> '');
    END IF;
END $$;

-- Applications: rejection_reason required when status is 'rejected'
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_applications_rejection_reason_required'
    ) THEN
        ALTER TABLE applications ADD CONSTRAINT chk_applications_rejection_reason_required
            CHECK (status <> 'rejected' OR rejection_reason IS NOT NULL);
    END IF;
END $$;

-- Interviews: no_show_reason required when status is 'no_show'
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_interviews_no_show_reason_required'
    ) THEN
        ALTER TABLE interviews ADD CONSTRAINT chk_interviews_no_show_reason_required
            CHECK (status <> 'no_show' OR no_show_reason IS NOT NULL);
    END IF;
END $$;

-- ============================================================================
-- END OF ADDITIONAL OPTIMIZATIONS
-- ============================================================================
