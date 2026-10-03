-- =============================================================================
-- Gated Communities — Database Optimizations
-- =============================================================================
-- Applied on top of schema.sql for query optimization, partitioning,
-- constraints, triggers, materialized views, and stored procedures.
-- =============================================================================

BEGIN;

-- =============================================================================
-- 1. QUERY OPTIMIZATION — Missing Indexes
-- =============================================================================

-- Composite index for member lookups by community + status (common filter)
CREATE INDEX idx_members_community_status ON members (community_id, status) WHERE deleted_at IS NULL;

-- Composite index for content feed queries (community + status + published_at)
CREATE INDEX idx_content_community_status_published ON content (community_id, status, published_at DESC) WHERE deleted_at IS NULL;

-- Composite index for content by author + status
CREATE INDEX idx_content_author_status ON content (author_id, status) WHERE deleted_at IS NULL;

-- Index for tier lookups by community + active status
CREATE INDEX idx_tiers_community_active ON tiers (community_id, is_active) WHERE deleted_at IS NULL;

-- Index for moderation actions by community + status
CREATE INDEX idx_moderation_community_status ON moderation_actions (community_id, status);

-- Index for moderation actions by target member
CREATE INDEX idx_moderation_target_member_status ON moderation_actions (target_member_id, status);

-- Index for escalations by community + status + priority
CREATE INDEX idx_escalations_community_status_priority ON escalations (community_id, status, priority) WHERE deleted_at IS NULL;

-- Index for compliance reports by community + status
CREATE INDEX idx_compliance_community_status ON compliance_reports (community_id, status) WHERE deleted_at IS NULL;

-- Index for analytics events by event_type + created_at (time-series queries)
CREATE INDEX idx_analytics_event_type_created ON analytics_events (event_type, created_at DESC);

-- Index for analytics events by user_id + created_at
CREATE INDEX idx_analytics_user_created ON analytics_events (user_id, created_at DESC);

-- Index for audit_log by table_name + created_at (recent changes queries)
CREATE INDEX idx_audit_table_created ON audit_log (table_name, created_at DESC);

-- Index for audit_log by performed_by + created_at
CREATE INDEX idx_audit_performed_by_created ON audit_log (performed_by, created_at DESC);

-- GIN index for content body full-text search (if not using search_vector)
-- Note: search_vector already exists, this is for ad-hoc body searches
CREATE INDEX idx_content_body_gin ON content USING GIN (to_tsvector('english', body));

-- GIN index for communities description
CREATE INDEX idx_communities_description_gin ON communities USING GIN (to_tsvector('english', description));

-- Index for members joined_at (sorting by join date)
CREATE INDEX idx_members_joined_at ON members (joined_at DESC) WHERE deleted_at IS NULL;

-- Index for content edited_at (recently edited content)
CREATE INDEX idx_content_edited_at ON content (edited_at DESC) WHERE deleted_at IS NULL AND edited_at IS NOT NULL;

-- Index for reputation scores by community + score (leaderboard queries)
CREATE INDEX idx_reputation_community_score ON reputation_scores (community_id, score DESC);

-- Index for escalations due_at (overdue escalations)
CREATE INDEX idx_escalations_due_at_status ON escalations (due_at) WHERE deleted_at IS NULL AND status IN ('open', 'investigating');

-- Index for compliance reports by report_type + status
CREATE INDEX idx_compliance_type_status ON compliance_reports (report_type, status) WHERE deleted_at IS NULL;

-- Index for analytics events by session_id + created_at
CREATE INDEX idx_analytics_session_created ON analytics_events (session_id, created_at DESC);

-- Partial index for active members only (most common query pattern)
CREATE INDEX idx_members_active ON members (community_id, user_id) WHERE deleted_at IS NULL AND status = 'active';

-- Partial index for published content only
CREATE INDEX idx_content_published ON content (community_id, published_at DESC) WHERE deleted_at IS NULL AND status = 'published';

-- Partial index for active tiers only
CREATE INDEX idx_tiers_active ON tiers (community_id, sort_order) WHERE deleted_at IS NULL AND is_active = true;

-- =============================================================================
-- 2. PARTITIONING — Analytics Events (already partitioned, add future partitions)
-- =============================================================================

-- Create partitions for 2028 (extend coverage)
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

-- =============================================================================
-- 3. CONSTRAINTS — CHECK and UNIQUE Constraints
-- =============================================================================

-- Communities: ensure slug is lowercase URL-friendly
ALTER TABLE communities ADD CONSTRAINT chk_communities_slug_format
    CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$');

-- Communities: ensure member_count matches actual count (deferred check via trigger)
-- Communities: ensure content_count matches actual count (deferred check via trigger)

