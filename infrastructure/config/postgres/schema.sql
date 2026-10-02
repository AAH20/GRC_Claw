-- =============================================================================
-- GRC Claw — PostgreSQL Schema
-- =============================================================================
-- Core database schema for the GRC Claw shared infrastructure.
-- This schema is applied on database initialization.
-- =============================================================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS grc_claw;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Agent registry
CREATE TABLE IF NOT EXISTS grc_claw.agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(100) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'active',
    config          JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON grc_claw.agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON grc_claw.agents(type);

-- Campaign tracking
CREATE TABLE IF NOT EXISTS grc_claw.campaigns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID NOT NULL REFERENCES grc_claw.agents(id),
    name            VARCHAR(255) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'draft',
    budget          DECIMAL(15,2) NOT NULL DEFAULT 0,
    spent           DECIMAL(15,2) NOT NULL DEFAULT 0,
    metrics         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_agent ON grc_claw.campaigns(agent_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON grc_claw.campaigns(status);

-- Event log (partitioned by month)
CREATE TABLE IF NOT EXISTS grc_claw.events (
    id              BIGSERIAL,
    event_type      VARCHAR(100) NOT NULL,
    agent_id        UUID REFERENCES grc_claw.agents(id),
    campaign_id     UUID REFERENCES grc_claw.campaigns(id),
    payload         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create initial partitions
CREATE TABLE IF NOT EXISTS grc_claw.events_2024_10
    PARTITION OF grc_claw.events
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE IF NOT EXISTS grc_claw.events_2024_11
    PARTITION OF grc_claw.events
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE INDEX IF NOT EXISTS idx_events_type ON grc_claw.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_agent ON grc_claw.events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON grc_claw.events(created_at);

-- Audit log
CREATE TABLE IF NOT EXISTS audit.log (
    id              BIGSERIAL PRIMARY KEY,
    table_name      VARCHAR(255) NOT NULL,
    record_id       UUID NOT NULL,
    action          VARCHAR(50) NOT NULL,
    old_data        JSONB,
    new_data        JSONB,
    performed_by    VARCHAR(255),
    performed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_table ON audit.log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit.log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_performed_at ON audit.log(performed_at);

-- =============================================================================
-- Materialized Views
-- =============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.campaign_summary AS
SELECT
    c.id AS campaign_id,
    c.name AS campaign_name,
    c.status,
    c.budget,
    c.spent,
    COUNT(e.id) AS event_count,
    MAX(e.created_at) AS last_event_at
FROM grc_claw.campaigns c
LEFT JOIN grc_claw.events e ON e.campaign_id = c.id
GROUP BY c.id, c.name, c.status, c.budget, c.spent;

CREATE UNIQUE INDEX IF NOT EXISTS idx_campaign_summary_id
    ON analytics.campaign_summary(campaign_id);

-- =============================================================================
-- Functions
-- =============================================================================

CREATE OR REPLACE FUNCTION grc_claw.create_monthly_partition(
    p_table_name TEXT,
    p_year INT,
    p_month INT
) RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    create_sql TEXT;
BEGIN
    partition_name := p_table_name || '_' || p_year || '_' || LPAD(p_month::TEXT, 2, '0');
    start_date := make_date(p_year, p_month, 1);
    end_date := start_date + INTERVAL '1 month';

    create_sql := format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        p_table_name,
        start_date,
        end_date
    );

    EXECUTE create_sql;
    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION grc_claw.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Triggers
-- =============================================================================

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'grc_claw'
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_updated_at ON grc_claw.%I',
            t
        );
        EXECUTE format(
            'CREATE TRIGGER trg_updated_at BEFORE UPDATE ON grc_claw.%I
             FOR EACH ROW EXECUTE FUNCTION grc_claw.update_updated_at_column()',
            t
        );
    END LOOP;
END
$$;
