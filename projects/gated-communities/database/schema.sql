-- =============================================================================
-- Gated Communities — PostgreSQL 16+ Schema
-- =============================================================================
-- Production-grade schema for gated community platform.
-- Features: UUID PKs, JSONB, full-text search, partitioning, audit trails.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- ENUMERATIONS
-- =============================================================================

CREATE TYPE community_visibility AS ENUM ('public', 'private', 'hidden');
CREATE TYPE community_status AS ENUM ('active', 'archived', 'suspended', 'deleted');
CREATE TYPE tier_billing_period AS ENUM ('monthly', 'quarterly', 'yearly', 'lifetime');
CREATE TYPE member_role AS ENUM ('owner', 'admin', 'moderator', 'member', 'guest');
CREATE TYPE member_status AS ENUM ('active', 'invited', 'banned', 'suspended', 'removed');
CREATE TYPE content_type AS ENUM ('post', 'comment', 'reply', 'poll', 'event', 'media');
CREATE TYPE content_status AS ENUM ('draft', 'published', 'edited', 'archived', 'deleted', 'flagged');
CREATE TYPE moderation_action_type AS ENUM (
    'warn', 'mute', 'unmute', 'ban', 'unban', 'content_remove',
    'content_restore', 'tier_change', 'role_change', 'note'
);
CREATE TYPE moderation_action_status AS ENUM ('pending', 'applied', 'reversed', 'expired');
CREATE TYPE escalation_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE escalation_status AS ENUM ('open', 'investigating', 'resolved', 'dismissed', 'escalated');
CREATE TYPE escalation_category AS ENUM (
    'harassment', 'spam', 'hate_speech', 'misinformation',
    'privacy_violation', 'illegal_content', 'other'
);
CREATE TYPE compliance_report_type AS ENUM (
    'gdpr_access', 'gdpr_deletion', 'gdpr_portability',
    'dmca', 'csam', 'law_enforcement', 'internal_audit'
);
CREATE TYPE compliance_report_status AS ENUM ('pending', 'in_review', 'fulfilled', 'rejected', 'appealed');
CREATE TYPE analytics_event_type AS ENUM (
    'page_view', 'content_view', 'content_like', 'content_share',
    'member_join', 'member_leave', 'tier_subscribe', 'tier_cancel',
    'search_query', 'notification_sent', 'notification_click'
);
CREATE TYPE audit_action AS ENUM ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'GRANT', 'REVOKE');

-- =============================================================================
-- COMMUNITIES
-- =============================================================================

CREATE TABLE communities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                VARCHAR(100) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT DEFAULT '',
    avatar_url          TEXT,
    banner_url          TEXT,
    visibility          community_visibility NOT NULL DEFAULT 'private',
    status              community_status NOT NULL DEFAULT 'active',
    settings            JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    member_count        INTEGER NOT NULL DEFAULT 0 CHECK (member_count >= 0),
    content_count       INTEGER NOT NULL DEFAULT 0 CHECK (content_count >= 0),
    created_by          UUID NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_communities_slug UNIQUE (slug),
    CONSTRAINT chk_communities_name_not_empty CHECK (char_length(trim(name)) > 0)
);

