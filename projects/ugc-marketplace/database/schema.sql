-- =============================================================================
-- UGC Marketplace Database Schema
-- PostgreSQL 16+
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- TABLE: creators
-- =============================================================================
CREATE TABLE creators (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username            VARCHAR(50)  NOT NULL,
    email               VARCHAR(255) NOT NULL,
    display_name        VARCHAR(100),
    bio                 TEXT,
    avatar_url          TEXT,
    website_url         TEXT,
    social_links        JSONB        NOT NULL DEFAULT '{}',
    verification_status VARCHAR(20)  NOT NULL DEFAULT 'unverified',
    reputation_score    NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    total_earnings      NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_sales         INTEGER      NOT NULL DEFAULT 0,
    is_active           BOOLEAN      NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT creators_username_unique   UNIQUE (username),
    CONSTRAINT creators_email_unique      UNIQUE (email),
    CONSTRAINT creators_verification_check CHECK (verification_status IN ('unverified', 'pending', 'verified', 'suspended')),
    CONSTRAINT creators_reputation_check  CHECK (reputation_score >= 0.00 AND reputation_score <= 100.00),
    CONSTRAINT creators_earnings_check    CHECK (total_earnings >= 0.00),
    CONSTRAINT creators_sales_check       CHECK (total_sales >= 0)
);

CREATE INDEX idx_creators_verification_status ON creators (verification_status);
CREATE INDEX idx_creators_is_active        ON creators (is_active);
CREATE INDEX idx_creators_reputation_score ON creators (reputation_score DESC);
CREATE INDEX idx_creators_social_links_gin  ON creators USING GIN (social_links);

-- =============================================================================
-- TABLE: content
-- =============================================================================
CREATE TABLE content (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id      UUID NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    content_type    VARCHAR(50)  NOT NULL,
    media_urls      JSONB        NOT NULL DEFAULT '[]',
    tags            TEXT[]       NOT NULL DEFAULT '{}',
    metadata        JSONB        NOT NULL DEFAULT '{}',
    status          VARCHAR(20)  NOT NULL DEFAULT 'draft',
    is_nsfw         BOOLEAN      NOT NULL DEFAULT false,
    view_count      INTEGER      NOT NULL DEFAULT 0,
    like_count      INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    search_vector   TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(array_to_string(tags, ' '), '')), 'C')
    ) STORED,

    CONSTRAINT content_creator_fk      FOREIGN KEY (creator_id) REFERENCES creators (id) ON DELETE CASCADE,
    CONSTRAINT content_status_check    CHECK (status IN ('draft', 'published', 'archived', 'removed')),
    CONSTRAINT content_view_count_check CHECK (view_count >= 0),
    CONSTRAINT content_like_count_check CHECK (like_count >= 0)
);

CREATE INDEX idx_content_creator_id      ON content (creator_id);
CREATE INDEX idx_content_status          ON content (status);
CREATE INDEX idx_content_content_type    ON content (content_type);
CREATE INDEX idx_content_is_nsfw         ON content (is_nsfw);
CREATE INDEX idx_content_tags_gin        ON content USING GIN (tags);
CREATE INDEX idx_content_metadata_gin    ON content USING GIN (metadata);
CREATE INDEX idx_content_search_vector   ON content USING GIN (search_vector);
CREATE INDEX idx_content_created_at      ON content (created_at DESC);

-- =============================================================================
-- TABLE: listings
-- =============================================================================
CREATE TABLE listings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id      UUID NOT NULL,
    creator_id      UUID NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    price           NUMERIC(12,2) NOT NULL,
    currency        VARCHAR(3)   NOT NULL DEFAULT 'USD',
    license_type    VARCHAR(50)  NOT NULL,
    usage_rights    JSONB        NOT NULL DEFAULT '{}',
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    sales_count     INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT listings_content_fk     FOREIGN KEY (content_id) REFERENCES content (id) ON DELETE CASCADE,
    CONSTRAINT listings_creator_fk     FOREIGN KEY (creator_id) REFERENCES creators (id) ON DELETE CASCADE,
    CONSTRAINT listings_price_check    CHECK (price >= 0.00),
    CONSTRAINT listings_sales_check    CHECK (sales_count >= 0)
);

CREATE INDEX idx_listings_content_id   ON listings (content_id);
CREATE INDEX idx_listings_creator_id   ON listings (creator_id);
CREATE INDEX idx_listings_is_active    ON listings (is_active);
CREATE INDEX idx_listings_price        ON listings (price);
CREATE INDEX idx_listings_license_type ON listings (license_type);
CREATE INDEX idx_listings_usage_rights_gin ON listings USING GIN (usage_rights);

