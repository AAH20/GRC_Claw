-- =============================================================================
-- UGC Marketplace Database Optimizations
-- PostgreSQL 16+
-- =============================================================================

-- =============================================================================
-- 1. QUERY OPTIMIZATION — Missing Indexes
-- =============================================================================

-- Composite index for content queries filtered by creator and status
CREATE INDEX idx_content_creator_status ON content (creator_id, status);

-- Composite index for listings queries filtered by creator and active status
CREATE INDEX idx_listings_creator_active ON listings (creator_id, is_active);

-- Composite index for transactions filtered by buyer and status
CREATE INDEX idx_transactions_buyer_status ON transactions (buyer_id, payment_status);

-- Composite index for transactions filtered by seller and status
CREATE INDEX idx_transactions_seller_status ON transactions (seller_id, payment_status);

-- Composite index for licenses filtered by licensee and active status
CREATE INDEX idx_licenses_licensee_active ON licenses (licensee_id, is_active);

-- Composite index for fraud reports filtered by status and type
CREATE INDEX idx_fraud_status_type ON fraud_reports (status, report_type);

-- Composite index for moderation actions filtered by content and action type
CREATE INDEX idx_moderation_content_action ON moderation_actions (content_id, action_type);

-- Composite index for moderation actions filtered by listing and action type
CREATE INDEX idx_moderation_listing_action ON moderation_actions (listing_id, action_type);

-- Composite index for quality scores filtered by content and score
CREATE INDEX idx_quality_content_score ON quality_scores (content_id, overall_score DESC);

-- Composite index for audit log filtered by table and record
CREATE INDEX idx_audit_table_record ON audit_log (table_name, record_id);

-- Composite index for audit log filtered by table and timestamp
CREATE INDEX idx_audit_table_changed_at ON audit_log (table_name, changed_at DESC);

-- Index for analytics events by session
CREATE INDEX idx_analytics_session_id ON analytics_events (session_id);

-- Composite index for analytics events filtered by event type and time
CREATE INDEX idx_analytics_event_type_created_at ON analytics_events (event_type, created_at DESC);

-- Index for analytics events by IP address (fraud detection)
CREATE INDEX idx_analytics_ip_address ON analytics_events (ip_address);

-- =============================================================================
-- 2. PARTITIONING — analytics_events Improvements
-- =============================================================================

-- Extend partitioning to cover 2025 Q3 through 2026 Q4
CREATE TABLE analytics_events_2025_q3 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');
CREATE TABLE analytics_events_2025_q4 PARTITION OF analytics_events
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
CREATE TABLE analytics_events_2026_q1 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE analytics_events_2026_q2 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE analytics_events_2026_q3 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE analytics_events_2026_q4 PARTITION OF analytics_events
    FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

-- =============================================================================
-- 3. CONSTRAINTS — CHECK and UNIQUE
-- =============================================================================

-- UNIQUE: Prevent duplicate Stripe payment intent IDs
CREATE UNIQUE INDEX idx_transactions_stripe_intent_unique
    ON transactions (stripe_payment_intent_id)
    WHERE stripe_payment_intent_id IS NOT NULL;

-- UNIQUE: Prevent duplicate listings for same content + license type
ALTER TABLE listings
    ADD CONSTRAINT listings_content_license_unique UNIQUE (content_id, license_type);

-- UNIQUE: One quality score per content per scoring model
ALTER TABLE quality_scores
    ADD CONSTRAINT quality_content_model_unique UNIQUE (content_id, scoring_model);

-- UNIQUE: Prevent duplicate licenses for same transaction + licensee + content
ALTER TABLE licenses
    ADD CONSTRAINT licenses_transaction_licensee_content_unique
    UNIQUE (transaction_id, licensee_id, content_id);

-- CHECK: Valid ISO 4217 currency codes
ALTER TABLE transactions
    ADD CONSTRAINT transactions_currency_check CHECK (currency ~ '^[A-Z]{3}$');

ALTER TABLE listings
    ADD CONSTRAINT listings_currency_check CHECK (currency ~ '^[A-Z]{3}$');

-- CHECK: Moderation actions must reference at least one entity
ALTER TABLE moderation_actions
    ADD CONSTRAINT moderation_entity_check
    CHECK (content_id IS NOT NULL OR listing_id IS NOT NULL OR moderator_id IS NOT NULL);

-- CHECK: Analytics events cannot have future timestamps (1-minute tolerance)
ALTER TABLE analytics_events
    ADD CONSTRAINT analytics_created_at_check
    CHECK (created_at <= now() + interval '1 minute');