CREATE INDEX idx_communities_slug ON communities (slug);
CREATE INDEX idx_communities_visibility ON communities (visibility) WHERE deleted_at IS NULL;
CREATE INDEX idx_communities_status ON communities (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_communities_created_by ON communities (created_by);
CREATE INDEX idx_communities_metadata_gin ON communities USING GIN (metadata jsonb_path_ops);
CREATE INDEX idx_communities_settings_gin ON communities USING GIN (settings jsonb_path_ops);

-- Full-text search on communities
ALTER TABLE communities
    ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED;

CREATE INDEX idx_communities_search ON communities USING GIN (search_vector);

-- =============================================================================
-- TIERS
-- =============================================================================

CREATE TABLE tiers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug                VARCHAR(100) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT DEFAULT '',
    price_cents         INTEGER NOT NULL DEFAULT 0 CHECK (price_cents >= 0),
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    billing_period      tier_billing_period NOT NULL DEFAULT 'monthly',
    is_public           BOOLEAN NOT NULL DEFAULT true,
    is_active           BOOLEAN NOT NULL DEFAULT true,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    benefits            JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    subscriber_count    INTEGER NOT NULL DEFAULT 0 CHECK (subscriber_count >= 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_tiers_community_slug UNIQUE (community_id, slug),
    CONSTRAINT chk_tiers_name_not_empty CHECK (char_length(trim(name)) > 0)
);

CREATE INDEX idx_tiers_community_id ON tiers (community_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tiers_is_public ON tiers (is_public) WHERE deleted_at IS NULL;
CREATE INDEX idx_tiers_is_active ON tiers (is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_tiers_benefits_gin ON tiers USING GIN (benefits jsonb_path_ops);

-- =============================================================================
-- MEMBERS
-- =============================================================================

CREATE TABLE members (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL,
    tier_id             UUID REFERENCES tiers(id) ON DELETE SET NULL,
    role                member_role NOT NULL DEFAULT 'member',
    status              member_status NOT NULL DEFAULT 'invited',
    display_name        VARCHAR(255),
    bio                 TEXT DEFAULT '',
    avatar_url          TEXT,
    joined_at           TIMESTAMPTZ,
    invited_at          TIMESTAMPTZ,
    banned_at           TIMESTAMPTZ,
    banned_reason       TEXT,
    tier_expires_at     TIMESTAMPTZ,
    last_active_at      TIMESTAMPTZ,
    notification_prefs  JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT uq_members_community_user UNIQUE (community_id, user_id),
    CONSTRAINT chk_members_display_name CHECK (display_name IS NULL OR char_length(trim(display_name)) > 0)
);

CREATE INDEX idx_members_community_id ON members (community_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_user_id ON members (user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_tier_id ON members (tier_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_role ON members (role) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_status ON members (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_last_active ON members (last_active_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_members_metadata_gin ON members USING GIN (metadata jsonb_path_ops);
CREATE INDEX idx_members_notification_prefs_gin ON members USING GIN (notification_prefs jsonb_path_ops);

-- =============================================================================
-- CONTENT
-- =============================================================================

CREATE TABLE content (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    author_id           UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    parent_id           UUID REFERENCES content(id) ON DELETE SET NULL,
    content_type        content_type NOT NULL DEFAULT 'post',
    status              content_status NOT NULL DEFAULT 'draft',
    title               VARCHAR(500),
    body                TEXT DEFAULT '',
    body_rendered       TEXT DEFAULT '',
    media_urls          JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags                JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    like_count          INTEGER NOT NULL DEFAULT 0 CHECK (like_count >= 0),
    comment_count       INTEGER NOT NULL DEFAULT 0 CHECK (comment_count >= 0),
    share_count         INTEGER NOT NULL DEFAULT 0 CHECK (share_count >= 0),
    view_count          INTEGER NOT NULL DEFAULT 0 CHECK (view_count >= 0),
    is_pinned           BOOLEAN NOT NULL DEFAULT false,
    is_locked           BOOLEAN NOT NULL DEFAULT false,
    published_at        TIMESTAMPTZ,
    edited_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT chk_content_title CHECK (title IS NULL OR char_length(trim(title)) > 0)
);

CREATE INDEX idx_content_community_id ON content (community_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_author_id ON content (author_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_parent_id ON content (parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_type ON content (content_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_status ON content (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_published_at ON content (published_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_content_is_pinned ON content (is_pinned, published_at DESC) WHERE deleted_at IS NULL AND is_pinned = true;
CREATE INDEX idx_content_tags_gin ON content USING GIN (tags jsonb_path_ops);
CREATE INDEX idx_content_metadata_gin ON content USING GIN (metadata jsonb_path_ops);
CREATE INDEX idx_content_media_urls_gin ON content USING GIN (media_urls jsonb_path_ops);

-- Full-text search on content
ALTER TABLE content
    ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(body, '')), 'B')
    ) STORED;

CREATE INDEX idx_content_search ON content USING GIN (search_vector);

-- =============================================================================
-- MODERATION ACTIONS
-- =============================================================================

CREATE TABLE moderation_actions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    target_member_id    UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    target_content_id   UUID REFERENCES content(id) ON DELETE SET NULL,
    action_type         moderation_action_type NOT NULL,
    status              moderation_action_status NOT NULL DEFAULT 'pending',
    reason              TEXT NOT NULL,
    details             JSONB NOT NULL DEFAULT '{}'::jsonb,
    duration_hours      INTEGER CHECK (duration_hours IS NULL OR duration_hours > 0),
    expires_at          TIMESTAMPTZ,
    applied_by          UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    applied_at          TIMESTAMPTZ,
    reversed_by         UUID REFERENCES members(id) ON DELETE SET NULL,
    reversed_at         TIMESTAMPTZ,
    reversal_reason     TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_moderation_reason_not_empty CHECK (char_length(trim(reason)) > 0)
);

CREATE INDEX idx_moderation_community_id ON moderation_actions (community_id);
CREATE INDEX idx_moderation_target_member ON moderation_actions (target_member_id);
CREATE INDEX idx_moderation_target_content ON moderation_actions (target_content_id);
CREATE INDEX idx_moderation_action_type ON moderation_actions (action_type);
CREATE INDEX idx_moderation_status ON moderation_actions (status);
CREATE INDEX idx_moderation_applied_by ON moderation_actions (applied_by);
CREATE INDEX idx_moderation_expires_at ON moderation_actions (expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_moderation_details_gin ON moderation_actions USING GIN (details jsonb_path_ops);

-- =============================================================================
-- REPUTATION SCORES
-- =============================================================================

CREATE TABLE reputation_scores (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    member_id           UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    score               INTEGER NOT NULL DEFAULT 0,
    total_earned        INTEGER NOT NULL DEFAULT 0 CHECK (total_earned >= 0),
    total_deducted      INTEGER NOT NULL DEFAULT 0 CHECK (total_deducted >= 0),
    breakdown           JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_event_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_reputation_community_member UNIQUE (community_id, member_id)
);

CREATE INDEX idx_reputation_community_id ON reputation_scores (community_id);
CREATE INDEX idx_reputation_member_id ON reputation_scores (member_id);
CREATE INDEX idx_reputation_score ON reputation_scores (score DESC);
CREATE INDEX idx_reputation_breakdown_gin ON reputation_scores USING GIN (breakdown jsonb_path_ops);

-- =============================================================================
-- ESCALATIONS
-- =============================================================================

CREATE TABLE escalations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    reporter_id         UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    target_member_id    UUID REFERENCES members(id) ON DELETE SET NULL,
    target_content_id   UUID REFERENCES content(id) ON DELETE SET NULL,
    category            escalation_category NOT NULL,
    priority            escalation_priority NOT NULL DEFAULT 'medium',
    status              escalation_status NOT NULL DEFAULT 'open',
    subject             VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    resolution_notes    TEXT,
    assigned_to         UUID REFERENCES members(id) ON DELETE SET NULL,
    resolved_by         UUID REFERENCES members(id) ON DELETE SET NULL,
    resolved_at         TIMESTAMPTZ,
    due_at              TIMESTAMPTZ,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT chk_escalations_subject_not_empty CHECK (char_length(trim(subject)) > 0),
    CONSTRAINT chk_escalations_description_not_empty CHECK (char_length(trim(description)) > 0)
);

CREATE INDEX idx_escalations_community_id ON escalations (community_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_reporter ON escalations (reporter_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_target_member ON escalations (target_member_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_target_content ON escalations (target_content_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_category ON escalations (category) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_priority ON escalations (priority) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_status ON escalations (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_assigned_to ON escalations (assigned_to) WHERE deleted_at IS NULL;
CREATE INDEX idx_escalations_due_at ON escalations (due_at) WHERE deleted_at IS NULL AND due_at IS NOT NULL;
CREATE INDEX idx_escalations_metadata_gin ON escalations USING GIN (metadata jsonb_path_ops);

-- =============================================================================
-- COMPLIANCE REPORTS
-- =============================================================================

CREATE TABLE compliance_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    reporter_id         UUID REFERENCES members(id) ON DELETE SET NULL,
    report_type         compliance_report_type NOT NULL,
    status              compliance_report_status NOT NULL DEFAULT 'pending',
    subject             VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    evidence_urls       JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by         UUID REFERENCES members(id) ON DELETE SET NULL,
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT,
    external_ref        VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT chk_compliance_subject_not_empty CHECK (char_length(trim(subject)) > 0),
    CONSTRAINT chk_compliance_description_not_empty CHECK (char_length(trim(description)) > 0)
);

CREATE INDEX idx_compliance_community_id ON compliance_reports (community_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_compliance_reporter ON compliance_reports (reporter_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_compliance_report_type ON compliance_reports (report_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_compliance_status ON compliance_reports (status) WHERE deleted_at IS NULL;
CREATE INDEX idx_compliance_reviewed_by ON compliance_reports (reviewed_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_compliance_external_ref ON compliance_reports (external_ref) WHERE external_ref IS NOT NULL;
CREATE INDEX idx_compliance_evidence_gin ON compliance_reports USING GIN (evidence_urls jsonb_path_ops);
CREATE INDEX idx_compliance_metadata_gin ON compliance_reports USING GIN (metadata jsonb_path_ops);

-- =============================================================================
-- ANALYTICS EVENTS (Partitioned by Range on created_at)
-- =============================================================================

CREATE TABLE analytics_events (
    id                  UUID NOT NULL DEFAULT gen_random_uuid(),
    community_id        UUID NOT NULL,
    user_id             UUID,
    session_id          VARCHAR(255),
    event_type          analytics_event_type NOT NULL,
    event_data          JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address          INET,
    user_agent          TEXT,
    referrer_url        TEXT,
    page_url            TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for the current and next 12 months
-- In production, use pg_partman or a scheduled job to create future partitions
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

-- Default partition for overflow
CREATE TABLE analytics_events_default PARTITION OF analytics_events DEFAULT;

-- Indexes on partitioned table (inherited by all partitions)
CREATE INDEX idx_analytics_community_id ON analytics_events (community_id);
CREATE INDEX idx_analytics_user_id ON analytics_events (user_id);
CREATE INDEX idx_analytics_event_type ON analytics_events (event_type);
CREATE INDEX idx_analytics_created_at ON analytics_events (created_at DESC);
CREATE INDEX idx_analytics_session_id ON analytics_events (session_id);
CREATE INDEX idx_analytics_event_data_gin ON analytics_events USING GIN (event_data jsonb_path_ops);
CREATE INDEX idx_analytics_community_event ON analytics_events (community_id, event_type, created_at DESC);

-- =============================================================================
-- AUDIT LOG
-- =============================================================================

CREATE TABLE audit_log (
    id                  BIGSERIAL PRIMARY KEY,
    table_name          VARCHAR(128) NOT NULL,
    record_id           UUID NOT NULL,
    action              audit_action NOT NULL,
    old_data            JSONB,
    new_data            JSONB,
    changed_fields      JSONB,
    performed_by        UUID,
    performed_by_type   VARCHAR(50) DEFAULT 'user',
    ip_address          INET,
    user_agent          TEXT,
    session_id          VARCHAR(255),
    request_id          VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_table_name ON audit_log (table_name);
CREATE INDEX idx_audit_record_id ON audit_log (record_id);
CREATE INDEX idx_audit_action ON audit_log (action);
CREATE INDEX idx_audit_performed_by ON audit_log (performed_by);
CREATE INDEX idx_audit_created_at ON audit_log (created_at DESC);
CREATE INDEX idx_audit_table_record ON audit_log (table_name, record_id);
CREATE INDEX idx_audit_old_data_gin ON audit_log USING GIN (old_data jsonb_path_ops);
CREATE INDEX idx_audit_new_data_gin ON audit_log USING GIN (new_data jsonb_path_ops);

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER trg_communities_updated_at
    BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_tiers_updated_at
    BEFORE UPDATE ON tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_content_updated_at
    BEFORE UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_moderation_actions_updated_at
    BEFORE UPDATE ON moderation_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_reputation_scores_updated_at
    BEFORE UPDATE ON reputation_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_escalations_updated_at
    BEFORE UPDATE ON escalations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_compliance_reports_updated_at
    BEFORE UPDATE ON compliance_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit log trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_changed_fields JSONB;
    v_record_id UUID;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        v_old_data = to_jsonb(OLD);
        v_new_data = NULL;
        v_changed_fields = NULL;
        v_record_id = OLD.id;
    ELSIF (TG_OP = 'INSERT') THEN
        v_old_data = NULL;
        v_new_data = to_jsonb(NEW);
        v_changed_fields = NULL;
        v_record_id = NEW.id;
    ELSIF (TG_OP = 'UPDATE') THEN
        v_old_data = to_jsonb(OLD);
        v_new_data = to_jsonb(NEW);
        v_changed_fields = (
            SELECT jsonb_agg(key)
            FROM jsonb_each(v_new_data) AS n(key, value)
            WHERE v_old_data->key IS DISTINCT FROM n.value
        );
        v_record_id = NEW.id;
    END IF;

    INSERT INTO audit_log (
        table_name, record_id, action, old_data, new_data,
        changed_fields, performed_by, performed_by_type
    ) VALUES (
        TG_TABLE_NAME, v_record_id, TG_OP, v_old_data, v_new_data,
        v_changed_fields, NULL, 'system'
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to core tables
CREATE TRIGGER trg_audit_communities
    AFTER INSERT OR UPDATE OR DELETE ON communities
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_members
    AFTER INSERT OR UPDATE OR DELETE ON members
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_content
    AFTER INSERT OR UPDATE OR DELETE ON content
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_moderation_actions
    AFTER INSERT OR UPDATE OR DELETE ON moderation_actions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_escalations
    AFTER INSERT OR UPDATE OR DELETE ON escalations
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_compliance_reports
    AFTER INSERT OR UPDATE OR DELETE ON compliance_reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Community summary view
CREATE OR REPLACE VIEW v_community_summary AS
SELECT
    c.id,
    c.slug,
    c.name,
    c.visibility,
    c.status,
    c.member_count,
    c.content_count,
    c.created_at,
    COUNT(DISTINCT m.id) FILTER (WHERE m.status = 'active') AS active_members,
    COUNT(DISTINCT t.id) FILTER (WHERE t.is_active = true) AS active_tiers,
    COUNT(DISTINCT ct.id) FILTER (WHERE ct.status = 'published') AS published_content
FROM communities c
LEFT JOIN members m ON m.community_id = c.id AND m.deleted_at IS NULL
LEFT JOIN tiers t ON t.community_id = c.id AND t.deleted_at IS NULL
LEFT JOIN content ct ON ct.community_id = c.id AND ct.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.id;

-- Member detail view
CREATE OR REPLACE VIEW v_member_detail AS
SELECT
    m.id,
    m.community_id,
    c.slug AS community_slug,
    c.name AS community_name,
    m.user_id,
    m.role,
    m.status,
    m.display_name,
    m.bio,
    m.joined_at,
    m.last_active_at,
    m.tier_id,
    t.name AS tier_name,
    m.tier_expires_at,
    rs.score AS reputation_score,
    m.created_at
FROM members m
JOIN communities c ON c.id = m.community_id
LEFT JOIN tiers t ON t.id = m.tier_id
LEFT JOIN reputation_scores rs ON rs.member_id = m.id AND rs.community_id = m.community_id
WHERE m.deleted_at IS NULL;

-- Content detail view
CREATE OR REPLACE VIEW v_content_detail AS
SELECT
    ct.id,
    ct.community_id,
    c.slug AS community_slug,
    ct.author_id,
    m.display_name AS author_name,
    ct.content_type,
    ct.status,
    ct.title,
    ct.body,
    ct.tags,
    ct.like_count,
    ct.comment_count,
    ct.share_count,
    ct.view_count,
    ct.is_pinned,
    ct.published_at,
    ct.created_at
FROM content ct
JOIN communities c ON c.id = ct.community_id
JOIN members m ON m.id = ct.author_id
WHERE ct.deleted_at IS NULL;

-- =============================================================================
-- ROW-LEVEL SECURITY (Optional — enable as needed)
-- =============================================================================

-- ALTER TABLE communities ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE members ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- COMMENTS / DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE communities IS 'Core communities table — top-level entity for gated groups';
COMMENT ON TABLE tiers IS 'Membership tiers/pricing levels within a community';
COMMENT ON TABLE members IS 'Community membership records linking users to communities';
COMMENT ON TABLE content IS 'User-generated content (posts, comments, replies, etc.)';
COMMENT ON TABLE moderation_actions IS 'Moderation actions taken against members or content';
COMMENT ON TABLE reputation_scores IS 'Per-member reputation scores within each community';
COMMENT ON TABLE escalations IS 'Escalated reports requiring manual review';
COMMENT ON TABLE compliance_reports IS 'Compliance and legal reports (GDPR, DMCA, etc.)';
COMMENT ON TABLE analytics_events IS 'Partitioned analytics events for tracking user behavior';
COMMENT ON TABLE audit_log IS 'Audit trail for all changes to core tables';

COMMENT ON COLUMN communities.settings IS 'Community-level settings (features, permissions, etc.)';
COMMENT ON COLUMN communities.metadata IS 'Flexible metadata storage for community';
COMMENT ON COLUMN tiers.benefits IS 'Array of benefits included in this tier';
COMMENT ON COLUMN members.notification_prefs IS 'Per-member notification preferences';
COMMENT ON COLUMN content.tags IS 'Array of tags for content categorization';
COMMENT ON COLUMN content.media_urls IS 'Array of media attachment URLs';
COMMENT ON COLUMN analytics_events.event_data IS 'Flexible JSONB payload for event-specific data';