-- =============================================================================
-- TABLE: transactions
-- =============================================================================
CREATE TABLE transactions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id              UUID NOT NULL,
    buyer_id                UUID NOT NULL,
    seller_id               UUID NOT NULL,
    amount                  NUMERIC(12,2) NOT NULL,
    currency                VARCHAR(3)   NOT NULL DEFAULT 'USD',
    platform_fee            NUMERIC(12,2) NOT NULL,
    seller_earnings         NUMERIC(12,2) NOT NULL,
    payment_method          VARCHAR(50),
    payment_status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    stripe_payment_intent_id VARCHAR(255),
    metadata                JSONB        NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT transactions_listing_fk      FOREIGN KEY (listing_id) REFERENCES listings (id),
    CONSTRAINT transactions_buyer_fk        FOREIGN KEY (buyer_id)   REFERENCES creators (id),
    CONSTRAINT transactions_seller_fk       FOREIGN KEY (seller_id)  REFERENCES creators (id),
    CONSTRAINT transactions_amount_check    CHECK (amount >= 0.00),
    CONSTRAINT transactions_fee_check       CHECK (platform_fee >= 0.00),
    CONSTRAINT transactions_earnings_check  CHECK (seller_earnings >= 0.00),
    CONSTRAINT transactions_status_check    CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded', 'disputed')),
    CONSTRAINT transactions_buyer_seller_check CHECK (buyer_id != seller_id)
);

CREATE INDEX idx_transactions_listing_id   ON transactions (listing_id);
CREATE INDEX idx_transactions_buyer_id     ON transactions (buyer_id);
CREATE INDEX idx_transactions_seller_id    ON transactions (seller_id);
CREATE INDEX idx_transactions_status       ON transactions (payment_status);
CREATE INDEX idx_transactions_created_at   ON transactions (created_at DESC);
CREATE INDEX idx_transactions_metadata_gin ON transactions USING GIN (metadata);

-- =============================================================================
-- TABLE: licenses
-- =============================================================================
CREATE TABLE licenses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id  UUID NOT NULL,
    licensee_id     UUID NOT NULL,
    licensor_id     UUID NOT NULL,
    content_id      UUID NOT NULL,
    license_type    VARCHAR(50)  NOT NULL,
    usage_scope     JSONB        NOT NULL DEFAULT '{}',
    valid_from      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    valid_until     TIMESTAMPTZ,
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT licenses_transaction_fk  FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE,
    CONSTRAINT licenses_licensee_fk    FOREIGN KEY (licensee_id)    REFERENCES creators (id),
    CONSTRAINT licenses_licensor_fk    FOREIGN KEY (licensor_id)    REFERENCES creators (id),
    CONSTRAINT licenses_content_fk     FOREIGN KEY (content_id)     REFERENCES content (id),
    CONSTRAINT licenses_validity_check  CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE INDEX idx_licenses_transaction_id ON licenses (transaction_id);
CREATE INDEX idx_licenses_licensee_id    ON licenses (licensee_id);
CREATE INDEX idx_licenses_licensor_id    ON licenses (licensor_id);
CREATE INDEX idx_licenses_content_id     ON licenses (content_id);
CREATE INDEX idx_licenses_is_active      ON licenses (is_active);
CREATE INDEX idx_licenses_valid_until    ON licenses (valid_until);
CREATE INDEX idx_licenses_usage_scope_gin ON licenses USING GIN (usage_scope);

-- =============================================================================
-- TABLE: moderation_actions
-- =============================================================================
CREATE TABLE moderation_actions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id      UUID,
    listing_id      UUID,
    moderator_id    UUID,
    action_type     VARCHAR(50) NOT NULL,
    reason          TEXT,
    details         JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT moderation_content_fk    FOREIGN KEY (content_id)   REFERENCES content (id)   ON DELETE SET NULL,
    CONSTRAINT moderation_listing_fk    FOREIGN KEY (listing_id)   REFERENCES listings (id)   ON DELETE SET NULL,
    CONSTRAINT moderation_moderator_fk  FOREIGN KEY (moderator_id) REFERENCES creators (id)  ON DELETE SET NULL,
    CONSTRAINT moderation_action_check  CHECK (action_type IN ('approve', 'reject', 'flag', 'remove', 'restore', 'warn', 'suspend', 'ban'))
);

CREATE INDEX idx_moderation_content_id   ON moderation_actions (content_id);
CREATE INDEX idx_moderation_listing_id   ON moderation_actions (listing_id);
CREATE INDEX idx_moderation_moderator_id ON moderation_actions (moderator_id);
CREATE INDEX idx_moderation_action_type  ON moderation_actions (action_type);
CREATE INDEX idx_moderation_created_at   ON moderation_actions (created_at DESC);
CREATE INDEX idx_moderation_details_gin  ON moderation_actions USING GIN (details);