-- Tiers: ensure currency is valid ISO 4217 (3 uppercase letters)
ALTER TABLE tiers ADD CONSTRAINT chk_tiers_currency_format
    CHECK (currency ~ '^[A-Z]{3}$');

-- Tiers: ensure sort_order is non-negative
ALTER TABLE tiers ADD CONSTRAINT chk_tiers_sort_order CHECK (sort_order >= 0);

-- Members: ensure joined_at is before or equal to last_active_at
ALTER TABLE members ADD CONSTRAINT chk_members_joined_before_active
    CHECK (joined_at IS NULL OR last_active_at IS NULL OR joined_at <= last_active_at);

-- Members: ensure banned_at is set when status is banned
ALTER TABLE members ADD CONSTRAINT chk_members_banned_has_timestamp
    CHECK (status != 'banned' OR banned_at IS NOT NULL);

-- Members: ensure tier_expires_at is in the future when set
ALTER TABLE members ADD CONSTRAINT chk_members_tier_expires_future
    CHECK (tier_expires_at IS NULL OR tier_expires_at > created_at);

-- Content: ensure published_at is set when status is published
ALTER TABLE content ADD CONSTRAINT chk_content_published_has_timestamp
    CHECK (status NOT IN ('published', 'edited') OR published_at IS NOT NULL);

-- Content: ensure edited_at is set when status is edited
ALTER TABLE content ADD CONSTRAINT chk_content_edited_has_timestamp
    CHECK (status != 'edited' OR edited_at IS NOT NULL);

-- Content: ensure parent_id is set for comments and replies
ALTER TABLE content ADD CONSTRAINT chk_content_parent_required
    CHECK (content_type NOT IN ('comment', 'reply') OR parent_id IS NOT NULL);

-- Content: ensure title is set for posts
ALTER TABLE content ADD CONSTRAINT chk_content_post_has_title
    CHECK (content_type != 'post' OR title IS NOT NULL);

-- Moderation actions: ensure expires_at is set when duration_hours is set
ALTER TABLE moderation_actions ADD CONSTRAINT chk_moderation_duration_has_expiry
    CHECK (duration_hours IS NULL OR expires_at IS NOT NULL);

-- Moderation actions: ensure applied_at is set when status is applied
ALTER TABLE moderation_actions ADD CONSTRAINT chk_moderation_applied_has_timestamp
    CHECK (status != 'applied' OR applied_at IS NOT NULL);

-- Moderation actions: ensure reversed_at is set when status is reversed
ALTER TABLE moderation_actions ADD CONSTRAINT chk_moderation_reversed_has_timestamp
    CHECK (status != 'reversed' OR reversed_at IS NOT NULL);

-- Reputation scores: ensure score equals total_earned minus total_deducted
ALTER TABLE reputation_scores ADD CONSTRAINT chk_reputation_score_consistency
    CHECK (score = total_earned - total_deducted);

-- Escalations: ensure resolved_at is set when status is resolved
ALTER TABLE escalations ADD CONSTRAINT chk_escalations_resolved_has_timestamp
    CHECK (status != 'resolved' OR resolved_at IS NOT NULL);

-- Escalations: ensure due_at is after created_at
ALTER TABLE escalations ADD CONSTRAINT chk_escalations_due_after_created
    CHECK (due_at IS NULL OR due_at > created_at);

-- Compliance reports: ensure reviewed_at is set when status is not pending
ALTER TABLE compliance_reports ADD CONSTRAINT chk_compliance_reviewed_has_timestamp
    CHECK (status = 'pending' OR reviewed_at IS NOT NULL);

-- Compliance reports: ensure external_ref is unique when not null
CREATE UNIQUE INDEX IF NOT EXISTS uq_compliance_external_ref
    ON compliance_reports (external_ref) WHERE external_ref IS NOT NULL;

-- Analytics events: ensure created_at is not in the future (with 1 minute tolerance)
-- Note: Cannot use now() in CHECK constraint (not immutable)
-- Use a trigger instead for this validation
CREATE OR REPLACE FUNCTION validate_analytics_created_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.created_at > now() + interval '1 minute' THEN
        RAISE EXCEPTION 'created_at cannot be in the future';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_analytics_created_at
    BEFORE INSERT OR UPDATE ON analytics_events
    FOR EACH ROW EXECUTE FUNCTION validate_analytics_created_at();

-- =============================================================================
-- 4. TRIGGERS — Audit Triggers for Additional Tables
-- =============================================================================

