-- =============================================================================
-- Gated Communities — Additional Database Optimizations
-- =============================================================================
-- Complements optimizations.sql with missing indexes, extended partitioning,
-- and additional constraints. Does not repeat existing patterns.
-- =============================================================================

BEGIN;

-- =============================================================================
-- 1. QUERY OPTIMIZATION — Missing Indexes (12)
-- =============================================================================

-- Composite index for filtered content feeds by type
CREATE INDEX idx_content_community_type_status_published
    ON content (community_id, content_type, status, published_at DESC)
    WHERE deleted_at IS NULL;

-- Index for comment thread traversal
CREATE INDEX idx_content_parent_created
    ON content (parent_id, created_at)
    WHERE deleted_at IS NULL AND parent_id IS NOT NULL;

-- Composite index for role-based member queries
CREATE INDEX idx_members_community_role_status
    ON members (community_id, role, status)
    WHERE deleted_at IS NULL;

-- Index for tier member lists
CREATE INDEX idx_members_tier_status
    ON members (tier_id, status)
    WHERE deleted_at IS NULL AND tier_id IS NOT NULL;

-- Index for price-sorted tier listings
CREATE INDEX idx_tiers_community_price
    ON tiers (community_id, price_cents)
    WHERE deleted_at IS NULL;

-- Index for moderation history per community
CREATE INDEX idx_moderation_community_type_created
    ON moderation_actions (community_id, action_type, created_at DESC);

-- FK index for moderation_actions.reversed_by
CREATE INDEX idx_moderation_reversed_by
    ON moderation_actions (reversed_by)
    WHERE reversed_by IS NOT NULL;

-- Index for assigned escalation queue
CREATE INDEX idx_escalations_assigned_status
    ON escalations (assigned_to, status)
    WHERE deleted_at IS NULL AND assigned_to IS NOT NULL;

-- FK index for escalations.resolved_by
CREATE INDEX idx_escalations_resolved_by
    ON escalations (resolved_by)
    WHERE resolved_by IS NOT NULL;

-- Composite index for filtered compliance queries
CREATE INDEX idx_compliance_community_type_status
    ON compliance_reports (community_id, report_type, status)
    WHERE deleted_at IS NULL;

-- Index for per-user analytics queries
CREATE INDEX idx_analytics_community_user_created
    ON analytics_events (community_id, user_id, created_at DESC);

-- Index for audit filtering by action
CREATE INDEX idx_audit_table_action_created
    ON audit_log (table_name, action, created_at DESC);

-- =============================================================================
-- 2. PARTITIONING — Analytics Events (12 new partitions for 2029)
-- =============================================================================

CREATE TABLE IF NOT EXISTS analytics_events_2029_01 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-01-01') TO ('2029-02-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_02 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-02-01') TO ('2029-03-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_03 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-03-01') TO ('2029-04-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_04 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-04-01') TO ('2029-05-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_05 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-05-01') TO ('2029-06-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_06 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-06-01') TO ('2029-07-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_07 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-07-01') TO ('2029-08-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_08 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-08-01') TO ('2029-09-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_09 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-09-01') TO ('2029-10-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_10 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-10-01') TO ('2029-11-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_11 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-11-01') TO ('2029-12-01');
CREATE TABLE IF NOT EXISTS analytics_events_2029_12 PARTITION OF analytics_events
    FOR VALUES FROM ('2029-12-01') TO ('2030-01-01');

-- =============================================================================
-- 3. CONSTRAINTS — CHECK & UNIQUE (9)
-- =============================================================================

-- Communities: deleted_at must be after created_at
ALTER TABLE communities ADD CONSTRAINT chk_communities_deleted_after_created
    CHECK (deleted_at IS NULL OR deleted_at > created_at);

-- Tiers: deleted_at must be after created_at
ALTER TABLE tiers ADD CONSTRAINT chk_tiers_deleted_after_created
    CHECK (deleted_at IS NULL OR deleted_at > created_at);

-- Members: invited_at must be set when status is 'invited'
ALTER TABLE members ADD CONSTRAINT chk_members_invited_has_timestamp
    CHECK (status != 'invited' OR invited_at IS NOT NULL);

-- Members: banned_reason must be set when status is 'banned'
ALTER TABLE members ADD CONSTRAINT chk_members_banned_has_reason
    CHECK (status != 'banned' OR banned_reason IS NOT NULL);

-- Content: edited_at must be after published_at when both set
ALTER TABLE content ADD CONSTRAINT chk_content_edited_after_published
    CHECK (edited_at IS NULL OR published_at IS NULL OR edited_at >= published_at);

-- Moderation actions: reversal_reason must be set when status is 'reversed'
ALTER TABLE moderation_actions ADD CONSTRAINT chk_moderation_reversed_has_reason
    CHECK (status != 'reversed' OR reversal_reason IS NOT NULL);

-- Escalations: resolution_notes must be set when status is 'resolved'
ALTER TABLE escalations ADD CONSTRAINT chk_escalations_resolved_has_notes
    CHECK (status != 'resolved' OR resolution_notes IS NOT NULL);

-- Compliance reports: review_notes must be set when status is 'fulfilled' or 'rejected'
ALTER TABLE compliance_reports ADD CONSTRAINT chk_compliance_reviewed_has_notes
    CHECK (status NOT IN ('fulfilled', 'rejected') OR review_notes IS NOT NULL);

-- Analytics events: prevent duplicate events (same user, type, timestamp)
CREATE UNIQUE INDEX IF NOT EXISTS uq_analytics_dedup
    ON analytics_events (community_id, user_id, event_type, created_at);

COMMIT;