-- =============================================================================
-- TABLE: quality_scores
-- =============================================================================
CREATE TABLE quality_scores (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id        UUID NOT NULL,
    overall_score     NUMERIC(4,3) NOT NULL,
    technical_score   NUMERIC(4,3),
    aesthetic_score   NUMERIC(4,3),
    engagement_score  NUMERIC(4,3),
    originality_score NUMERIC(4,3),
    scoring_model     VARCHAR(100),
    details           JSONB        NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT quality_content_fk         FOREIGN KEY (content_id) REFERENCES content (id) ON DELETE CASCADE,
    CONSTRAINT quality_overall_check      CHECK (overall_score >= 0.000 AND overall_score <= 1.000),
    CONSTRAINT quality_technical_check    CHECK (technical_score IS NULL OR (technical_score >= 0.000 AND technical_score <= 1.000)),
    CONSTRAINT quality_aesthetic_check    CHECK (aesthetic_score IS NULL OR (aesthetic_score >= 0.000 AND aesthetic_score <= 1.000)),
    CONSTRAINT quality_engagement_check   CHECK (engagement_score IS NULL OR (engagement_score >= 0.000 AND engagement_score <= 1.000)),
    CONSTRAINT quality_originality_check  CHECK (originality_score IS NULL OR (originality_score >= 0.000 AND originality_score <= 1.000))
);

CREATE INDEX idx_quality_content_id      ON quality_scores (content_id);
CREATE INDEX idx_quality_overall_score   ON quality_scores (overall_score DESC);
CREATE INDEX idx_quality_scoring_model   ON quality_scores (scoring_model);
CREATE INDEX idx_quality_details_gin     ON quality_scores USING GIN (details);

-- =============================================================================
-- TABLE: fraud_reports
-- =============================================================================
CREATE TABLE fraud_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporter_id         UUID NOT NULL,
    reported_content_id UUID,
    reported_listing_id UUID,
    reported_user_id    UUID,
    report_type         VARCHAR(50) NOT NULL,
    description         TEXT,
    evidence            JSONB       NOT NULL DEFAULT '{}',
    status              VARCHAR(20) NOT NULL DEFAULT 'open',
    resolution          TEXT,
    resolved_by         UUID,
    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fraud_reporter_fk        FOREIGN KEY (reporter_id)         REFERENCES creators (id),
    CONSTRAINT fraud_content_fk         FOREIGN KEY (reported_content_id) REFERENCES content (id)   ON DELETE SET NULL,
    CONSTRAINT fraud_listing_fk         FOREIGN KEY (reported_listing_id) REFERENCES listings (id)   ON DELETE SET NULL,
    CONSTRAINT fraud_reported_user_fk   FOREIGN KEY (reported_user_id)    REFERENCES creators (id)  ON DELETE SET NULL,
    CONSTRAINT fraud_resolved_by_fk     FOREIGN KEY (resolved_by)         REFERENCES creators (id)  ON DELETE SET NULL,
    CONSTRAINT fraud_status_check       CHECK (status IN ('open', 'investigating', 'resolved', 'dismissed', 'escalated')),
    CONSTRAINT fraud_type_check         CHECK (report_type IN ('copyright', 'fraud', 'spam', 'impersonation', 'prohibited_content', 'other'))
);

CREATE INDEX idx_fraud_reporter_id      ON fraud_reports (reporter_id);
CREATE INDEX idx_fraud_content_id       ON fraud_reports (reported_content_id);
CREATE INDEX idx_fraud_listing_id       ON fraud_reports (reported_listing_id);
CREATE INDEX idx_fraud_reported_user_id ON fraud_reports (reported_user_id);
CREATE INDEX idx_fraud_status           ON fraud_reports (status);
CREATE INDEX idx_fraud_report_type      ON fraud_reports (report_type);
CREATE INDEX idx_fraud_created_at       ON fraud_reports (created_at DESC);
CREATE INDEX idx_fraud_evidence_gin     ON fraud_reports USING GIN (evidence);