-- Apply audit triggers to tiers and reputation_scores (not covered in original)
CREATE TRIGGER trg_audit_tiers
    AFTER INSERT OR UPDATE OR DELETE ON tiers
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_reputation_scores
    AFTER INSERT OR UPDATE OR DELETE ON reputation_scores
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Trigger to auto-update community member_count when members change
CREATE OR REPLACE FUNCTION update_community_member_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE communities SET member_count = member_count + 1 WHERE id = NEW.community_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE communities SET member_count = member_count - 1 WHERE id = OLD.community_id;
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' AND OLD.community_id IS DISTINCT FROM NEW.community_id THEN
        UPDATE communities SET member_count = member_count - 1 WHERE id = OLD.community_id;
        UPDATE communities SET member_count = member_count + 1 WHERE id = NEW.community_id;
        RETURN NEW;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_members_count
    AFTER INSERT OR UPDATE OR DELETE ON members
    FOR EACH ROW EXECUTE FUNCTION update_community_member_count();

-- Trigger to auto-update community content_count when content changes
CREATE OR REPLACE FUNCTION update_community_content_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE communities SET content_count = content_count + 1 WHERE id = NEW.community_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE communities SET content_count = content_count - 1 WHERE id = OLD.community_id;
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' AND OLD.community_id IS DISTINCT FROM NEW.community_id THEN
        UPDATE communities SET content_count = content_count - 1 WHERE id = OLD.community_id;
        UPDATE communities SET content_count = content_count + 1 WHERE id = NEW.community_id;
        RETURN NEW;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_content_count
    AFTER INSERT OR UPDATE OR DELETE ON content
    FOR EACH ROW EXECUTE FUNCTION update_community_content_count();

-- Trigger to auto-update tier subscriber_count when members change tier
CREATE OR REPLACE FUNCTION update_tier_subscriber_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.tier_id IS NOT NULL THEN
        UPDATE tiers SET subscriber_count = subscriber_count + 1 WHERE id = NEW.tier_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' AND OLD.tier_id IS NOT NULL THEN
        UPDATE tiers SET subscriber_count = subscriber_count - 1 WHERE id = OLD.tier_id;
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.tier_id IS DISTINCT FROM NEW.tier_id THEN
            IF OLD.tier_id IS NOT NULL THEN
                UPDATE tiers SET subscriber_count = subscriber_count - 1 WHERE id = OLD.tier_id;
            END IF;
            IF NEW.tier_id IS NOT NULL THEN
                UPDATE tiers SET subscriber_count = subscriber_count + 1 WHERE id = NEW.tier_id;
            END IF;
        END IF;
        RETURN NEW;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tier_subscribers
    AFTER INSERT OR UPDATE OR DELETE ON members
    FOR EACH ROW EXECUTE FUNCTION update_tier_subscriber_count();

-- Trigger to prevent deletion of community owner
CREATE OR REPLACE FUNCTION prevent_owner_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role = 'owner' THEN
        RAISE EXCEPTION 'Cannot delete community owner. Transfer ownership first.';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_owner_delete
    BEFORE DELETE ON members
    FOR EACH ROW EXECUTE FUNCTION prevent_owner_deletion();

-- Trigger to prevent self-demotion of community owner
CREATE OR REPLACE FUNCTION prevent_owner_demotion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role = 'owner' AND NEW.role != 'owner' THEN
        RAISE EXCEPTION 'Cannot demote community owner. Transfer ownership first.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_owner_demotion
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION prevent_owner_demotion();

-- =============================================================================
-- 5. VIEWS — Materialized Views for Common Queries
-- =============================================================================

-- Materialized view: Community statistics (refreshed periodically)
CREATE MATERIALIZED VIEW mv_community_stats AS
SELECT
    c.id AS community_id,
    c.slug,
    c.name,
    c.visibility,
    c.status,
    COUNT(DISTINCT m.id) FILTER (WHERE m.deleted_at IS NULL) AS total_members,
    COUNT(DISTINCT m.id) FILTER (WHERE m.deleted_at IS NULL AND m.status = 'active') AS active_members,
    COUNT(DISTINCT m.id) FILTER (WHERE m.deleted_at IS NULL AND m.status = 'banned') AS banned_members,
    COUNT(DISTINCT t.id) FILTER (WHERE t.deleted_at IS NULL) AS total_tiers,
    COUNT(DISTINCT t.id) FILTER (WHERE t.deleted_at IS NULL AND t.is_active = true) AS active_tiers,
    COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL) AS total_content,
    COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL AND ct.status = 'published') AS published_content,
    COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL AND ct.status = 'draft') AS draft_content,
    COALESCE(SUM(ct.like_count) FILTER (WHERE ct.deleted_at IS NULL), 0) AS total_likes,
    COALESCE(SUM(ct.comment_count) FILTER (WHERE ct.deleted_at IS NULL), 0) AS total_comments,
    COALESCE(SUM(ct.view_count) FILTER (WHERE ct.deleted_at IS NULL), 0) AS total_views,
    c.created_at,
    c.updated_at
FROM communities c
LEFT JOIN members m ON m.community_id = c.id
LEFT JOIN tiers t ON t.community_id = c.id
LEFT JOIN content ct ON ct.community_id = c.id
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.slug, c.name, c.visibility, c.status, c.created_at, c.updated_at;

CREATE UNIQUE INDEX idx_mv_community_stats_id ON mv_community_stats (community_id);
CREATE INDEX idx_mv_community_stats_visibility ON mv_community_stats (visibility);
CREATE INDEX idx_mv_community_stats_status ON mv_community_stats (status);

-- Materialized view: Member leaderboard per community
CREATE MATERIALIZED VIEW mv_member_leaderboard AS
SELECT
    rs.community_id,
    c.slug AS community_slug,
    rs.member_id,
    m.display_name,
    m.user_id,
    rs.score,
    rs.total_earned,
    rs.total_deducted,
    rs.breakdown,
    rs.last_event_at,
    RANK() OVER (PARTITION BY rs.community_id ORDER BY rs.score DESC) AS rank,
    DENSE_RANK() OVER (PARTITION BY rs.community_id ORDER BY rs.score DESC) AS dense_rank,
    PERCENT_RANK() OVER (PARTITION BY rs.community_id ORDER BY rs.score DESC) AS percentile_rank
FROM reputation_scores rs
JOIN communities c ON c.id = rs.community_id
JOIN members m ON m.id = rs.member_id
WHERE m.deleted_at IS NULL;

CREATE UNIQUE INDEX idx_mv_leaderboard_community_member ON mv_member_leaderboard (community_id, member_id);
CREATE INDEX idx_mv_leaderboard_community_rank ON mv_member_leaderboard (community_id, rank);

-- Materialized view: Content performance metrics
CREATE MATERIALIZED VIEW mv_content_performance AS
SELECT
    ct.id AS content_id,
    ct.community_id,
    c.slug AS community_slug,
    ct.author_id,
    m.display_name AS author_name,
    ct.content_type,
    ct.status,
    ct.title,
    ct.like_count,
    ct.comment_count,
    ct.share_count,
    ct.view_count,
    ct.is_pinned,
    ct.published_at,
    ct.created_at,
    CASE WHEN ct.view_count > 0 THEN ROUND(ct.like_count::numeric / ct.view_count, 4) ELSE 0 END AS like_rate,
    CASE WHEN ct.view_count > 0 THEN ROUND(ct.comment_count::numeric / ct.view_count, 4) ELSE 0 END AS comment_rate,
    CASE WHEN ct.view_count > 0 THEN ROUND(ct.share_count::numeric / ct.view_count, 4) ELSE 0 END AS share_rate
FROM content ct
JOIN communities c ON c.id = ct.community_id
JOIN members m ON m.id = ct.author_id
WHERE ct.deleted_at IS NULL;

CREATE UNIQUE INDEX idx_mv_content_performance_id ON mv_content_performance (content_id);
CREATE INDEX idx_mv_content_performance_community ON mv_content_performance (community_id);
CREATE INDEX idx_mv_content_performance_author ON mv_content_performance (author_id);
CREATE INDEX idx_mv_content_performance_published ON mv_content_performance (published_at DESC);

-- Materialized view: Moderation summary per community
CREATE MATERIALIZED VIEW mv_moderation_summary AS
SELECT
    ma.community_id,
    c.slug AS community_slug,
    COUNT(*) AS total_actions,
    COUNT(*) FILTER (WHERE ma.status = 'pending') AS pending_actions,
    COUNT(*) FILTER (WHERE ma.status = 'applied') AS applied_actions,
    COUNT(*) FILTER (WHERE ma.status = 'reversed') AS reversed_actions,
    COUNT(*) FILTER (WHERE ma.action_type = 'warn') AS warn_count,
    COUNT(*) FILTER (WHERE ma.action_type = 'mute') AS mute_count,
    COUNT(*) FILTER (WHERE ma.action_type = 'ban') AS ban_count,
    COUNT(*) FILTER (WHERE ma.action_type = 'content_remove') AS content_removals,
    COUNT(DISTINCT ma.target_member_id) AS unique_members_actioned,
    COUNT(DISTINCT ma.applied_by) AS unique_moderators,
    MAX(ma.created_at) AS last_action_at
FROM moderation_actions ma
JOIN communities c ON c.id = ma.community_id
GROUP BY ma.community_id, c.slug;