-- =============================================================================
-- TABLE: analytics_events (Partitioned by Range on created_at)
-- =============================================================================
CREATE TABLE analytics_events (
    id          UUID         NOT NULL,
    event_type  VARCHAR(100) NOT NULL,
    user_id     UUID,
    content_id  UUID,
    listing_id  UUID,
    session_id  UUID,
    ip_address  INET,
    user_agent  TEXT,
    referrer    TEXT,
    event_data  JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT analytics_events_pkey       PRIMARY KEY (id, created_at),
    CONSTRAINT analytics_user_fk          FOREIGN KEY (user_id)    REFERENCES creators (id)  ON DELETE SET NULL,
    CONSTRAINT analytics_content_fk       FOREIGN KEY (content_id) REFERENCES content (id)   ON DELETE SET NULL,
    CONSTRAINT analytics_listing_fk       FOREIGN KEY (listing_id) REFERENCES listings (id)   ON DELETE SET NULL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions (example: 2024 Q4 through 2025 Q2)
CREATE TABLE analytics_events_2024_q4 PARTITION OF analytics_events
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
CREATE TABLE analytics_events_2025_q1 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE analytics_events_2025_q2 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

-- Default partition for overflow
CREATE TABLE analytics_events_default PARTITION OF analytics_events DEFAULT;

-- Indexes on partitioned table (inherited by partitions)
CREATE INDEX idx_analytics_event_type  ON analytics_events (event_type);
CREATE INDEX idx_analytics_user_id     ON analytics_events (user_id);
CREATE INDEX idx_analytics_content_id  ON analytics_events (content_id);
CREATE INDEX idx_analytics_listing_id  ON analytics_events (listing_id);
CREATE INDEX idx_analytics_created_at  ON analytics_events (created_at DESC);
CREATE INDEX idx_analytics_event_data_gin ON analytics_events USING GIN (event_data);

-- =============================================================================
-- TABLE: audit_log
-- =============================================================================
CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name  VARCHAR(100) NOT NULL,
    record_id   UUID         NOT NULL,
    action      VARCHAR(20)  NOT NULL,
    old_values  JSONB,
    new_values  JSONB,
    changed_by  UUID,
    changed_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ip_address  INET,
    user_agent  TEXT,

    CONSTRAINT audit_changed_by_fk FOREIGN KEY (changed_by) REFERENCES creators (id) ON DELETE SET NULL,
    CONSTRAINT audit_action_check  CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_audit_table_name  ON audit_log (table_name);
CREATE INDEX idx_audit_record_id   ON audit_log (record_id);
CREATE INDEX idx_audit_changed_by  ON audit_log (changed_by);
CREATE INDEX idx_audit_changed_at  ON audit_log (changed_at DESC);
CREATE INDEX idx_audit_old_values_gin ON audit_log USING GIN (old_values);
CREATE INDEX idx_audit_new_values_gin ON audit_log USING GIN (new_values);

-- =============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_creators_updated_at
    BEFORE UPDATE ON creators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_content_updated_at
    BEFORE UPDATE ON content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_listings_updated_at
    BEFORE UPDATE ON listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_licenses_updated_at
    BEFORE UPDATE ON licenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_fraud_reports_updated_at
    BEFORE UPDATE ON fraud_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- TRIGGER: Audit log for key tables
-- =============================================================================
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), NULL);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), NULL);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), NULL);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_creators
    AFTER INSERT OR UPDATE OR DELETE ON creators
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_content
    AFTER INSERT OR UPDATE OR DELETE ON content
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_listings
    AFTER INSERT OR UPDATE OR DELETE ON listings
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER trg_audit_transactions
    AFTER INSERT OR UPDATE OR DELETE ON transactions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Creator summary view
CREATE VIEW v_creator_summary AS
SELECT
    c.id,
    c.username,
    c.display_name,
    c.verification_status,
    c.reputation_score,
    c.total_earnings,
    c.total_sales,
    COUNT(DISTINCT ct.id)  AS content_count,
    COUNT(DISTINCT l.id)   AS listing_count,
    c.created_at
FROM creators c
LEFT JOIN content ct ON ct.creator_id = c.id AND ct.status = 'published'
LEFT JOIN listings l ON l.creator_id = c.id AND l.is_active = true
GROUP BY c.id;

-- Content detail view with creator info
CREATE VIEW v_content_detail AS
SELECT
    ct.id,
    ct.title,
    ct.content_type,
    ct.status,
    ct.tags,
    ct.view_count,
    ct.like_count,
    ct.created_at,
    c.id          AS creator_id,
    c.username    AS creator_username,
    c.display_name AS creator_display_name,
    c.avatar_url  AS creator_avatar_url,
    qs.overall_score AS quality_score
FROM content ct
JOIN creators c ON c.id = ct.creator_id
LEFT JOIN quality_scores qs ON qs.content_id = ct.id;

-- Transaction summary view
CREATE VIEW v_transaction_summary AS
SELECT
    t.id,
    t.amount,
    t.currency,
    t.platform_fee,
    t.seller_earnings,
    t.payment_status,
    t.created_at,
    l.title       AS listing_title,
    buyer.username  AS buyer_username,
    seller.username AS seller_username
FROM transactions t
JOIN listings l ON l.id = t.listing_id
JOIN creators buyer ON buyer.id = t.buyer_id
JOIN creators seller ON seller.id = t.seller_id;