CREATE UNIQUE INDEX idx_mv_moderation_summary_community ON mv_moderation_summary (community_id);

-- Materialized view: Analytics daily summary
CREATE MATERIALIZED VIEW mv_analytics_daily AS
SELECT
    community_id,
    event_type,
    DATE(created_at) AS event_date,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM analytics_events
GROUP BY community_id, event_type, DATE(created_at);

CREATE UNIQUE INDEX idx_mv_analytics_daily ON mv_analytics_daily (community_id, event_type, event_date);
CREATE INDEX idx_mv_analytics_daily_date ON mv_analytics_daily (event_date DESC);
CREATE INDEX idx_mv_analytics_daily_community ON mv_analytics_daily (community_id);

-- =============================================================================
-- 6. FUNCTIONS — Stored Procedures for Complex Operations
-- =============================================================================

-- Function: Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_community_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_member_leaderboard;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_content_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_moderation_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_analytics_daily;
END;
$$ LANGUAGE plpgsql;

-- Function: Get community dashboard data
CREATE OR REPLACE FUNCTION get_community_dashboard(p_community_id UUID)
RETURNS TABLE (
    community_id UUID,
    slug VARCHAR,
    name VARCHAR,
    visibility community_visibility,
    status community_status,
    total_members BIGINT,
    active_members BIGINT,
    total_tiers BIGINT,
    active_tiers BIGINT,
    total_content BIGINT,
    published_content BIGINT,
    total_likes BIGINT,
    total_comments BIGINT,
    total_views BIGINT,
    recent_members JSONB,
    recent_content JSONB,
    top_members JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH recent_m AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'id', m.id,
                'display_name', m.display_name,
                'role', m.role,
                'joined_at', m.joined_at
            ) ORDER BY m.joined_at DESC
        ) AS members
        FROM members m
        WHERE m.community_id = p_community_id AND m.deleted_at IS NULL
        ORDER BY m.joined_at DESC
        LIMIT 5
    ),
    recent_c AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'id', ct.id,
                'title', ct.title,
                'content_type', ct.content_type,
                'author', m.display_name,
                'published_at', ct.published_at
            ) ORDER BY ct.published_at DESC
        ) AS content
        FROM content ct
        JOIN members m ON m.id = ct.author_id
        WHERE ct.community_id = p_community_id AND ct.deleted_at IS NULL AND ct.status = 'published'
        ORDER BY ct.published_at DESC
        LIMIT 5
    ),
    top_m AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'member_id', rs.member_id,
                'display_name', m.display_name,
                'score', rs.score
            ) ORDER BY rs.score DESC
        ) AS members
        FROM reputation_scores rs
        JOIN members m ON m.id = rs.member_id
        WHERE rs.community_id = p_community_id AND m.deleted_at IS NULL
        ORDER BY rs.score DESC
        LIMIT 5
    )
    SELECT
        c.id,
        c.slug,
        c.name,
        c.visibility,
        c.status,
        COUNT(DISTINCT m.id) FILTER (WHERE m.deleted_at IS NULL),
        COUNT(DISTINCT m.id) FILTER (WHERE m.deleted_at IS NULL AND m.status = 'active'),
        COUNT(DISTINCT t.id) FILTER (WHERE t.deleted_at IS NULL),
        COUNT(DISTINCT t.id) FILTER (WHERE t.deleted_at IS NULL AND t.is_active = true),
        COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL),
        COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL AND ct.status = 'published'),
        COALESCE(SUM(ct.like_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COALESCE(SUM(ct.comment_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COALESCE(SUM(ct.view_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COALESCE((SELECT members FROM recent_m), '[]'::jsonb),
        COALESCE((SELECT content FROM recent_c), '[]'::jsonb),
        COALESCE((SELECT members FROM top_m), '[]'::jsonb)
    FROM communities c
    LEFT JOIN members m ON m.community_id = c.id
    LEFT JOIN tiers t ON t.community_id = c.id
    LEFT JOIN content ct ON ct.community_id = c.id
    WHERE c.id = p_community_id AND c.deleted_at IS NULL
    GROUP BY c.id, c.slug, c.name, c.visibility, c.status;
END;
$$ LANGUAGE plpgsql;

-- Function: Search content with full-text search
CREATE OR REPLACE FUNCTION search_content(
    p_query TEXT,
    p_community_id UUID DEFAULT NULL,
    p_content_type content_type DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    content_id UUID,
    community_id UUID,
    community_slug VARCHAR,
    author_name VARCHAR,
    content_type content_type,
    title VARCHAR,
    body_excerpt TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ct.id,
        ct.community_id,
        c.slug,
        m.display_name,
        ct.content_type,
        ct.title,
        LEFT(ct.body, 200) AS body_excerpt,
        ts_rank(ct.search_vector, plainto_tsquery('english', p_query)) AS rank
    FROM content ct
    JOIN communities c ON c.id = ct.community_id
    JOIN members m ON m.id = ct.author_id
    WHERE ct.deleted_at IS NULL
      AND ct.status = 'published'
      AND ct.search_vector @@ plainto_tsquery('english', p_query)
      AND (p_community_id IS NULL OR ct.community_id = p_community_id)
      AND (p_content_type IS NULL OR ct.content_type = p_content_type)
    ORDER BY rank DESC, ct.published_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function: Get member activity summary
CREATE OR REPLACE FUNCTION get_member_activity_summary(
    p_member_id UUID,
    p_community_id UUID DEFAULT NULL
)
RETURNS TABLE (
    member_id UUID,
    community_id UUID,
    community_slug VARCHAR,
    display_name VARCHAR,
    role member_role,
    status member_status,
    joined_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ,
    reputation_score INTEGER,
    total_content BIGINT,
    total_likes_received BIGINT,
    total_comments_received BIGINT,
    total_views_received BIGINT,
    moderation_actions_received BIGINT,
    escalation_reports BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.community_id,
        c.slug,
        m.display_name,
        m.role,
        m.status,
        m.joined_at,
        m.last_active_at,
        rs.score,
        COUNT(DISTINCT ct.id) FILTER (WHERE ct.deleted_at IS NULL),
        COALESCE(SUM(ct.like_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COALESCE(SUM(ct.comment_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COALESCE(SUM(ct.view_count) FILTER (WHERE ct.deleted_at IS NULL), 0),
        COUNT(DISTINCT ma.id) FILTER (WHERE ma.target_member_id = m.id),
        COUNT(DISTINCT e.id) FILTER (WHERE e.reporter_id = m.id AND e.deleted_at IS NULL)
    FROM members m
    JOIN communities c ON c.id = m.community_id
    LEFT JOIN reputation_scores rs ON rs.member_id = m.id AND rs.community_id = m.community_id
    LEFT JOIN content ct ON ct.author_id = m.id
    LEFT JOIN moderation_actions ma ON ma.target_member_id = m.id
    LEFT JOIN escalations e ON e.reporter_id = m.id
    WHERE m.id = p_member_id
      AND m.deleted_at IS NULL
      AND (p_community_id IS NULL OR m.community_id = p_community_id)
    GROUP BY m.id, m.community_id, c.slug, m.display_name, m.role, m.status,
             m.joined_at, m.last_active_at, rs.score;
END;
$$ LANGUAGE plpgsql;

-- Function: Apply moderation action with validation
CREATE OR REPLACE FUNCTION apply_moderation_action(
    p_community_id UUID,
    p_target_member_id UUID,
    p_target_content_id UUID DEFAULT NULL,
    p_action_type moderation_action_type,
    p_reason TEXT,
    p_details JSONB DEFAULT '{}'::jsonb,
    p_duration_hours INTEGER DEFAULT NULL,
    p_applied_by UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_action_id UUID;
    v_expires_at TIMESTAMPTZ;
BEGIN
    -- Validate target member exists and is in the community
    IF NOT EXISTS (
        SELECT 1 FROM members
        WHERE id = p_target_member_id AND community_id = p_community_id AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Target member not found in community';
    END IF;

    -- Validate applied_by is a moderator or admin
    IF p_applied_by IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM members
        WHERE id = p_applied_by AND community_id = p_community_id
          AND role IN ('owner', 'admin', 'moderator') AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Applied by user must be a moderator or admin';
    END IF;

    -- Calculate expiration
    IF p_duration_hours IS NOT NULL THEN
        v_expires_at := now() + (p_duration_hours || ' hours')::interval;
    END IF;

    -- Insert moderation action
    INSERT INTO moderation_actions (
        community_id, target_member_id, target_content_id,
        action_type, status, reason, details, duration_hours,
        expires_at, applied_by, applied_at
    ) VALUES (
        p_community_id, p_target_member_id, p_target_content_id,
        p_action_type, 'applied', p_reason, p_details, p_duration_hours,
        v_expires_at, p_applied_by, now()
    ) RETURNING id INTO v_action_id;

    -- Update member status based on action type
    IF p_action_type = 'ban' THEN
        UPDATE members SET status = 'banned', banned_at = now(), banned_reason = p_reason
        WHERE id = p_target_member_id;
    ELSIF p_action_type = 'unban' THEN
        UPDATE members SET status = 'active', banned_at = NULL, banned_reason = NULL
        WHERE id = p_target_member_id;
    ELSIF p_action_type = 'mute' THEN
        UPDATE members SET status = 'suspended' WHERE id = p_target_member_id;
    ELSIF p_action_type = 'unmute' THEN
        UPDATE members SET status = 'active' WHERE id = p_target_member_id;
    END IF;

    RETURN v_action_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get analytics summary for date range
CREATE OR REPLACE FUNCTION get_analytics_summary(
    p_community_id UUID,
    p_start_date TIMESTAMPTZ,
    p_end_date TIMESTAMPTZ
)
RETURNS TABLE (
    event_type analytics_event_type,
    event_count BIGINT,
    unique_users BIGINT,
    unique_sessions BIGINT,
    avg_daily_events NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.event_type,
        COUNT(*) AS event_count,
        COUNT(DISTINCT ae.user_id) AS unique_users,
        COUNT(DISTINCT ae.session_id) AS unique_sessions,
        ROUND(COUNT(*)::numeric / GREATEST(EXTRACT(DAY FROM (p_end_date - p_start_date)), 1), 2) AS avg_daily_events
    FROM analytics_events ae
    WHERE ae.community_id = p_community_id
      AND ae.created_at >= p_start_date
      AND ae.created_at < p_end_date
    GROUP BY ae.event_type
    ORDER BY event_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Clean up old analytics events (archive/delete)
CREATE OR REPLACE FUNCTION cleanup_old_analytics_events(
    p_older_than TIMESTAMPTZ,
    p_batch_size INTEGER DEFAULT 10000
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER := 0;
    v_batch INTEGER;
BEGIN
    LOOP
        WITH deleted AS (
            DELETE FROM analytics_events
            WHERE created_at < p_older_than
            AND id IN (
                SELECT id FROM analytics_events
                WHERE created_at < p_older_than
                LIMIT p_batch_size
            )
            RETURNING id
        )
        SELECT COUNT(*) INTO v_batch FROM deleted;

        v_deleted := v_deleted + v_batch;
        EXIT WHEN v_batch < p_batch_size;
    END LOOP;

    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- Function: Get escalation queue with priority scoring
CREATE OR REPLACE FUNCTION get_escalation_queue(
    p_community_id UUID DEFAULT NULL,
    p_status escalation_status DEFAULT NULL,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    escalation_id UUID,
    community_id UUID,
    community_slug VARCHAR,
    category escalation_category,
    priority escalation_priority,
    status escalation_status,
    subject VARCHAR,
    reporter_name VARCHAR,
    assigned_to_name VARCHAR,
    due_at TIMESTAMPTZ,
    hours_until_due NUMERIC,
    priority_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.community_id,
        c.slug,
        e.category,
        e.priority,
        e.status,
        e.subject,
        rm.display_name AS reporter_name,
        am.display_name AS assigned_to_name,
        e.due_at,
        ROUND(EXTRACT(EPOCH FROM (e.due_at - now())) / 3600, 2) AS hours_until_due,
        CASE e.priority
            WHEN 'critical' THEN 100
            WHEN 'high' THEN 75
            WHEN 'medium' THEN 50
            WHEN 'low' THEN 25
        END +
        CASE
            WHEN e.due_at IS NOT NULL AND e.due_at < now() THEN 50
            WHEN e.due_at IS NOT NULL AND e.due_at < now() + interval '24 hours' THEN 25
            ELSE 0
        END AS priority_score
    FROM escalations e
    JOIN communities c ON c.id = e.community_id
    JOIN members rm ON rm.id = e.reporter_id
    LEFT JOIN members am ON am.id = e.assigned_to
    WHERE e.deleted_at IS NULL
      AND (p_community_id IS NULL OR e.community_id = p_community_id)
      AND (p_status IS NULL OR e.status = p_status)
    ORDER BY priority_score DESC, e.created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. TEST DATA VALIDATION — Verify Seed Data Integrity
-- =============================================================================

-- Validate community counts match
DO $$
DECLARE
    v_mismatch INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_mismatch
    FROM communities c
    WHERE c.member_count != (SELECT COUNT(*) FROM members m WHERE m.community_id = c.id AND m.deleted_at IS NULL)
       OR c.content_count != (SELECT COUNT(*) FROM content ct WHERE ct.community_id = c.id AND ct.deleted_at IS NULL);

    IF v_mismatch > 0 THEN
        RAISE WARNING 'Community count mismatch detected in % communities', v_mismatch;
    ELSE
        RAISE NOTICE 'Community counts validated: all match';
    END IF;
END $$;

-- Validate tier subscriber counts
DO $$
DECLARE
    v_mismatch INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_mismatch
    FROM tiers t
    WHERE t.subscriber_count != (SELECT COUNT(*) FROM members m WHERE m.tier_id = t.id AND m.deleted_at IS NULL);

    IF v_mismatch > 0 THEN
        RAISE WARNING 'Tier subscriber count mismatch detected in % tiers', v_mismatch;
    ELSE
        RAISE NOTICE 'Tier subscriber counts validated: all match';
    END IF;
END $$;

-- Validate reputation score consistency
DO $$
DECLARE
    v_mismatch INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_mismatch
    FROM reputation_scores rs
    WHERE rs.score != rs.total_earned - rs.total_deducted;

    IF v_mismatch > 0 THEN
        RAISE WARNING 'Reputation score inconsistency detected in % records', v_mismatch;
    ELSE
        RAISE NOTICE 'Reputation scores validated: all consistent';
    END IF;
END $$;

-- Validate foreign key integrity
DO $$
DECLARE
    v_orphans INTEGER;
BEGIN
    -- Check for orphaned members (community doesn't exist)
    SELECT COUNT(*) INTO v_orphans
    FROM members m
    WHERE NOT EXISTS (SELECT 1 FROM communities c WHERE c.id = m.community_id);

    IF v_orphans > 0 THEN
        RAISE WARNING 'Orphaned members detected: %', v_orphans;
    END IF;

    -- Check for orphaned content (author doesn't exist)
    SELECT COUNT(*) INTO v_orphans
    FROM content ct
    WHERE NOT EXISTS (SELECT 1 FROM members m WHERE m.id = ct.author_id);

    IF v_orphans > 0 THEN
        RAISE WARNING 'Orphaned content detected: %', v_orphans;
    END IF;

    -- Check for orphaned content (community doesn't exist)
    SELECT COUNT(*) INTO v_orphans
    FROM content ct
    WHERE NOT EXISTS (SELECT 1 FROM communities c WHERE c.id = ct.community_id);

    IF v_orphans > 0 THEN
        RAISE WARNING 'Orphaned content (community) detected: %', v_orphans;
    END IF;

    RAISE NOTICE 'Foreign key integrity validated';
END $$;

-- Validate enum values are within expected ranges
DO $$
DECLARE
    v_invalid INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_invalid
    FROM communities
    WHERE visibility NOT IN ('public', 'private', 'hidden')
       OR status NOT IN ('active', 'archived', 'suspended', 'deleted');

    IF v_invalid > 0 THEN
        RAISE WARNING 'Invalid community enum values: %', v_invalid;
    END IF;

    SELECT COUNT(*) INTO v_invalid
    FROM members
    WHERE role NOT IN ('owner', 'admin', 'moderator', 'member', 'guest')
       OR status NOT IN ('active', 'invited', 'banned', 'suspended', 'removed');

    IF v_invalid > 0 THEN
        RAISE WARNING 'Invalid member enum values: %', v_invalid;
    END IF;

    RAISE NOTICE 'Enum values validated';
END $$;

-- Validate no duplicate slugs within communities
DO $$
DECLARE
    v_duplicates INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_duplicates
    FROM (
        SELECT community_id, slug, COUNT(*) as cnt
        FROM tiers
        GROUP BY community_id, slug
        HAVING COUNT(*) > 1
    ) dupes;

    IF v_duplicates > 0 THEN
        RAISE WARNING 'Duplicate tier slugs detected: %', v_duplicates;
    ELSE
        RAISE NOTICE 'Tier slug uniqueness validated';
    END IF;
END $$;

-- Validate no duplicate community-user memberships
DO $$
DECLARE
    v_duplicates INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_duplicates
    FROM (
        SELECT community_id, user_id, COUNT(*) as cnt
        FROM members
        WHERE deleted_at IS NULL
        GROUP BY community_id, user_id
        HAVING COUNT(*) > 1
    ) dupes;

    IF v_duplicates > 0 THEN
        RAISE WARNING 'Duplicate memberships detected: %', v_duplicates;
    ELSE
        RAISE NOTICE 'Membership uniqueness validated';
    END IF;
END $$;

-- =============================================================================
-- 8. PERFORMANCE BENCHMARK — Run EXPLAIN ANALYZE on Key Queries
-- =============================================================================

-- These are documented in the optimization report. Run manually:
-- EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM get_community_dashboard('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
-- EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM search_content('AI', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
-- EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM get_member_activity_summary('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11');
-- EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM get_analytics_summary('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', '2026-10-01', '2026-11-01');
-- EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM get_escalation_queue();

COMMIT;

-- =============================================================================
-- POST-MIGRATION: Refresh materialized views
-- =============================================================================
SELECT refresh_materialized_views();
