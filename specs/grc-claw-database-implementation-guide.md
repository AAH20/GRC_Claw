# GRC_Claw Database Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** grc-claw-storage-spec.md v1.1, grc-claw-integration-specification.md v2.0

---

## Table of Contents

1. [Overview](#1-overview)
2. [PostgreSQL Schema](#2-postgresql-schema)
3. [MongoDB Schemas](#3-mongodb-schemas)
4. [Neo4j Graph Schema](#4-neo4j-graph-schema)
5. [TimescaleDB Hypertables](#5-timescaledb-hypertables)
6. [Database Migration Scripts](#6-database-migration-scripts)
7. [Seed Data Scripts](#7-seed-data-scripts)
8. [Backup and Restore Procedures](#8-backup-and-restore-procedures)

---

## 1. Overview

GRC_Claw uses four storage backends, each optimized for specific data models:

| Backend | Technology | Data Models | Use Case |
|---------|-----------|-------------|----------|
| Relational | PostgreSQL 16 | Policy, Enforcement, Assessment, Compliance | ACID transactions, referential integrity |
| Document | MongoDB 7 | Evidence, Policy versions, Assessment reports | Flexible schema, large documents |
| Graph | Neo4j 5 | Enforcement dependencies, Compliance mappings | Relationship traversal, impact analysis |
| Time-Series | TimescaleDB 2 | Evidence metrics | High-ingest metrics, time-based aggregation |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GRC_Claw Application                  │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Policy   │ Evidence │Enforcement│ Assessment │ Compliance│
│ Service  │ Service  │ Service   │ Service   │ Service   │
├──────────┴──────────┴──────────┴────────────────────────┤
│              Storage Abstraction Layer                   │
├──────────┬──────────┬──────────┬────────────────────────┤
│Relational│ Document │  Graph   │    Time-Series         │
│PostgreSQL│MongoDB   │Neo4j     │    TimescaleDB         │
└──────────┴──────────┴──────────┴────────────────────────┘
```

---

## 2. PostgreSQL Schema

### 2.1 Extensions

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS "pg_cron";       -- Scheduled jobs (optional)
CREATE EXTENSION IF NOT EXISTS "timescaledb";   -- Time-series support
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Trigram text search
```

### 2.2 Schema Creation

```sql
-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS grc_claw;
CREATE SCHEMA IF NOT EXISTS grc_claw_archive;
CREATE SCHEMA IF NOT EXISTS grc_claw_audit;

-- Set search path
SET search_path TO grc_claw, public;
```

### 2.3 Policy Model Tables

```sql
-- ============================================================
-- POLICY MODEL
-- ============================================================

CREATE TABLE policies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_key      VARCHAR(128) UNIQUE NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    category        VARCHAR(64) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'draft',
    version         INTEGER NOT NULL DEFAULT 1,
    effective_date  TIMESTAMPTZ,
    expiry_date     TIMESTAMPTZ,
    owner_id        UUID NOT NULL,
    metadata        JSONB,
    legal_hold      BOOLEAN NOT NULL DEFAULT false,
    legal_hold_reason TEXT,
    lifecycle_stage VARCHAR(32) NOT NULL DEFAULT 'active',
    stage_changed_at TIMESTAMPTZ,
    compression_enabled BOOLEAN NOT NULL DEFAULT false,
    compressed_size_bytes BIGINT,
    original_size_bytes BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID NOT NULL,
    updated_by      UUID NOT NULL,
    
    CONSTRAINT chk_policy_category CHECK (category IN (
        'ethics', 'safety', 'privacy', 'fairness', 'data_handling',
        'agent_behavior', 'model_governance', 'access_control',
        'content_safety', 'custom'
    )),
    CONSTRAINT chk_policy_status CHECK (status IN (
        'draft', 'review', 'active', 'deprecated', 'archived'
    )),
    CONSTRAINT chk_policy_dates CHECK (
        effective_date IS NULL OR expiry_date IS NULL OR effective_date < expiry_date
    ),
    CONSTRAINT chk_policy_version CHECK (version > 0)
);

CREATE TABLE policy_clauses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id       UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    clause_number   VARCHAR(32) NOT NULL,
    title           VARCHAR(256) NOT NULL,
    body            TEXT NOT NULL,
    severity        VARCHAR(16) NOT NULL DEFAULT 'medium',
    enforcement_type VARCHAR(32) NOT NULL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_clause_severity CHECK (severity IN (
        'critical', 'high', 'medium', 'low'
    )),
    CONSTRAINT chk_clause_enforcement CHECK (enforcement_type IN (
        'automated', 'manual', 'hybrid'
    )),
    CONSTRAINT uq_policy_clause UNIQUE (policy_id, clause_number)
);

CREATE TABLE policy_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_policy   UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    target_policy   UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    relation_type   VARCHAR(64) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_relation_type CHECK (relation_type IN (
        'supersedes', 'conflicts_with', 'derives_from', 'related_to'
    )),
    CONSTRAINT chk_no_self_relation CHECK (source_policy != target_policy),
    CONSTRAINT uq_policy_relationship UNIQUE (source_policy, target_policy, relation_type)
);

-- Policy indexes
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_effective ON policies(effective_date, expiry_date);
CREATE INDEX idx_policies_owner ON policies(owner_id);
CREATE INDEX idx_policies_lifecycle ON policies(lifecycle_stage);
CREATE INDEX idx_policies_legal_hold ON policies(legal_hold) WHERE legal_hold = true;
CREATE INDEX idx_policy_clauses_policy ON policy_clauses(policy_id);
CREATE INDEX idx_policy_clauses_severity ON policy_clauses(severity);
CREATE INDEX idx_policy_rel_source ON policy_relationships(source_policy);
CREATE INDEX idx_policy_rel_target ON policy_relationships(target_policy);
CREATE INDEX idx_policies_active ON policies(category, status) WHERE status = 'active';
CREATE INDEX idx_policies_metadata ON policies USING GIN(metadata jsonb_path_ops);
```

### 2.4 Enforcement Model Tables

```sql
-- ============================================================
-- ENFORCEMENT MODEL
-- ============================================================

CREATE TABLE enforcement_actions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_key      VARCHAR(128) UNIQUE NOT NULL,
    policy_id       UUID NOT NULL REFERENCES policies(id),
    clause_id       UUID REFERENCES policy_clauses(id),
    evidence_id     UUID,
    action_type     VARCHAR(64) NOT NULL,
    target_type     VARCHAR(64) NOT NULL,
    target_id       VARCHAR(256) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    priority        VARCHAR(16) NOT NULL DEFAULT 'medium',
    triggered_by    UUID NOT NULL,
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at     TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    result          JSONB,
    error_message   TEXT,
    rollback_action JSONB,
    metadata        JSONB,
    legal_hold      BOOLEAN NOT NULL DEFAULT false,
    legal_hold_reason TEXT,
    lifecycle_stage VARCHAR(32) NOT NULL DEFAULT 'active',
    stage_changed_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_action_type CHECK (action_type IN (
        'block', 'flag', 'quarantine', 'notify', 'escalate', 'auto_remediate'
    )),
    CONSTRAINT chk_target_type CHECK (target_type IN (
        'model', 'dataset', 'endpoint', 'user', 'pipeline', 'agent', 'tool', 'resource'
    )),
    CONSTRAINT chk_enforcement_status CHECK (status IN (
        'pending', 'in_progress', 'completed', 'failed', 'rolled_back'
    )),
    CONSTRAINT chk_priority CHECK (priority IN (
        'critical', 'high', 'medium', 'low'
    )),
    CONSTRAINT chk_enforcement_dates CHECK (
        executed_at IS NULL OR completed_at IS NULL OR executed_at <= completed_at
    )
);

CREATE TABLE enforcement_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id       UUID NOT NULL REFERENCES enforcement_actions(id) ON DELETE CASCADE,
    event_type      VARCHAR(64) NOT NULL,
    event_data      JSONB,
    actor           UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_audit_event_type CHECK (event_type IN (
        'created', 'started', 'completed', 'failed', 'rolled_back'
    ))
);

-- Enforcement indexes
CREATE INDEX idx_enforcement_policy ON enforcement_actions(policy_id);
CREATE INDEX idx_enforcement_status ON enforcement_actions(status);
CREATE INDEX idx_enforcement_target ON enforcement_actions(target_type, target_id);
CREATE INDEX idx_enforcement_triggered ON enforcement_actions(triggered_at);
CREATE INDEX idx_enforcement_priority ON enforcement_actions(priority);
CREATE INDEX idx_enforcement_legal_hold ON enforcement_actions(legal_hold) WHERE legal_hold = true;
CREATE INDEX idx_enforcement_audit_action ON enforcement_audit_log(action_id);
CREATE INDEX idx_enforcement_audit_created ON enforcement_audit_log(created_at);
CREATE INDEX idx_enforcement_active ON enforcement_actions(policy_id, status, priority)
    WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_enforcement_result ON enforcement_actions USING GIN(result jsonb_path_ops);
```

### 2.5 Assessment Model Tables

```sql
-- ============================================================
-- ASSESSMENT MODEL
-- ============================================================

CREATE TABLE assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_key  VARCHAR(128) UNIQUE NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT,
    assessment_type VARCHAR(64) NOT NULL,
    target_id       VARCHAR(256) NOT NULL,
    target_type     VARCHAR(64) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'planned',
    methodology     VARCHAR(128),
    score           NUMERIC(5,2),
    risk_level      VARCHAR(16),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    next_assessment_at TIMESTAMPTZ,
    lead_assessor   UUID NOT NULL,
    metadata        JSONB,
    legal_hold      BOOLEAN NOT NULL DEFAULT false,
    legal_hold_reason TEXT,
    lifecycle_stage VARCHAR(32) NOT NULL DEFAULT 'active',
    stage_changed_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID NOT NULL,
    updated_by      UUID NOT NULL,
    
    CONSTRAINT chk_assessment_type CHECK (assessment_type IN (
        'risk', 'compliance', 'maturity', 'readiness',
        'control_assessment', 'framework_assessment', 'risk_assessment',
        'impact_assessment', 'vendor_assessment', 'agent_assessment'
    )),
    CONSTRAINT chk_assessment_target_type CHECK (target_type IN (
        'model', 'system', 'organization', 'process', 'agent', 'vendor'
    )),
    CONSTRAINT chk_assessment_status CHECK (status IN (
        'planned', 'in_progress', 'completed', 'cancelled', 'not_started', 'failed', 'expired'
    )),
    CONSTRAINT chk_assessment_score CHECK (score IS NULL OR (score >= 0.00 AND score <= 100.00)),
    CONSTRAINT chk_risk_level CHECK (risk_level IS NULL OR risk_level IN (
        'critical', 'high', 'medium', 'low'
    )),
    CONSTRAINT chk_assessment_dates CHECK (
        started_at IS NULL OR completed_at IS NULL OR started_at <= completed_at
    )
);

CREATE TABLE assessment_findings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id   UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    finding_key     VARCHAR(128) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT NOT NULL,
    severity        VARCHAR(16) NOT NULL,
    category        VARCHAR(64) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'open',
    policy_id       UUID REFERENCES policies(id),
    evidence_ids    UUID[],
    remediation    TEXT,
    remediated_by   UUID,
    remediated_at   TIMESTAMPTZ,
    due_date        TIMESTAMPTZ,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_finding_severity CHECK (severity IN (
        'critical', 'high', 'medium', 'low', 'informational'
    )),
    CONSTRAINT chk_finding_status CHECK (status IN (
        'open', 'in_progress', 'resolved', 'accepted', 'false_positive'
    )),
    CONSTRAINT uq_finding_key UNIQUE (assessment_id, finding_key)
);

CREATE TABLE assessment_evidence_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id   UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    evidence_id     UUID NOT NULL,
    finding_id      UUID REFERENCES assessment_findings(id),
    relevance_score NUMERIC(3,2),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_relevance_score CHECK (
        relevance_score IS NULL OR (relevance_score >= 0.00 AND relevance_score <= 1.00)
    ),
    CONSTRAINT uq_assessment_evidence UNIQUE (assessment_id, evidence_id, finding_id)
);

-- Assessment indexes
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_assessments_target ON assessments(target_type, target_id);
CREATE INDEX idx_assessments_lead ON assessments(lead_assessor);
CREATE INDEX idx_assessments_next ON assessments(next_assessment_at);
CREATE INDEX idx_assessments_legal_hold ON assessments(legal_hold) WHERE legal_hold = true;
CREATE INDEX idx_findings_assessment ON assessment_findings(assessment_id);
CREATE INDEX idx_findings_status ON assessment_findings(status);
CREATE INDEX idx_findings_severity ON assessment_findings(severity);
CREATE INDEX idx_findings_policy ON assessment_findings(policy_id);
CREATE INDEX idx_findings_due_date ON assessment_findings(due_date);
CREATE INDEX idx_assessment_evidence_links_assessment ON assessment_evidence_links(assessment_id);
CREATE INDEX idx_assessment_evidence_links_evidence ON assessment_evidence_links(evidence_id);
CREATE INDEX idx_assessment_evidence_links_finding ON assessment_evidence_links(finding_id);
```

### 2.6 Compliance Model Tables

```sql
-- ============================================================
-- COMPLIANCE MODEL
-- ============================================================

CREATE TABLE compliance_frameworks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_key   VARCHAR(128) UNIQUE NOT NULL,
    name            VARCHAR(256) NOT NULL,
    version         VARCHAR(64) NOT NULL,
    description     TEXT,
    authority       VARCHAR(256),
    effective_date  DATE,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE compliance_controls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id    UUID NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    control_key     VARCHAR(128) NOT NULL,
    title           VARCHAR(512) NOT NULL,
    description     TEXT NOT NULL,
    category        VARCHAR(128) NOT NULL,
    guidance        TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_control_key UNIQUE (framework_id, control_key)
);

CREATE TABLE compliance_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id      UUID NOT NULL REFERENCES compliance_controls(id) ON DELETE CASCADE,
    policy_id       UUID REFERENCES policies(id),
    assessment_id   UUID REFERENCES assessments(id),
    mapping_type    VARCHAR(64) NOT NULL,
    coverage        VARCHAR(16) NOT NULL DEFAULT 'partial',
    notes           TEXT,
    mapped_by       UUID NOT NULL,
    mapped_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_mapping_type CHECK (mapping_type IN (
        'policy_satisfies', 'assessment_covers', 'evidence_supports'
    )),
    CONSTRAINT chk_coverage CHECK (coverage IN ('full', 'partial', 'none'))
);

CREATE TABLE compliance_status (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id    UUID NOT NULL REFERENCES compliance_frameworks(id),
    control_id      UUID NOT NULL REFERENCES compliance_controls(id),
    target_id       VARCHAR(256) NOT NULL,
    target_type     VARCHAR(64) NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'unknown',
    evidence_ids    UUID[],
    assessment_id   UUID REFERENCES assessments(id),
    evaluated_at    TIMESTAMPTZ,
    evaluated_by    UUID,
    next_review_at  TIMESTAMPTZ,
    notes           TEXT,
    metadata        JSONB,
    legal_hold      BOOLEAN NOT NULL DEFAULT false,
    legal_hold_reason TEXT,
    lifecycle_stage VARCHAR(32) NOT NULL DEFAULT 'active',
    stage_changed_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_compliance_status CHECK (status IN (
        'compliant', 'non_compliant', 'partial', 'not_assessed', 'unknown', 'exempt'
    )),
    CONSTRAINT uq_compliance_status UNIQUE (framework_id, control_id, target_id, target_type)
);

CREATE TABLE compliance_attestations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    compliance_status_id UUID NOT NULL REFERENCES compliance_status(id) ON DELETE CASCADE,
    attestation_type VARCHAR(64) NOT NULL,
    attested_by     UUID NOT NULL,
    attested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ NOT NULL,
    evidence_id     UUID,
    notes           TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_attestation_type CHECK (attestation_type IN (
        'self', 'internal_audit', 'external_audit', 'certification'
    )),
    CONSTRAINT chk_attestation_dates CHECK (valid_from < valid_until)
);

-- Compliance indexes
CREATE INDEX idx_compliance_controls_framework ON compliance_controls(framework_id);
CREATE INDEX idx_compliance_controls_category ON compliance_controls(category);
CREATE INDEX idx_compliance_mappings_control ON compliance_mappings(control_id);
CREATE INDEX idx_compliance_mappings_policy ON compliance_mappings(policy_id);
CREATE INDEX idx_compliance_mappings_assessment ON compliance_mappings(assessment_id);
CREATE INDEX idx_compliance_status_framework ON compliance_status(framework_id);
CREATE INDEX idx_compliance_status_control ON compliance_status(control_id);
CREATE INDEX idx_compliance_status_target ON compliance_status(target_type, target_id);
CREATE INDEX idx_compliance_status_review ON compliance_status(next_review_at);
CREATE INDEX idx_compliance_status_legal_hold ON compliance_status(legal_hold) WHERE legal_hold = true;
CREATE INDEX idx_compliance_attestations_status ON compliance_attestations(compliance_status_id);
CREATE INDEX idx_compliance_attestations_valid ON compliance_attestations(valid_from, valid_until);
CREATE INDEX idx_compliance_status_lookup ON compliance_status(framework_id, control_id, target_type, target_id)
    INCLUDE (status, evaluated_at, next_review_at);
```

### 2.7 Audit Log Table

```sql
-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name      VARCHAR(128) NOT NULL,
    record_id       UUID NOT NULL,
    operation       VARCHAR(16) NOT NULL,
    old_values      JSONB,
    new_values      JSONB,
    actor           UUID NOT NULL,
    actor_ip        INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_audit_operation CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(record_id);
CREATE INDEX idx_audit_log_actor ON audit_log(actor);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
```

### 2.8 Deduplication Hash Index

```sql
-- ============================================================
-- DEDUPLICATION
-- ============================================================

CREATE TABLE dedup_hash_index (
    content_hash    VARCHAR(64) PRIMARY KEY,
    reference_count INTEGER NOT NULL DEFAULT 1,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    storage_location TEXT NOT NULL,
    size_bytes      BIGINT NOT NULL
);

CREATE INDEX idx_dedup_hash ON dedup_hash_index(content_hash);
CREATE INDEX idx_dedup_last_accessed ON dedup_hash_index(last_accessed_at);
```

### 2.9 Row-Level Security

```sql
-- ============================================================
-- ROW-LEVEL SECURITY
-- ============================================================

ALTER TABLE policies ENABLE ROW LEVEL SECURITY;

CREATE POLICY policies_org_isolation ON policies
    USING (metadata->>'org_id' = current_setting('app.current_org_id', true)::uuid);

ALTER TABLE enforcement_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY enforcement_admin_all ON enforcement_actions
    FOR ALL TO grc_admin USING (true);

CREATE POLICY enforcement_user_own ON enforcement_actions
    FOR SELECT TO grc_app
    USING (triggered_by = current_setting('app.current_user_id', true)::uuid);

ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY assessments_admin_all ON assessments
    FOR ALL TO grc_admin USING (true);

CREATE POLICY assessments_lead_own ON assessments
    FOR SELECT TO grc_app
    USING (lead_assessor = current_setting('app.current_user_id', true)::uuid);

ALTER TABLE compliance_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY compliance_admin_all ON compliance_status
    FOR ALL TO grc_admin USING (true);

CREATE POLICY compliance_read_all ON compliance_status
    FOR SELECT TO grc_readonly USING (true);
```

### 2.10 Database Roles

```sql
-- ============================================================
-- DATABASE ROLES
-- ============================================================

CREATE ROLE grc_app WITH LOGIN;
GRANT USAGE ON SCHEMA grc_claw TO grc_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA grc_claw TO grc_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA grc_claw TO grc_app;

CREATE ROLE grc_readonly WITH LOGIN;
GRANT USAGE ON SCHEMA grc_claw TO grc_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA grc_claw TO grc_readonly;

CREATE ROLE grc_backup WITH LOGIN;
GRANT USAGE ON SCHEMA grc_claw TO grc_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA grc_claw TO grc_backup;

CREATE ROLE grc_admin WITH LOGIN;
GRANT ALL PRIVILEGES ON SCHEMA grc_claw TO grc_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA grc_claw TO grc_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA grc_claw TO grc_admin;
```

### 2.11 Triggers for Audit and Timestamps

```sql
-- ============================================================
-- TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_policy_clauses_updated_at
    BEFORE UPDATE ON policy_clauses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_enforcement_actions_updated_at
    BEFORE UPDATE ON enforcement_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_assessments_updated_at
    BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_assessment_findings_updated_at
    BEFORE UPDATE ON assessment_findings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_compliance_frameworks_updated_at
    BEFORE UPDATE ON compliance_frameworks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_compliance_controls_updated_at
    BEFORE UPDATE ON compliance_controls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_compliance_mappings_updated_at
    BEFORE UPDATE ON compliance_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_compliance_status_updated_at
    BEFORE UPDATE ON compliance_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit log trigger
CREATE OR REPLACE FUNCTION audit_log_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (table_name, record_id, operation, old_values, actor)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), current_setting('app.current_user_id', true)::uuid);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, actor)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), current_setting('app.current_user_id', true)::uuid);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (table_name, record_id, operation, new_values, actor)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), current_setting('app.current_user_id', true)::uuid);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_policies_audit
    AFTER INSERT OR UPDATE OR DELETE ON policies
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger();

CREATE TRIGGER trg_enforcement_actions_audit
    AFTER INSERT OR UPDATE OR DELETE ON enforcement_actions
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger();

CREATE TRIGGER trg_assessments_audit
    AFTER INSERT OR UPDATE OR DELETE ON assessments
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger();

CREATE TRIGGER trg_compliance_status_audit
    AFTER INSERT OR UPDATE OR DELETE ON compliance_status
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger();
```

### 2.12 Views for Monitoring

```sql
-- ============================================================
-- MONITORING VIEWS
-- ============================================================

CREATE VIEW v_storage_performance AS
SELECT
    schemaname,
    relname AS table_name,
    seq_scan,
    idx_scan,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze,
    pg_total_relation_size(relid) AS total_size_bytes,
    pg_relation_size(relid) AS table_size_bytes,
    pg_indexes_size(relid) AS index_size_bytes
FROM pg_stat_user_tables
JOIN pg_class ON relname = relname
ORDER BY pg_total_relation_size(relid) DESC;

CREATE VIEW v_enforcement_summary AS
SELECT
    ea.id,
    ea.action_key,
    ea.action_type,
    ea.status,
    ea.priority,
    ea.target_type,
    ea.target_id,
    p.policy_key,
    p.title AS policy_title,
    ea.triggered_at,
    ea.completed_at,
    EXTRACT(EPOCH FROM (ea.completed_at - ea.triggered_at)) AS duration_seconds
FROM enforcement_actions ea
LEFT JOIN policies p ON ea.policy_id = p.id;

CREATE VIEW v_compliance_posture AS
SELECT
    cf.framework_key,
    cf.name AS framework_name,
    cc.control_key,
    cc.title AS control_title,
    cs.target_id,
    cs.target_type,
    cs.status,
    cs.evaluated_at,
    cs.next_review_at
FROM compliance_frameworks cf
JOIN compliance_controls cc ON cf.id = cc.framework_id
LEFT JOIN compliance_status cs ON cc.id = cs.control_id
ORDER BY cf.framework_key, cc.control_key;
```

---

## 3. MongoDB Schemas

### 3.1 Evidence Collection

```javascript
// ============================================================
// EVIDENCE COLLECTION
// ============================================================

db.createCollection("evidence", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["evidence_id", "policy_id", "source", "evidence_type", "content", "context", "validation", "retention_class", "created_at"],
            properties: {
                evidence_id: { bsonType: "string" },
                policy_id: { bsonType: "string" },
                assessment_id: { bsonType: "string" },
                source: {
                    bsonType: "object",
                    required: ["type", "system", "collection_method"],
                    properties: {
                        type: { enum: ["scan", "audit", "manual", "api", "log"] },
                        system: { bsonType: "string" },
                        collection_method: { bsonType: "string" }
                    }
                },
                evidence_type: {
                    enum: ["config", "log", "metric", "screenshot", "report", "attestation"]
                },
                content: {
                    bsonType: "object",
                    required: ["format", "data", "hash"],
                    properties: {
                        format: { enum: ["json", "text", "binary", "image"] },
                        data: {},
                        hash: { bsonType: "string" }
                    }
                },
                context: {
                    bsonType: "object",
                    required: ["environment", "region", "timestamp"],
                    properties: {
                        environment: { enum: ["prod", "staging", "dev"] },
                        region: { bsonType: "string" },
                        timestamp: { bsonType: "date" },
                        metadata: { bsonType: "object" }
                    }
                },
                validation: {
                    bsonType: "object",
                    required: ["status"],
                    properties: {
                        status: { enum: ["pending", "validated", "rejected", "expired"] },
                        validated_by: { bsonType: "string" },
                        validated_at: { bsonType: "date" },
                        confidence_score: { bsonType: "double", minimum: 0.0, maximum: 1.0 }
                    }
                },
                retention_class: {
                    enum: ["standard", "extended", "permanent", "ephemeral"]
                },
                legal_hold: { bsonType: "bool" },
                legal_hold_reason: { bsonType: "string" },
                lifecycle_stage: {
                    enum: ["active", "warm", "cold", "purge", "frozen"]
                },
                stage_changed_at: { bsonType: "date" },
                compression_enabled: { bsonType: "bool" },
                original_size_bytes: { bsonType: "long" },
                compressed_size_bytes: { bsonType: "long" },
                created_at: { bsonType: "date" },
                expires_at: { bsonType: "date" }
            }
        }
    }
});

// Evidence indexes
db.evidence.createIndex({ "evidence_id": 1 }, { unique: true });
db.evidence.createIndex({ "policy_id": 1, "validation.status": 1, "created_at": -1 });
db.evidence.createIndex({ "assessment_id": 1 });
db.evidence.createIndex({ "evidence_type": 1 });
db.evidence.createIndex({ "source.type": 1 });
db.evidence.createIndex({ "source.system": 1 });
db.evidence.createIndex({ "context.environment": 1 });
db.evidence.createIndex({ "context.region": 1 });
db.evidence.createIndex({ "validation.status": 1 });
db.evidence.createIndex({ "retention_class": 1 });
db.evidence.createIndex({ "lifecycle_stage": 1 });
db.evidence.createIndex({ "created_at": -1 });
db.evidence.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
db.evidence.createIndex({ "legal_hold": 1 }, { partialFilterExpression: { legal_hold: true } });
db.evidence.createIndex(
    { "content.data": "text", "source.system": "text" },
    { weights: { "content.data": 10, "source.system": 5 } }
);
db.evidence.createIndex({ "evidence_id": "hashed" });
db.evidence.createIndex(
    { "created_at": -1 },
    { partialFilterExpression: { "validation.status": "pending" } }
);
db.evidence.createIndex(
    { "expires_at": 1 },
    {
        expireAfterSeconds: 0,
        partialFilterExpression: { retention_class: "ephemeral" }
    }
);
```

### 3.2 Policy Versions Collection

```javascript
// ============================================================
// POLICY VERSIONS COLLECTION
// ============================================================

db.createCollection("policy_versions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["policy_id", "version", "full_text", "created_at"],
            properties: {
                policy_id: { bsonType: "string" },
                version: { bsonType: "int", minimum: 1 },
                full_text: { bsonType: "string" },
                change_summary: { bsonType: "string" },
                diff_from_previous: { bsonType: "string" },
                approved_by: { bsonType: "string" },
                approved_at: { bsonType: "date" },
                created_at: { bsonType: "date" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

db.policy_versions.createIndex({ "policy_id": 1, "version": -1 });
db.policy_versions.createIndex({ "created_at": -1 });
db.policy_versions.createIndex({ "approved_by": 1 });
```

### 3.3 Assessment Reports Collection

```javascript
// ============================================================
// ASSESSMENT REPORTS COLLECTION
// ============================================================

db.createCollection("assessment_reports", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["assessment_id", "report_format", "full_report", "generated_at"],
            properties: {
                assessment_id: { bsonType: "string" },
                report_format: { enum: ["pdf", "html", "markdown"] },
                full_report: { bsonType: "string" },
                executive_summary: { bsonType: "string" },
                detailed_findings: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                recommendations: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                appendices: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                generated_at: { bsonType: "date" },
                generated_by: { bsonType: "string" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

db.assessment_reports.createIndex({ "assessment_id": 1 });
db.assessment_reports.createIndex({ "report_format": 1 });
db.assessment_reports.createIndex({ "generated_at": -1 });
db.assessment_reports.createIndex({ "generated_by": 1 });
```

### 3.4 MongoDB Sharding (Production)

```javascript
// ============================================================
// SHARDING CONFIGURATION (Production)
// ============================================================

sh.enableSharding("grc_claw");
sh.shardCollection("grc_claw.evidence", { "policy_id": 1, "created_at": -1 });
sh.shardCollection("grc_claw.policy_versions", { "policy_id": 1, "version": -1 });
sh.shardCollection("grc_claw.assessment_reports", { "assessment_id": 1 });
```

---

## 4. Neo4j Graph Schema

### 4.1 Constraints

```cypher
// ============================================================
// NEO4J CONSTRAINTS
// ============================================================

CREATE CONSTRAINT policy_id_unique IF NOT EXISTS
FOR (p:Policy) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT policy_key_unique IF NOT EXISTS
FOR (p:Policy) REQUIRE p.policy_key IS UNIQUE;

CREATE CONSTRAINT enforcement_id_unique IF NOT EXISTS
FOR (e:EnforcementAction) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT enforcement_key_unique IF NOT EXISTS
FOR (e:EnforcementAction) REQUIRE e.action_key IS UNIQUE;

CREATE CONSTRAINT target_id_unique IF NOT EXISTS
FOR (t:Target) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
FOR (e:Evidence) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT compliance_framework_id_unique IF NOT EXISTS
FOR (cf:ComplianceFramework) REQUIRE cf.id IS UNIQUE;

CREATE CONSTRAINT compliance_control_id_unique IF NOT EXISTS
FOR (cc:ComplianceControl) REQUIRE cc.id IS UNIQUE;

CREATE CONSTRAINT compliance_status_id_unique IF NOT EXISTS
FOR (cs:ComplianceStatus) REQUIRE cs.id IS UNIQUE;

CREATE CONSTRAINT assessment_id_unique IF NOT EXISTS
FOR (a:Assessment) REQUIRE a.id IS UNIQUE;
```

### 4.2 Indexes

```cypher
// ============================================================
// NEO4J INDEXES
// ============================================================

CREATE INDEX policy_status_idx IF NOT EXISTS
FOR (p:Policy) ON (p.status);

CREATE INDEX policy_category_idx IF NOT EXISTS
FOR (p:Policy) ON (p.category);

CREATE INDEX enforcement_status_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.status);

CREATE INDEX enforcement_priority_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.priority);

CREATE INDEX enforcement_action_type_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.action_type);

CREATE INDEX target_type_idx IF NOT EXISTS
FOR (t:Target) ON (t.target_type);

CREATE INDEX compliance_status_idx IF NOT EXISTS
FOR (cs:ComplianceStatus) ON (cs.status);

CREATE INDEX assessment_status_idx IF NOT EXISTS
FOR (a:Assessment) ON (a.status);

CREATE INDEX assessment_type_idx IF NOT EXISTS
FOR (a:Assessment) ON (a.assessment_type);
```

### 4.3 Node Labels and Properties

```cypher
// ============================================================
// NODE LABELS AND PROPERTIES
// ============================================================

// Policy nodes
(:Policy {
    id: UUID,
    policy_key: String,
    title: String,
    category: String,
    status: String,
    version: Integer,
    effective_date: DateTime,
    expiry_date: DateTime
})

// Enforcement Action nodes
(:EnforcementAction {
    id: UUID,
    action_key: String,
    action_type: String,
    status: String,
    priority: String,
    triggered_at: DateTime,
    completed_at: DateTime
})

// Target nodes
(:Target {
    id: UUID,
    target_type: String,
    target_id: String
})

// Evidence nodes
(:Evidence {
    id: UUID,
    evidence_id: String,
    evidence_type: String,
    validation_status: String
})

// Compliance Framework nodes
(:ComplianceFramework {
    id: UUID,
    framework_key: String,
    name: String,
    version: String
})

// Compliance Control nodes
(:ComplianceControl {
    id: UUID,
    control_key: String,
    title: String,
    category: String
})

// Compliance Status nodes
(:ComplianceStatus {
    id: UUID,
    status: String,
    evaluated_at: DateTime
})

// Assessment nodes
(:Assessment {
    id: UUID,
    assessment_key: String,
    assessment_type: String,
    status: String,
    score: Float
})
```

### 4.4 Relationship Types

```cypher
// ============================================================
// RELATIONSHIP TYPES
// ============================================================

// Enforcement relationships
(:EnforcementAction)-[:ENFORCES]->(:Policy)
(:EnforcementAction)-[:TARGETS]->(:Target)
(:EnforcementAction)-[:TRIGGERED_BY]->(:Evidence)
(:EnforcementAction)-[:DEPENDS_ON]->(:EnforcementAction)
(:EnforcementAction)-[:SUPERSEDED_BY]->(:EnforcementAction)

// Compliance relationships
(:ComplianceFramework)-[:CONTAINS]->(:ComplianceControl)
(:ComplianceControl)-[:SATISFIED_BY {coverage: String}]->(:Policy)
(:ComplianceControl)-[:ASSESSED_BY]->(:Assessment)
(:ComplianceControl)-[:HAS_STATUS]->(:ComplianceStatus)
(:Policy)-[:MAPS_TO]->(:ComplianceControl)

// Assessment relationships
(:Assessment)-[:EVALUATES]->(:Target)
(:Assessment)-[:PRODUCES]->(:Evidence)
(:Assessment)-[:IDENTIFIES]->(:Finding)

// Policy relationships
(:Policy)-[:SUPERSEDES]->(:Policy)
(:Policy)-[:CONFLICTS_WITH]->(:Policy)
(:Policy)-[:DERIVES_FROM]->(:Policy)
(:Policy)-[:RELATED_TO]->(:Policy)
```

### 4.5 Graph Data Population

```cypher
// ============================================================
// GRAPH DATA POPULATION
// ============================================================

// Sync policies from PostgreSQL
MATCH (p:Policy)
WHERE p.id = $policy_id
SET p.policy_key = $policy_key,
    p.title = $title,
    p.category = $category,
    p.status = $status,
    p.version = $version;

// Create enforcement action nodes
CREATE (e:EnforcementAction {
    id: $id,
    action_key: $action_key,
    action_type: $action_type,
    status: $status,
    priority: $priority,
    triggered_at: $triggered_at,
    completed_at: $completed_at
});

// Create relationships
MATCH (e:EnforcementAction {id: $enforcement_id})
MATCH (p:Policy {id: $policy_id})
CREATE (e)-[:ENFORCES]->(p);

MATCH (e:EnforcementAction {id: $enforcement_id})
MATCH (t:Target {id: $target_id})
CREATE (e)-[:TARGETS]->(t);

MATCH (e:EnforcementAction {id: $enforcement_id})
MATCH (ev:Evidence {id: $evidence_id})
CREATE (e)-[:TRIGGERED_BY]->(ev);

// Compliance graph
MATCH (cf:ComplianceFramework {id: $framework_id})
MATCH (cc:ComplianceControl {id: $control_id})
CREATE (cf)-[:CONTAINS]->(cc);

MATCH (cc:ComplianceControl {id: $control_id})
MATCH (p:Policy {id: $policy_id})
CREATE (cc)-[:SATISFIED_BY {coverage: $coverage}]->(p);

MATCH (cc:ComplianceControl {id: $control_id})
MATCH (a:Assessment {id: $assessment_id})
CREATE (cc)-[:ASSESSED_BY]->(a);

MATCH (cc:ComplianceControl {id: $control_id})
MATCH (cs:ComplianceStatus {id: $status_id})
CREATE (cc)-[:HAS_STATUS]->(cs);
```

### 4.6 Impact Analysis Queries

```cypher
// ============================================================
// IMPACT ANALYSIS QUERIES
// ============================================================

// Find all enforcement actions targeting a specific model
MATCH (e:EnforcementAction)-[:TARGETS]->(t:Target {target_type: 'model', target_id: $model_id})
RETURN e.id, e.action_key, e.action_type, e.status, e.priority
ORDER BY e.triggered_at DESC;

// Find blast radius: if this model is blocked, which pipelines are affected?
MATCH (e:EnforcementAction)-[:TARGETS]->(t:Target {target_id: $model_id})
MATCH (e)-[:ENFORCES]->(p:Policy)
RETURN p.policy_key, p.title, e.action_type, e.status;

// Find all policies affected by a compliance control change
MATCH (cc:ComplianceControl {control_key: $control_key})<-[:MAPS_TO]-(p:Policy)
RETURN p.policy_key, p.title, p.status;

// Find enforcement dependency chain
MATCH path = (e1:EnforcementAction {action_key: $action_key})-[:DEPENDS_ON*]->(e2:EnforcementAction)
RETURN path;

// Find all evidence supporting a compliance control
MATCH (cc:ComplianceControl {control_key: $control_id})<-[:SATISFIED_BY]-(p:Policy)
MATCH (e:EnforcementAction)-[:ENFORCES]->(p)
MATCH (e)-[:TRIGGERED_BY]->(ev:Evidence)
RETURN ev.evidence_id, ev.evidence_type, ev.validation_status;
```

---

## 5. TimescaleDB Hypertables

### 5.1 Hypertable Creation

```sql
-- ============================================================
-- TIMESCALEDB HYPERTABLES
-- ============================================================

CREATE TABLE evidence_metrics (
    time            TIMESTAMPTZ NOT NULL,
    evidence_id     UUID NOT NULL,
    policy_id       UUID NOT NULL,
    metric_name     VARCHAR(128) NOT NULL,
    metric_value    DOUBLE PRECISION NOT NULL,
    unit            VARCHAR(32),
    labels          JSONB,
    source          VARCHAR(128)
);

SELECT create_hypertable('evidence_metrics', 'time');
SELECT set_chunk_time_interval('evidence_metrics', INTERVAL '1 day');

ALTER TABLE evidence_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'policy_id, metric_name',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('evidence_metrics', INTERVAL '7 days');
SELECT add_retention_policy('evidence_metrics', INTERVAL '1 year');

CREATE INDEX idx_evidence_metrics_policy ON evidence_metrics(policy_id, time DESC);
CREATE INDEX idx_evidence_metrics_name ON evidence_metrics(metric_name, time DESC);
CREATE INDEX idx_evidence_metrics_evidence ON evidence_metrics(evidence_id, time DESC);
CREATE INDEX idx_evidence_metrics_source ON evidence_metrics(source, time DESC);
CREATE INDEX idx_evidence_metrics_time ON evidence_metrics USING BRIN(time)
    WITH (pages_per_range = 32);
CREATE INDEX idx_evidence_metrics_labels ON evidence_metrics USING GIN(labels jsonb_path_ops);
```

### 5.2 Continuous Aggregates

```sql
-- ============================================================
-- CONTINUOUS AGGREGATES
-- ============================================================

CREATE MATERIALIZED VIEW evidence_metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    policy_id,
    metric_name,
    source,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    COUNT(*) AS sample_count
FROM evidence_metrics
GROUP BY bucket, policy_id, metric_name, source;

CREATE MATERIALIZED VIEW evidence_metrics_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    policy_id,
    metric_name,
    source,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    STDDEV(metric_value) AS stddev_value,
    COUNT(*) AS sample_count
FROM evidence_metrics
GROUP BY bucket, policy_id, metric_name, source;

SELECT add_continuous_aggregate_policy('evidence_metrics_hourly',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('evidence_metrics_daily',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');
```

### 5.3 Partition Management

```sql
-- ============================================================
// PARTITION MANAGEMENT
// ============================================================

CREATE TABLE evidence_metrics_2026_10 PARTITION OF evidence_metrics
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE evidence_metrics_2026_11 PARTITION OF evidence_metrics
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE evidence_metrics_2026_12 PARTITION OF evidence_metrics
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    partition_name TEXT := 'evidence_metrics_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date DATE := partition_date;
    end_date DATE := partition_date + INTERVAL '1 month';
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF evidence_metrics FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('create-partition', '0 0 25 * *', 'SELECT create_monthly_partition()');
```

---

## 6. Database Migration Scripts

### 6.1 Migration Framework Setup

```python
# migrations/env.py
"""Alembic migration environment for GRC_Claw."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 6.2 Initial Migration

```python
# migrations/versions/001_initial_schema.py
"""Initial GRC_Claw schema

Revision ID: 001
Revises: 
Create Date: 2026-10-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"')
    
    op.execute('CREATE SCHEMA IF NOT EXISTS grc_claw')
    op.execute('CREATE SCHEMA IF NOT EXISTS grc_claw_archive')
    op.execute('CREATE SCHEMA IF NOT EXISTS grc_claw_audit')
    
    # Policies table
    op.create_table(
        'policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_key', sa.String(128), unique=True, nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('effective_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('expiry_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('legal_hold_reason', sa.Text(), nullable=True),
        sa.Column('lifecycle_stage', sa.String(32), nullable=False, server_default='active'),
        sa.Column('stage_changed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('compression_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('compressed_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('original_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        schema='grc_claw'
    )
    
    op.create_index('idx_policies_category', 'policies', ['category'], schema='grc_claw')
    op.create_index('idx_policies_status', 'policies', ['status'], schema='grc_claw')
    op.create_index('idx_policies_effective', 'policies', ['effective_date', 'expiry_date'], schema='grc_claw')
    op.create_index('idx_policies_owner', 'policies', ['owner_id'], schema='grc_claw')
    op.create_index('idx_policies_lifecycle', 'policies', ['lifecycle_stage'], schema='grc_claw')
    op.create_index('idx_policies_legal_hold', 'policies', ['legal_hold'], schema='grc_claw',
                    postgresql_where=sa.text('legal_hold = true'))
    op.create_index('idx_policies_active', 'policies', ['category', 'status'], schema='grc_claw',
                    postgresql_where=sa.text("status = 'active'"))
    op.create_index('idx_policies_metadata', 'policies', ['metadata'], schema='grc_claw',
                    postgresql_using='gin', postgresql_ops={'metadata': 'jsonb_path_ops'})
    
    # Policy clauses table
    op.create_table(
        'policy_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clause_number', sa.String(32), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('enforcement_type', sa.String(32), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('policy_id', 'clause_number', name='uq_policy_clause'),
        schema='grc_claw'
    )
    
    op.create_index('idx_policy_clauses_policy', 'policy_clauses', ['policy_id'], schema='grc_claw')
    op.create_index('idx_policy_clauses_severity', 'policy_clauses', ['severity'], schema='grc_claw')
    
    # Policy relationships table
    op.create_table(
        'policy_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_policy', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_policy', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(64), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('source_policy', 'target_policy', 'relation_type', name='uq_policy_relationship'),
        schema='grc_claw'
    )
    
    op.create_index('idx_policy_rel_source', 'policy_relationships', ['source_policy'], schema='grc_claw')
    op.create_index('idx_policy_rel_target', 'policy_relationships', ['target_policy'], schema='grc_claw')
    
    # Enforcement actions table
    op.create_table(
        'enforcement_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('action_key', sa.String(128), unique=True, nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id'), nullable=False),
        sa.Column('clause_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policy_clauses.id'), nullable=True),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action_type', sa.String(64), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=False),
        sa.Column('target_id', sa.String(256), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('triggered_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('triggered_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('executed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('rollback_action', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('legal_hold_reason', sa.Text(), nullable=True),
        sa.Column('lifecycle_stage', sa.String(32), nullable=False, server_default='active'),
        sa.Column('stage_changed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw'
    )
    
    op.create_index('idx_enforcement_policy', 'enforcement_actions', ['policy_id'], schema='grc_claw')
    op.create_index('idx_enforcement_status', 'enforcement_actions', ['status'], schema='grc_claw')
    op.create_index('idx_enforcement_target', 'enforcement_actions', ['target_type', 'target_id'], schema='grc_claw')
    op.create_index('idx_enforcement_triggered', 'enforcement_actions', ['triggered_at'], schema='grc_claw')
    op.create_index('idx_enforcement_priority', 'enforcement_actions', ['priority'], schema='grc_claw')
    op.create_index('idx_enforcement_legal_hold', 'enforcement_actions', ['legal_hold'], schema='grc_claw',
                    postgresql_where=sa.text('legal_hold = true'))
    op.create_index('idx_enforcement_active', 'enforcement_actions', ['policy_id', 'status', 'priority'], schema='grc_claw',
                    postgresql_where=sa.text("status IN ('pending', 'in_progress')"))
    op.create_index('idx_enforcement_result', 'enforcement_actions', ['result'], schema='grc_claw',
                    postgresql_using='gin', postgresql_ops={'result': 'jsonb_path_ops'})
    
    # Enforcement audit log table
    op.create_table(
        'enforcement_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('action_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.enforcement_actions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('actor', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw'
    )
    
    op.create_index('idx_enforcement_audit_action', 'enforcement_audit_log', ['action_id'], schema='grc_claw')
    op.create_index('idx_enforcement_audit_created', 'enforcement_audit_log', ['created_at'], schema='grc_claw')
    
    # Assessments table
    op.create_table(
        'assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_key', sa.String(128), unique=True, nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assessment_type', sa.String(64), nullable=False),
        sa.Column('target_id', sa.String(256), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='planned'),
        sa.Column('methodology', sa.String(128), nullable=True),
        sa.Column('score', sa.Numeric(5, 2), nullable=True),
        sa.Column('risk_level', sa.String(16), nullable=True),
        sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('next_assessment_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('lead_assessor', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('legal_hold_reason', sa.Text(), nullable=True),
        sa.Column('lifecycle_stage', sa.String(32), nullable=False, server_default='active'),
        sa.Column('stage_changed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=False),
        schema='grc_claw'
    )
    
    op.create_index('idx_assessments_type', 'assessments', ['assessment_type'], schema='grc_claw')
    op.create_index('idx_assessments_status', 'assessments', ['status'], schema='grc_claw')
    op.create_index('idx_assessments_target', 'assessments', ['target_type', 'target_id'], schema='grc_claw')
    op.create_index('idx_assessments_lead', 'assessments', ['lead_assessor'], schema='grc_claw')
    op.create_index('idx_assessments_next', 'assessments', ['next_assessment_at'], schema='grc_claw')
    op.create_index('idx_assessments_legal_hold', 'assessments', ['legal_hold'], schema='grc_claw',
                    postgresql_where=sa.text('legal_hold = true'))
    
    # Assessment findings table
    op.create_table(
        'assessment_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('finding_key', sa.String(128), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('category', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='open'),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id'), nullable=True),
        sa.Column('evidence_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('remediated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('remediated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('due_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('assessment_id', 'finding_key', name='uq_finding_key'),
        schema='grc_claw'
    )
    
    op.create_index('idx_findings_assessment', 'assessment_findings', ['assessment_id'], schema='grc_claw')
    op.create_index('idx_findings_status', 'assessment_findings', ['status'], schema='grc_claw')
    op.create_index('idx_findings_severity', 'assessment_findings', ['severity'], schema='grc_claw')
    op.create_index('idx_findings_policy', 'assessment_findings', ['policy_id'], schema='grc_claw')
    op.create_index('idx_findings_due_date', 'assessment_findings', ['due_date'], schema='grc_claw')
    
    # Assessment evidence links table
    op.create_table(
        'assessment_evidence_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.assessment_findings.id'), nullable=True),
        sa.Column('relevance_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('assessment_id', 'evidence_id', 'finding_id', name='uq_assessment_evidence'),
        schema='grc_claw'
    )
    
    op.create_index('idx_assessment_evidence_links_assessment', 'assessment_evidence_links', ['assessment_id'], schema='grc_claw')
    op.create_index('idx_assessment_evidence_links_evidence', 'assessment_evidence_links', ['evidence_id'], schema='grc_claw')
    op.create_index('idx_assessment_evidence_links_finding', 'assessment_evidence_links', ['finding_id'], schema='grc_claw')
    
    # Compliance frameworks table
    op.create_table(
        'compliance_frameworks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('framework_key', sa.String(128), unique=True, nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('version', sa.String(64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('authority', sa.String(256), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw'
    )
    
    # Compliance controls table
    op.create_table(
        'compliance_controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.compliance_frameworks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('control_key', sa.String(128), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(128), nullable=False),
        sa.Column('guidance', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('framework_id', 'control_key', name='uq_control_key'),
        schema='grc_claw'
    )
    
    op.create_index('idx_compliance_controls_framework', 'compliance_controls', ['framework_id'], schema='grc_claw')
    op.create_index('idx_compliance_controls_category', 'compliance_controls', ['category'], schema='grc_claw')
    
    # Compliance mappings table
    op.create_table(
        'compliance_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.compliance_controls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.policies.id'), nullable=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.assessments.id'), nullable=True),
        sa.Column('mapping_type', sa.String(64), nullable=False),
        sa.Column('coverage', sa.String(16), nullable=False, server_default='partial'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('mapped_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mapped_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw'
    )
    
    op.create_index('idx_compliance_mappings_control', 'compliance_mappings', ['control_id'], schema='grc_claw')
    op.create_index('idx_compliance_mappings_policy', 'compliance_mappings', ['policy_id'], schema='grc_claw')
    op.create_index('idx_compliance_mappings_assessment', 'compliance_mappings', ['assessment_id'], schema='grc_claw')
    
    # Compliance status table
    op.create_table(
        'compliance_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.compliance_frameworks.id'), nullable=False),
        sa.Column('control_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.compliance_controls.id'), nullable=False),
        sa.Column('target_id', sa.String(256), nullable=False),
        sa.Column('target_type', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='unknown'),
        sa.Column('evidence_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.assessments.id'), nullable=True),
        sa.Column('evaluated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('evaluated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('next_review_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('legal_hold_reason', sa.Text(), nullable=True),
        sa.Column('lifecycle_stage', sa.String(32), nullable=False, server_default='active'),
        sa.Column('stage_changed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('framework_id', 'control_id', 'target_id', 'target_type', name='uq_compliance_status'),
        schema='grc_claw'
    )
    
    op.create_index('idx_compliance_status_framework', 'compliance_status', ['framework_id'], schema='grc_claw')
    op.create_index('idx_compliance_status_control', 'compliance_status', ['control_id'], schema='grc_claw')
    op.create_index('idx_compliance_status_target', 'compliance_status', ['target_type', 'target_id'], schema='grc_claw')
    op.create_index('idx_compliance_status_review', 'compliance_status', ['next_review_at'], schema='grc_claw')
    op.create_index('idx_compliance_status_legal_hold', 'compliance_status', ['legal_hold'], schema='grc_claw',
                    postgresql_where=sa.text('legal_hold = true'))
    op.create_index('idx_compliance_status_lookup', 'compliance_status',
                    ['framework_id', 'control_id', 'target_type', 'target_id'],
                    schema='grc_claw',
                    postgresql_include=['status', 'evaluated_at', 'next_review_at'])
    
    # Compliance attestations table
    op.create_table(
        'compliance_attestations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('compliance_status_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grc_claw.compliance_status.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attestation_type', sa.String(64), nullable=False),
        sa.Column('attested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attested_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('valid_from', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('valid_until', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw'
    )
    
    op.create_index('idx_compliance_attestations_status', 'compliance_attestations', ['compliance_status_id'], schema='grc_claw')
    op.create_index('idx_compliance_attestations_valid', 'compliance_attestations', ['valid_from', 'valid_until'], schema='grc_claw')
    
    # Audit log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('table_name', sa.String(128), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation', sa.String(16), nullable=False),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('actor', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_ip', postgresql.INET(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='grc_claw_audit'
    )
    
    op.create_index('idx_audit_log_table', 'audit_log', ['table_name'], schema='grc_claw_audit')
    op.create_index('idx_audit_log_record', 'audit_log', ['record_id'], schema='grc_claw_audit')
    op.create_index('idx_audit_log_actor', 'audit_log', ['actor'], schema='grc_claw_audit')
    op.create_index('idx_audit_log_created', 'audit_log', ['created_at'], schema='grc_claw_audit')
    op.create_index('idx_audit_log_table_record', 'audit_log', ['table_name', 'record_id'], schema='grc_claw_audit')
    
    # Dedup hash index table
    op.create_table(
        'dedup_hash_index',
        sa.Column('content_hash', sa.String(64), primary_key=True),
        sa.Column('reference_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('first_seen_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_accessed_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('storage_location', sa.Text(), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        schema='grc_claw'
    )
    
    op.create_index('idx_dedup_hash', 'dedup_hash_index', ['content_hash'], schema='grc_claw')
    op.create_index('idx_dedup_last_accessed', 'dedup_hash_index', ['last_accessed_at'], schema='grc_claw')
    
    # Create triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    for table in ['policies', 'policy_clauses', 'enforcement_actions', 'assessments',
                  'assessment_findings', 'compliance_frameworks', 'compliance_controls',
                  'compliance_mappings', 'compliance_status']:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
                BEFORE UPDATE ON grc_claw.{table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_log_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO grc_claw_audit.audit_log (table_name, record_id, operation, old_values, actor)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), current_setting('app.current_user_id', true)::uuid);
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO grc_claw_audit.audit_log (table_name, record_id, operation, old_values, new_values, actor)
                VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), current_setting('app.current_user_id', true)::uuid);
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO grc_claw_audit.audit_log (table_name, record_id, operation, new_values, actor)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), current_setting('app.current_user_id', true)::uuid);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    for table in ['policies', 'enforcement_actions', 'assessments', 'compliance_status']:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_audit
                AFTER INSERT OR UPDATE OR DELETE ON grc_claw.{table}
                FOR EACH ROW EXECUTE FUNCTION audit_log_trigger();
        """)
    
    # Create views
    op.execute("""
        CREATE VIEW grc_claw.v_storage_performance AS
        SELECT
            schemaname,
            relname AS table_name,
            seq_scan,
            idx_scan,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
            pg_total_relation_size(relid) AS total_size_bytes,
            pg_relation_size(relid) AS table_size_bytes,
            pg_indexes_size(relid) AS index_size_bytes
        FROM pg_stat_user_tables
        JOIN pg_class ON relname = relname
        ORDER BY pg_total_relation_size(relid) DESC;
    """)
    
    op.execute("""
        CREATE VIEW grc_claw.v_enforcement_summary AS
        SELECT
            ea.id,
            ea.action_key,
            ea.action_type,
            ea.status,
            ea.priority,
            ea.target_type,
            ea.target_id,
            p.policy_key,
            p.title AS policy_title,
            ea.triggered_at,
            ea.completed_at,
            EXTRACT(EPOCH FROM (ea.completed_at - ea.triggered_at)) AS duration_seconds
        FROM grc_claw.enforcement_actions ea
        LEFT JOIN grc_claw.policies p ON ea.policy_id = p.id;
    """)
    
    op.execute("""
        CREATE VIEW grc_claw.v_compliance_posture AS
        SELECT
            cf.framework_key,
            cf.name AS framework_name,
            cc.control_key,
            cc.title AS control_title,
            cs.target_id,
            cs.target_type,
            cs.status,
            cs.evaluated_at,
            cs.next_review_at
        FROM grc_claw.compliance_frameworks cf
        JOIN grc_claw.compliance_controls cc ON cf.id = cc.framework_id
        LEFT JOIN grc_claw.compliance_status cs ON cc.id = cs.control_id
        ORDER BY cf.framework_key, cc.control_key;
    """)


def downgrade() -> None:
    op.execute('DROP VIEW IF EXISTS grc_claw.v_compliance_posture')
    op.execute('DROP VIEW IF EXISTS grc_claw.v_enforcement_summary')
    op.execute('DROP VIEW IF EXISTS grc_claw.v_storage_performance')
    
    for table in ['policies', 'enforcement_actions', 'assessments', 'compliance_status']:
        op.execute(f'DROP TRIGGER IF EXISTS trg_{table}_audit ON grc_claw.{table}')
    
    for table in ['policies', 'policy_clauses', 'enforcement_actions', 'assessments',
                  'assessment_findings', 'compliance_frameworks', 'compliance_controls',
                  'compliance_mappings', 'compliance_status']:
        op.execute(f'DROP TRIGGER IF EXISTS trg_{table}_updated_at ON grc_claw.{table}')
    
    op.execute('DROP FUNCTION IF EXISTS audit_log_trigger()')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    op.drop_table('dedup_hash_index', schema='grc_claw')
    op.drop_table('audit_log', schema='grc_claw_audit')
    op.drop_table('compliance_attestations', schema='grc_claw')
    op.drop_table('compliance_status', schema='grc_claw')
    op.drop_table('compliance_mappings', schema='grc_claw')
    op.drop_table('compliance_controls', schema='grc_claw')
    op.drop_table('compliance_frameworks', schema='grc_claw')
    op.drop_table('assessment_evidence_links', schema='grc_claw')
    op.drop_table('assessment_findings', schema='grc_claw')
    op.drop_table('assessments', schema='grc_claw')
    op.drop_table('enforcement_audit_log', schema='grc_claw')
    op.drop_table('enforcement_actions', schema='grc_claw')
    op.drop_table('policy_relationships', schema='grc_claw')
    op.drop_table('policy_clauses', schema='grc_claw')
    op.drop_table('policies', schema='grc_claw')
    
    op.execute('DROP SCHEMA IF EXISTS grc_claw_audit')
    op.execute('DROP SCHEMA IF EXISTS grc_claw_archive')
    op.execute('DROP SCHEMA IF EXISTS grc_claw')
```

### 6.3 TimescaleDB Migration

```python
# migrations/versions/002_timescaledb_hypertables.py
"""TimescaleDB hypertables for GRC_Claw

Revision ID: 002
Revises: 001
Create Date: 2026-10-01 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb')
    
    op.create_table(
        'evidence_metrics',
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(128), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(32), nullable=True),
        sa.Column('labels', postgresql.JSONB(), nullable=True),
        sa.Column('source', sa.String(128), nullable=True),
        schema='grc_claw'
    )
    
    op.execute("SELECT create_hypertable('grc_claw.evidence_metrics', 'time')")
    op.execute("SELECT set_chunk_time_interval('grc_claw.evidence_metrics', INTERVAL '1 day')")
    
    op.execute("""
        ALTER TABLE grc_claw.evidence_metrics SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'policy_id, metric_name',
            timescaledb.compress_orderby = 'time DESC'
        )
    """)
    
    op.execute("SELECT add_compression_policy('grc_claw.evidence_metrics', INTERVAL '7 days')")
    op.execute("SELECT add_retention_policy('grc_claw.evidence_metrics', INTERVAL '1 year')")
    
    op.create_index('idx_evidence_metrics_policy', 'evidence_metrics', ['policy_id', sa.text('time DESC')], schema='grc_claw')
    op.create_index('idx_evidence_metrics_name', 'evidence_metrics', ['metric_name', sa.text('time DESC')], schema='grc_claw')
    op.create_index('idx_evidence_metrics_evidence', 'evidence_metrics', ['evidence_id', sa.text('time DESC')], schema='grc_claw')
    op.create_index('idx_evidence_metrics_source', 'evidence_metrics', ['source', sa.text('time DESC')], schema='grc_claw')
    op.create_index('idx_evidence_metrics_time', 'evidence_metrics', ['time'], schema='grc_claw',
                    postgresql_using='brin', postgresql_with={'pages_per_range': '32'})
    op.create_index('idx_evidence_metrics_labels', 'evidence_metrics', ['labels'], schema='grc_claw',
                    postgresql_using='gin', postgresql_ops={'labels': 'jsonb_path_ops'})
    
    op.execute("""
        CREATE MATERIALIZED VIEW grc_claw.evidence_metrics_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', time) AS bucket,
            policy_id,
            metric_name,
            source,
            AVG(metric_value) AS avg_value,
            MIN(metric_value) AS min_value,
            MAX(metric_value) AS max_value,
            COUNT(*) AS sample_count
        FROM grc_claw.evidence_metrics
        GROUP BY bucket, policy_id, metric_name, source;
    """)
    
    op.execute("""
        CREATE MATERIALIZED VIEW grc_claw.evidence_metrics_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', time) AS bucket,
            policy_id,
            metric_name,
            source,
            AVG(metric_value) AS avg_value,
            MIN(metric_value) AS min_value,
            MAX(metric_value) AS max_value,
            STDDEV(metric_value) AS stddev_value,
            COUNT(*) AS sample_count
        FROM grc_claw.evidence_metrics
        GROUP BY bucket, policy_id, metric_name, source;
    """)
    
    op.execute("""
        SELECT add_continuous_aggregate_policy('grc_claw.evidence_metrics_hourly',
            start_offset => INTERVAL '1 month',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour');
    """)
    
    op.execute("""
        SELECT add_continuous_aggregate_policy('grc_claw.evidence_metrics_daily',
            start_offset => INTERVAL '3 months',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day');
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS grc_claw.evidence_metrics_daily")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS grc_claw.evidence_metrics_hourly")
    
    op.drop_index('idx_evidence_metrics_labels', table_name='evidence_metrics', schema='grc_claw')
    op.drop_index('idx_evidence_metrics_time', table_name='evidence_metrics', schema='grc_claw')
    op.drop_index('idx_evidence_metrics_source', table_name='evidence_metrics', schema='grc_claw')
    op.drop_index('idx_evidence_metrics_evidence', table_name='evidence_metrics', schema='grc_claw')
    op.drop_index('idx_evidence_metrics_name', table_name='evidence_metrics', schema='grc_claw')
    op.drop_index('idx_evidence_metrics_policy', table_name='evidence_metrics', schema='grc_claw')
    
    op.drop_table('evidence_metrics', schema='grc_claw')
```

### 6.4 MongoDB Migration Script

```javascript
// migrations/mongodb/001_initial_collections.js
// MongoDB migration script for GRC_Claw

db = db.getSiblingDB('grc_claw');

// ============================================================
// EVIDENCE COLLECTION
// ============================================================

db.createCollection("evidence", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["evidence_id", "policy_id", "source", "evidence_type", "content", "context", "validation", "retention_class", "created_at"],
            properties: {
                evidence_id: { bsonType: "string" },
                policy_id: { bsonType: "string" },
                assessment_id: { bsonType: "string" },
                source: {
                    bsonType: "object",
                    required: ["type", "system", "collection_method"],
                    properties: {
                        type: { enum: ["scan", "audit", "manual", "api", "log"] },
                        system: { bsonType: "string" },
                        collection_method: { bsonType: "string" }
                    }
                },
                evidence_type: {
                    enum: ["config", "log", "metric", "screenshot", "report", "attestation"]
                },
                content: {
                    bsonType: "object",
                    required: ["format", "data", "hash"],
                    properties: {
                        format: { enum: ["json", "text", "binary", "image"] },
                        data: {},
                        hash: { bsonType: "string" }
                    }
                },
                context: {
                    bsonType: "object",
                    required: ["environment", "region", "timestamp"],
                    properties: {
                        environment: { enum: ["prod", "staging", "dev"] },
                        region: { bsonType: "string" },
                        timestamp: { bsonType: "date" },
                        metadata: { bsonType: "object" }
                    }
                },
                validation: {
                    bsonType: "object",
                    required: ["status"],
                    properties: {
                        status: { enum: ["pending", "validated", "rejected", "expired"] },
                        validated_by: { bsonType: "string" },
                        validated_at: { bsonType: "date" },
                        confidence_score: { bsonType: "double", minimum: 0.0, maximum: 1.0 }
                    }
                },
                retention_class: {
                    enum: ["standard", "extended", "permanent", "ephemeral"]
                },
                legal_hold: { bsonType: "bool" },
                legal_hold_reason: { bsonType: "string" },
                lifecycle_stage: {
                    enum: ["active", "warm", "cold", "purge", "frozen"]
                },
                stage_changed_at: { bsonType: "date" },
                compression_enabled: { bsonType: "bool" },
                original_size_bytes: { bsonType: "long" },
                compressed_size_bytes: { bsonType: "long" },
                created_at: { bsonType: "date" },
                expires_at: { bsonType: "date" }
            }
        }
    }
});

db.evidence.createIndex({ "evidence_id": 1 }, { unique: true });
db.evidence.createIndex({ "policy_id": 1, "validation.status": 1, "created_at": -1 });
db.evidence.createIndex({ "assessment_id": 1 });
db.evidence.createIndex({ "evidence_type": 1 });
db.evidence.createIndex({ "source.type": 1 });
db.evidence.createIndex({ "source.system": 1 });
db.evidence.createIndex({ "context.environment": 1 });
db.evidence.createIndex({ "context.region": 1 });
db.evidence.createIndex({ "validation.status": 1 });
db.evidence.createIndex({ "retention_class": 1 });
db.evidence.createIndex({ "lifecycle_stage": 1 });
db.evidence.createIndex({ "created_at": -1 });
db.evidence.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
db.evidence.createIndex({ "legal_hold": 1 }, { partialFilterExpression: { legal_hold: true } });
db.evidence.createIndex(
    { "content.data": "text", "source.system": "text" },
    { weights: { "content.data": 10, "source.system": 5 } }
);
db.evidence.createIndex({ "evidence_id": "hashed" });
db.evidence.createIndex(
    { "created_at": -1 },
    { partialFilterExpression: { "validation.status": "pending" } }
);
db.evidence.createIndex(
    { "expires_at": 1 },
    {
        expireAfterSeconds: 0,
        partialFilterExpression: { retention_class: "ephemeral" }
    }
);

// ============================================================
// POLICY VERSIONS COLLECTION
// ============================================================

db.createCollection("policy_versions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["policy_id", "version", "full_text", "created_at"],
            properties: {
                policy_id: { bsonType: "string" },
                version: { bsonType: "int", minimum: 1 },
                full_text: { bsonType: "string" },
                change_summary: { bsonType: "string" },
                diff_from_previous: { bsonType: "string" },
                approved_by: { bsonType: "string" },
                approved_at: { bsonType: "date" },
                created_at: { bsonType: "date" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

db.policy_versions.createIndex({ "policy_id": 1, "version": -1 });
db.policy_versions.createIndex({ "created_at": -1 });
db.policy_versions.createIndex({ "approved_by": 1 });

// ============================================================
// ASSESSMENT REPORTS COLLECTION
// ============================================================

db.createCollection("assessment_reports", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["assessment_id", "report_format", "full_report", "generated_at"],
            properties: {
                assessment_id: { bsonType: "string" },
                report_format: { enum: ["pdf", "html", "markdown"] },
                full_report: { bsonType: "string" },
                executive_summary: { bsonType: "string" },
                detailed_findings: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                recommendations: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                appendices: {
                    bsonType: "array",
                    items: { bsonType: "object" }
                },
                generated_at: { bsonType: "date" },
                generated_by: { bsonType: "string" },
                metadata: { bsonType: "object" }
            }
        }
    }
});

db.assessment_reports.createIndex({ "assessment_id": 1 });
db.assessment_reports.createIndex({ "report_format": 1 });
db.assessment_reports.createIndex({ "generated_at": -1 });
db.assessment_reports.createIndex({ "generated_by": 1 });

print("MongoDB migration 001 completed successfully");
```

### 6.5 Neo4j Migration Script

```cypher
// migrations/neo4j/001_initial_schema.cypher
// Neo4j migration script for GRC_Claw

// ============================================================
// CONSTRAINTS
// ============================================================

CREATE CONSTRAINT policy_id_unique IF NOT EXISTS
FOR (p:Policy) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT policy_key_unique IF NOT EXISTS
FOR (p:Policy) REQUIRE p.policy_key IS UNIQUE;

CREATE CONSTRAINT enforcement_id_unique IF NOT EXISTS
FOR (e:EnforcementAction) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT enforcement_key_unique IF NOT EXISTS
FOR (e:EnforcementAction) REQUIRE e.action_key IS UNIQUE;

CREATE CONSTRAINT target_id_unique IF NOT EXISTS
FOR (t:Target) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS
FOR (e:Evidence) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT compliance_framework_id_unique IF NOT EXISTS
FOR (cf:ComplianceFramework) REQUIRE cf.id IS UNIQUE;

CREATE CONSTRAINT compliance_control_id_unique IF NOT EXISTS
FOR (cc:ComplianceControl) REQUIRE cc.id IS UNIQUE;

CREATE CONSTRAINT compliance_status_id_unique IF NOT EXISTS
FOR (cs:ComplianceStatus) REQUIRE cs.id IS UNIQUE;

CREATE CONSTRAINT assessment_id_unique IF NOT EXISTS
FOR (a:Assessment) REQUIRE a.id IS UNIQUE;

// ============================================================
// INDEXES
// ============================================================

CREATE INDEX policy_status_idx IF NOT EXISTS
FOR (p:Policy) ON (p.status);

CREATE INDEX policy_category_idx IF NOT EXISTS
FOR (p:Policy) ON (p.category);

CREATE INDEX enforcement_status_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.status);

CREATE INDEX enforcement_priority_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.priority);

CREATE INDEX enforcement_action_type_idx IF NOT EXISTS
FOR (e:EnforcementAction) ON (e.action_type);

CREATE INDEX target_type_idx IF NOT EXISTS
FOR (t:Target) ON (t.target_type);

CREATE INDEX compliance_status_idx IF NOT EXISTS
FOR (cs:ComplianceStatus) ON (cs.status);

CREATE INDEX assessment_status_idx IF NOT EXISTS
FOR (a:Assessment) ON (a.status);

CREATE INDEX assessment_type_idx IF NOT EXISTS
FOR (a:Assessment) ON (a.assessment_type);
```

---

## 7. Seed Data Scripts

### 7.1 PostgreSQL Seed Data

```sql
-- ============================================================
-- SEED DATA
-- ============================================================

-- Insert sample policies
INSERT INTO grc_claw.policies (id, policy_key, title, description, category, status, version, effective_date, expiry_date, owner_id, metadata, created_by, updated_by)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'AI-ETHICS-001', 'AI Ethics Policy', 'Comprehensive AI ethics guidelines for responsible AI development and deployment', 'ethics', 'active', 1, '2026-01-01', '2027-01-01', '550e8400-e29b-41d4-a716-446655440000', '{"org_id": "550e8400-e29b-41d4-a716-446655440000", "department": "AI Governance"}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440002', 'DATA-PRIVACY-001', 'Data Privacy Policy', 'Data privacy and protection requirements for handling personal data', 'privacy', 'active', 1, '2026-01-01', '2027-01-01', '550e8400-e29b-41d4-a716-446655440000', '{"org_id": "550e8400-e29b-41d4-a716-446655440000", "department": "Data Protection"}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440003', 'MODEL-SAFETY-001', 'Model Safety Policy', 'Safety requirements for AI model development and deployment', 'safety', 'active', 1, '2026-01-01', '2027-01-01', '550e8400-e29b-41d4-a716-446655440000', '{"org_id": "550e8400-e29b-41d4-a716-446655440000", "department": "AI Safety"}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440004', 'FAIRNESS-001', 'Fairness and Bias Policy', 'Requirements for fairness and bias mitigation in AI systems', 'fairness', 'draft', 1, NULL, NULL, '550e8400-e29b-41d4-a716-446655440000', '{"org_id": "550e8400-e29b-41d4-a716-446655440000", "department": "AI Ethics"}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440005', 'ACCESS-CONTROL-001', 'Access Control Policy', 'Access control requirements for AI systems and data', 'access_control', 'active', 1, '2026-01-01', '2027-01-01', '550e8400-e29b-41d4-a716-446655440000', '{"org_id": "550e8400-e29b-41d4-a716-446655440000", "department": "Security"}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000');

-- Insert policy clauses
INSERT INTO grc_claw.policy_clauses (id, policy_id, clause_number, title, body, severity, enforcement_type, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', '1.1', 'Transparency Requirement', 'All AI systems must provide clear explanations for their decisions and actions.', 'high', 'automated', '{}'),
    ('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440001', '1.2', 'Human Oversight', 'Critical AI decisions must include human oversight and approval mechanisms.', 'critical', 'hybrid', '{}'),
    ('550e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440002', '2.1', 'Data Minimization', 'Only collect and process personal data that is strictly necessary for the specified purpose.', 'high', 'automated', '{}'),
    ('550e8400-e29b-41d4-a716-446655440104', '550e8400-e29b-41d4-a716-446655440002', '2.2', 'Consent Management', 'Obtain explicit consent from data subjects before processing their personal data.', 'critical', 'manual', '{}'),
    ('550e8400-e29b-41d4-a716-446655440105', '550e8400-e29b-41d4-a716-446655440003', '3.1', 'Model Validation', 'All AI models must undergo rigorous validation before deployment.', 'critical', 'hybrid', '{}');

-- Insert policy relationships
INSERT INTO grc_claw.policy_relationships (source_policy, target_policy, relation_type)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440003', 'related_to'),
    ('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440005', 'related_to'),
    ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440004', 'derives_from');

-- Insert compliance frameworks
INSERT INTO grc_claw.compliance_frameworks (id, framework_key, name, version, description, authority, effective_date, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440201', 'NIST-AI-RMF', 'NIST AI Risk Management Framework', '1.0', 'Framework for managing risks associated with AI systems', 'NIST', '2023-01-01', '{}'),
    ('550e8400-e29b-41d4-a716-446655440202', 'ISO-42001', 'ISO/IEC 42001 AI Management System', '2023', 'International standard for AI management systems', 'ISO/IEC', '2023-12-01', '{}'),
    ('550e8400-e29b-41d4-a716-446655440203', 'EU-AI-ACT', 'EU AI Act', '2024', 'European Union regulation on artificial intelligence', 'European Commission', '2024-08-01', '{}'),
    ('550e8400-e29b-41d4-a716-446655440204', 'SOC2', 'SOC 2 Trust Services Criteria', '2022', 'Service organization control criteria for security, availability, and confidentiality', 'AICPA', '2022-01-01', '{}');

-- Insert compliance controls
INSERT INTO grc_claw.compliance_controls (id, framework_id, control_key, title, description, category, guidance, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440301', '550e8400-e29b-41d4-a716-446655440201', 'NIST-AI-RMF.GOVERN.1', 'Governance Structure', 'Establish and maintain governance structure for AI risk management', 'Governance', 'Define roles and responsibilities for AI governance', '{}'),
    ('550e8400-e29b-41d4-a716-446655440302', '550e8400-e29b-41d4-a716-446655440201', 'NIST-AI-RMF.MAP.1', 'Risk Mapping', 'Identify and map AI risks to organizational objectives', 'Risk Management', 'Conduct comprehensive risk assessment', '{}'),
    ('550e8400-e29b-41d4-a716-446655440303', '550e8400-e29b-41d4-a716-446655440202', 'ISO-42001.A.5.1', 'AI Policy', 'Establish and maintain AI policy', 'Policy', 'Document AI governance policies', '{}'),
    ('550e8400-e29b-41d4-a716-446655440304', '550e8400-e29b-41d4-a716-446655440203', 'EU-AI-ACT.ART.9', 'Risk Management System', 'Establish and maintain risk management system for AI', 'Risk Management', 'Implement risk management processes', '{}'),
    ('550e8400-e29b-41d4-a716-446655440305', '550e8400-e29b-41d4-a716-446655440204', 'SOC2.CC6.1', 'Logical Access Controls', 'Implement logical access controls to protect data', 'Access Control', 'Deploy access control mechanisms', '{}');

-- Insert compliance mappings
INSERT INTO grc_claw.compliance_mappings (control_id, policy_id, assessment_id, mapping_type, coverage, notes, mapped_by)
VALUES
    ('550e8400-e29b-41d4-a716-446655440301', '550e8400-e29b-41d4-a716-446655440001', NULL, 'policy_satisfies', 'full', 'AI Ethics Policy satisfies governance requirements', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440303', '550e8400-e29b-41d4-a716-446655440001', NULL, 'policy_satisfies', 'partial', 'AI Ethics Policy partially satisfies ISO 42001 policy requirements', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440305', '550e8400-e29b-41d4-a716-446655440005', NULL, 'policy_satisfies', 'full', 'Access Control Policy satisfies SOC2 CC6.1', '550e8400-e29b-41d4-a716-446655440000');

-- Insert compliance status
INSERT INTO grc_claw.compliance_status (framework_id, control_id, target_id, target_type, status, evidence_ids, assessment_id, evaluated_at, evaluated_by, next_review_at, notes, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440201', '550e8400-e29b-41d4-a716-446655440301', 'organization', 'organization', 'compliant', NULL, NULL, '2026-09-01', '550e8400-e29b-41d4-a716-446655440000', '2026-12-01', 'Governance structure is in place', '{}'),
    ('550e8400-e29b-41d4-a716-446655440202', '550e8400-e29b-41d4-a716-446655440303', 'organization', 'organization', 'partial', NULL, NULL, '2026-09-01', '550e8400-e29b-41d4-a716-446655440000', '2026-12-01', 'AI policy needs updates', '{}'),
    ('550e8400-e29b-41d4-a716-446655440204', '550e8400-e29b-41d4-a716-446655440305', 'organization', 'organization', 'compliant', NULL, NULL, '2026-09-01', '550e8400-e29b-41d4-a716-446655440000', '2026-12-01', 'Access controls are effective', '{}');

-- Insert assessments
INSERT INTO grc_claw.assessments (id, assessment_key, title, description, assessment_type, target_id, target_type, status, methodology, score, risk_level, started_at, completed_at, next_assessment_at, lead_assessor, metadata, created_by, updated_by)
VALUES
    ('550e8400-e29b-41d4-a716-446655440401', 'ASSESS-2026-001', 'Annual AI Governance Assessment', 'Comprehensive assessment of AI governance posture', 'compliance', 'organization', 'organization', 'completed', 'NIST AI RMF', 85.50, 'medium', '2026-01-15', '2026-02-15', '2027-01-15', '550e8400-e29b-41d4-a716-446655440000', '{}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440402', 'ASSESS-2026-002', 'Model Safety Assessment', 'Assessment of model safety for production AI models', 'risk', 'model-gpt4', 'model', 'in_progress', 'NIST AI RMF', NULL, NULL, '2026-09-01', NULL, '2027-03-01', '550e8400-e29b-41d4-a716-446655440000', '{}', '550e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000');

-- Insert assessment findings
INSERT INTO grc_claw.assessment_findings (id, assessment_id, finding_key, title, description, severity, category, status, policy_id, evidence_ids, remediation, due_date, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440501', '550e8400-e29b-41d4-a716-446655440401', 'FIND-001', 'Incomplete Documentation', 'AI system documentation is incomplete for several production models', 'medium', 'documentation', 'open', '550e8400-e29b-41d4-a716-446655440001', NULL, 'Complete documentation for all production models', '2026-12-01', '{}'),
    ('550e8400-e29b-41d4-a716-446655440502', '550e8400-e29b-41d4-a716-446655440401', 'FIND-002', 'Missing Bias Testing', 'Bias testing has not been conducted for new model deployments', 'high', 'testing', 'open', '550e8400-e29b-41d4-a716-446655440004', NULL, 'Conduct bias testing for all new models', '2026-11-01', '{}');

-- Insert enforcement actions
INSERT INTO grc_claw.enforcement_actions (id, action_key, policy_id, clause_id, evidence_id, action_type, target_type, target_id, status, priority, triggered_by, triggered_at, executed_at, completed_at, result, error_message, rollback_action, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440601', 'ENFORCE-2026-001', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440101', NULL, 'block', 'model', 'model-gpt4', 'completed', 'high', '550e8400-e29b-41d4-a716-446655440000', '2026-09-15 10:00:00', '2026-09-15 10:00:05', '2026-09-15 10:00:05', '{"reason": "Policy violation: transparency requirement not met"}', NULL, '{"action": "unblock", "conditions": "Complete transparency documentation"}', '{}'),
    ('550e8400-e29b-41d4-a716-446655440602', 'ENFORCE-2026-002', '550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440103', NULL, 'flag', 'endpoint', 'api-endpoint-1', 'completed', 'medium', '550e8400-e29b-41d4-a716-446655440000', '2026-09-16 14:30:00', '2026-09-16 14:30:02', '2026-09-16 14:30:02', '{"reason": "Data minimization violation detected"}', NULL, NULL, '{}'),
    ('550e8400-e29b-41d4-a716-446655440603', 'ENFORCE-2026-003', '550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440105', NULL, 'notify', 'pipeline', 'training-pipeline-1', 'pending', 'low', '550e8400-e29b-41d4-a716-446655440000', '2026-09-17 09:00:00', NULL, NULL, NULL, NULL, NULL, '{}');

-- Insert enforcement audit log
INSERT INTO grc_claw.enforcement_audit_log (action_id, event_type, event_data, actor)
VALUES
    ('550e8400-e29b-41d4-a716-446655440601', 'created', '{"timestamp": "2026-09-15T10:00:00Z"}', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440601', 'started', '{"timestamp": "2026-09-15T10:00:05Z"}', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440601', 'completed', '{"timestamp": "2026-09-15T10:00:05Z", "result": "blocked"}', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440602', 'created', '{"timestamp": "2026-09-16T14:30:00Z"}', '550e8400-e29b-41d4-a716-446655440000'),
    ('550e8400-e29b-41d4-a716-446655440602', 'completed', '{"timestamp": "2026-09-16T14:30:02Z", "result": "flagged"}', '550e8400-e29b-41d4-a716-446655440000');

-- Insert compliance attestations
INSERT INTO grc_claw.compliance_attestations (compliance_status_id, attestation_type, attested_by, attested_at, valid_from, valid_until, evidence_id, notes, metadata)
VALUES
    ('550e8400-e29b-41d4-a716-446655440701', 'self', '550e8400-e29b-41d4-a716-446655440000', '2026-09-01', '2026-09-01', '2026-12-01', NULL, 'Self-assessment completed', '{}'),
    ('550e8400-e29b-41d4-a716-446655440702', 'internal_audit', '550e8400-e29b-41d4-a716-446655440000', '2026-09-15', '2026-09-15', '2026-12-15', NULL, 'Internal audit verification', '{}');

-- Insert evidence metrics (TimescaleDB)
INSERT INTO grc_claw.evidence_metrics (time, evidence_id, policy_id, metric_name, metric_value, unit, labels, source)
VALUES
    ('2026-09-15 10:00:00+00', '550e8400-e29b-41d4-a716-446655440801', '550e8400-e29b-41d4-a716-446655440001', 'model_drift_score', 0.15, 'ratio', '{"model": "model-gpt4"}', 'monitoring'),
    ('2026-09-15 11:00:00+00', '550e8400-e29b-41d4-a716-446655440801', '550e8400-e29b-41d4-a716-446655440001', 'model_drift_score', 0.18, 'ratio', '{"model": "model-gpt4"}', 'monitoring'),
    ('2026-09-15 12:00:00+00', '550e8400-e29b-41d4-a716-446655440801', '550e8400-e29b-41d4-a716-446655440001', 'model_drift_score', 0.22, 'ratio', '{"model": "model-gpt4"}', 'monitoring'),
    ('2026-09-16 10:00:00+00', '550e8400-e29b-41d4-a716-446655440802', '550e8400-e29b-41d4-a716-446655440002', 'data_quality_score', 0.92, 'ratio', '{"dataset": "customer-data"}', 'validation'),
    ('2026-09-16 11:00:00+00', '550e8400-e29b-41d4-a716-446655440802', '550e8400-e29b-41d4-a716-446655440002', 'data_quality_score', 0.89, 'ratio', '{"dataset": "customer-data"}', 'validation');
```

### 7.2 MongoDB Seed Data

```javascript
// seeds/mongodb/seed_data.js
// MongoDB seed data for GRC_Claw

db = db.getSiblingDB('grc_claw');

// ============================================================
// EVIDENCE SEED DATA
// ============================================================

db.evidence.insertMany([
    {
        evidence_id: "550e8400-e29b-41d4-a716-446655440801",
        policy_id: "550e8400-e29b-41d4-a716-446655440001",
        assessment_id: null,
        source: {
            type: "scan",
            system: "model-monitoring",
            collection_method: "automated"
        },
        evidence_type: "metric",
        content: {
            format: "json",
            data: { drift_score: 0.15, threshold: 0.20, model: "model-gpt4" },
            hash: "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
        },
        context: {
            environment: "prod",
            region: "us-east-1",
            timestamp: new Date("2026-09-15T10:00:00Z"),
            metadata: { model_version: "1.2.3" }
        },
        validation: {
            status: "validated",
            validated_by: "550e8400-e29b-41d4-a716-446655440000",
            validated_at: new Date("2026-09-15T10:05:00Z"),
            confidence_score: 0.95
        },
        retention_class: "standard",
        legal_hold: false,
        lifecycle_stage: "active",
        stage_changed_at: new Date("2026-09-15T10:00:00Z"),
        compression_enabled: false,
        original_size_bytes: 0,
        compressed_size_bytes: 0,
        created_at: new Date("2026-09-15T10:00:00Z"),
        expires_at: new Date("2027-09-15T10:00:00Z")
    },
    {
        evidence_id: "550e8400-e29b-41d4-a716-446655440802",
        policy_id: "550e8400-e29b-41d4-a716-446655440002",
        assessment_id: null,
        source: {
            type: "audit",
            system: "data-quality-checker",
            collection_method: "automated"
        },
        evidence_type: "report",
        content: {
            format: "json",
            data: { quality_score: 0.92, issues_found: 3, dataset: "customer-data" },
            hash: "b2c3d4e5f67890123456789012345678901abcdef2345678901abcdef234567"
        },
        context: {
            environment: "prod",
            region: "us-east-1",
            timestamp: new Date("2026-09-16T10:00:00Z"),
            metadata: { dataset_version: "2.1.0" }
        },
        validation: {
            status: "validated",
            validated_by: "550e8400-e29b-41d4-a716-446655440000",
            validated_at: new Date("2026-09-16T10:10:00Z"),
            confidence_score: 0.88
        },
        retention_class: "standard",
        legal_hold: false,
        lifecycle_stage: "active",
        stage_changed_at: new Date("2026-09-16T10:00:00Z"),
        compression_enabled: false,
        original_size_bytes: 0,
        compressed_size_bytes: 0,
        created_at: new Date("2026-09-16T10:00:00Z"),
        expires_at: new Date("2027-09-16T10:00:00Z")
    },
    {
        evidence_id: "550e8400-e29b-41d4-a716-446655440803",
        policy_id: "550e8400-e29b-41d4-a716-446655440003",
        assessment_id: "550e8400-e29b-41d4-a716-446655440402",
        source: {
            type: "manual",
            system: "assessment-tool",
            collection_method: "upload"
        },
        evidence_type: "attestation",
        content: {
            format: "text",
            data: "Model safety assessment completed. All critical tests passed.",
            hash: "c3d4e5f678901234567890123456789012abcdef3456789012abcdef345678"
        },
        context: {
            environment: "prod",
            region: "us-east-1",
            timestamp: new Date("2026-09-17T14:00:00Z"),
            metadata: { assessor: "550e8400-e29b-41d4-a716-446655440000" }
        },
        validation: {
            status: "pending",
            validated_by: null,
            validated_at: null,
            confidence_score: 0.0
        },
        retention_class: "extended",
        legal_hold: false,
        lifecycle_stage: "active",
        stage_changed_at: new Date("2026-09-17T14:00:00Z"),
        compression_enabled: false,
        original_size_bytes: 0,
        compressed_size_bytes: 0,
        created_at: new Date("2026-09-17T14:00:00Z"),
        expires_at: new Date("2033-09-17T14:00:00Z")
    }
]);

// ============================================================
// POLICY VERSIONS SEED DATA
// ============================================================

db.policy_versions.insertMany([
    {
        policy_id: "550e8400-e29b-41d4-a716-446655440001",
        version: 1,
        full_text: "# AI Ethics Policy\n\n## 1. Transparency Requirement\nAll AI systems must provide clear explanations for their decisions and actions.\n\n## 2. Human Oversight\nCritical AI decisions must include human oversight and approval mechanisms.",
        change_summary: "Initial version of AI Ethics Policy",
        diff_from_previous: null,
        approved_by: "550e8400-e29b-41d4-a716-446655440000",
        approved_at: new Date("2026-01-01T00:00:00Z"),
        created_at: new Date("2026-01-01T00:00:00Z"),
        metadata: {}
    },
    {
        policy_id: "550e8400-e29b-41d4-a716-446655440002",
        version: 1,
        full_text: "# Data Privacy Policy\n\n## 1. Data Minimization\nOnly collect and process personal data that is strictly necessary.\n\n## 2. Consent Management\nObtain explicit consent from data subjects before processing.",
        change_summary: "Initial version of Data Privacy Policy",
        diff_from_previous: null,
        approved_by: "550e8400-e29b-41d4-a716-446655440000",
        approved_at: new Date("2026-01-01T00:00:00Z"),
        created_at: new Date("2026-01-01T00:00:00Z"),
        metadata: {}
    }
]);

// ============================================================
// ASSESSMENT REPORTS SEED DATA
// ============================================================

db.assessment_reports.insertMany([
    {
        assessment_id: "550e8400-e29b-41d4-a716-446655440401",
        report_format: "pdf",
        full_report: "base64-encoded-pdf-content",
        executive_summary: "The organization demonstrates strong AI governance posture with an overall score of 85.50/100. Key strengths include established governance structure and comprehensive policy framework. Areas for improvement include documentation completeness and bias testing coverage.",
        detailed_findings: [
            {
                finding_id: "FIND-001",
                title: "Incomplete Documentation",
                severity: "medium",
                description: "AI system documentation is incomplete for several production models"
            },
            {
                finding_id: "FIND-002",
                title: "Missing Bias Testing",
                severity: "high",
                description: "Bias testing has not been conducted for new model deployments"
            }
        ],
        recommendations: [
            "Complete documentation for all production models by Q4 2026",
            "Implement mandatory bias testing for all new model deployments",
            "Establish regular compliance review cadence"
        ],
        appendices: [
            {
                title: "Assessment Methodology",
                content: "NIST AI Risk Management Framework assessment methodology"
            }
        ],
        generated_at: new Date("2026-02-15T00:00:00Z"),
        generated_by: "550e8400-e29b-41d4-a716-446655440000",
        metadata: {}
    }
]);

print("MongoDB seed data inserted successfully");
```

### 7.3 Neo4j Seed Data

```cypher
// seeds/neo4j/seed_data.cypher
// Neo4j seed data for GRC_Claw

// ============================================================
// POLICY NODES
// ============================================================

CREATE (p1:Policy {
    id: '550e8400-e29b-41d4-a716-446655440001',
    policy_key: 'AI-ETHICS-001',
    title: 'AI Ethics Policy',
    category: 'ethics',
    status: 'active',
    version: 1,
    effective_date: datetime('2026-01-01'),
    expiry_date: datetime('2027-01-01')
});

CREATE (p2:Policy {
    id: '550e8400-e29b-41d4-a716-446655440002',
    policy_key: 'DATA-PRIVACY-001',
    title: 'Data Privacy Policy',
    category: 'privacy',
    status: 'active',
    version: 1,
    effective_date: datetime('2026-01-01'),
    expiry_date: datetime('2027-01-01')
});

CREATE (p3:Policy {
    id: '550e8400-e29b-41d4-a716-446655440003',
    policy_key: 'MODEL-SAFETY-001',
    title: 'Model Safety Policy',
    category: 'safety',
    status: 'active',
    version: 1,
    effective_date: datetime('2026-01-01'),
    expiry_date: datetime('2027-01-01')
});

// ============================================================
// TARGET NODES
// ============================================================

CREATE (t1:Target {
    id: '550e8400-e29b-41d4-a716-446655440901',
    target_type: 'model',
    target_id: 'model-gpt4'
});

CREATE (t2:Target {
    id: '550e8400-e29b-41d4-a716-446655440902',
    target_type: 'endpoint',
    target_id: 'api-endpoint-1'
});

CREATE (t3:Target {
    id: '550e8400-e29b-41d4-a716-446655440903',
    target_type: 'pipeline',
    target_id: 'training-pipeline-1'
});

// ============================================================
// EVIDENCE NODES
// ============================================================

CREATE (e1:Evidence {
    id: '550e8400-e29b-41d4-a716-446655440801',
    evidence_id: '550e8400-e29b-41d4-a716-446655440801',
    evidence_type: 'metric',
    validation_status: 'validated'
});

CREATE (e2:Evidence {
    id: '550e8400-e29b-41d4-a716-446655440802',
    evidence_id: '550e8400-e29b-41d4-a716-446655440802',
    evidence_type: 'report',
    validation_status: 'validated'
});

// ============================================================
// ENFORCEMENT ACTION NODES
// ============================================================

CREATE (ea1:EnforcementAction {
    id: '550e8400-e29b-41d4-a716-446655440601',
    action_key: 'ENFORCE-2026-001',
    action_type: 'block',
    status: 'completed',
    priority: 'high',
    triggered_at: datetime('2026-09-15T10:00:00'),
    completed_at: datetime('2026-09-15T10:00:05')
});

CREATE (ea2:EnforcementAction {
    id: '550e8400-e29b-41d4-a716-446655440602',
    action_key: 'ENFORCE-2026-002',
    action_type: 'flag',
    status: 'completed',
    priority: 'medium',
    triggered_at: datetime('2026-09-16T14:30:00'),
    completed_at: datetime('2026-09-16T14:30:02')
});

// ============================================================
// RELATIONSHIPS
// ============================================================

MATCH (ea1:EnforcementAction {id: '550e8400-e29b-41d4-a716-446655440601'})
MATCH (p1:Policy {id: '550e8400-e29b-41d4-a716-446655440001'})
CREATE (ea1)-[:ENFORCES]->(p1);

MATCH (ea1:EnforcementAction {id: '550e8400-e29b-41d4-a716-446655440601'})
MATCH (t1:Target {id: '550e8400-e29b-41d4-a716-446655440901'})
CREATE (ea1)-[:TARGETS]->(t1);

MATCH (ea2:EnforcementAction {id: '550e8400-e29b-41d4-a716-446655440602'})
MATCH (p2:Policy {id: '550e8400-e29b-41d4-a716-446655440002'})
CREATE (ea2)-[:ENFORCES]->(p2);

MATCH (ea2:EnforcementAction {id: '550e8400-e29b-41d4-a716-446655440602'})
MATCH (t2:Target {id: '550e8400-e29b-41d4-a716-446655440902'})
CREATE (ea2)-[:TARGETS]->(t2);

// Policy relationships
MATCH (p1:Policy {id: '550e8400-e29b-41d4-a716-446655440001'})
MATCH (p3:Policy {id: '550e8400-e29b-41d4-a716-446655440003'})
CREATE (p1)-[:RELATED_TO]->(p3);

// ============================================================
// COMPLIANCE GRAPH
// ============================================================

CREATE (cf1:ComplianceFramework {
    id: '550e8400-e29b-41d4-a716-446655440201',
    framework_key: 'NIST-AI-RMF',
    name: 'NIST AI Risk Management Framework',
    version: '1.0'
});

CREATE (cc1:ComplianceControl {
    id: '550e8400-e29b-41d4-a716-446655440301',
    control_key: 'NIST-AI-RMF.GOVERN.1',
    title: 'Governance Structure',
    category: 'Governance'
});

CREATE (cs1:ComplianceStatus {
    id: '550e8400-e29b-41d4-a716-446655441001',
    status: 'compliant',
    evaluated_at: datetime('2026-09-01')
});

MATCH (cf1:ComplianceFramework {id: '550e8400-e29b-41d4-a716-446655440201'})
MATCH (cc1:ComplianceControl {id: '550e8400-e29b-41d4-a716-446655440301'})
CREATE (cf1)-[:CONTAINS]->(cc1);

MATCH (cc1:ComplianceControl {id: '550e8400-e29b-41d4-a716-446655440301'})
MATCH (p1:Policy {id: '550e8400-e29b-41d4-a716-446655440001'})
CREATE (cc1)-[:SATISFIED_BY {coverage: 'full'}]->(p1);

MATCH (cc1:ComplianceControl {id: '550e8400-e29b-41d4-a716-446655440301'})
MATCH (cs1:ComplianceStatus {id: '550e8400-e29b-41d4-a716-446655441001'})
CREATE (cc1)-[:HAS_STATUS]->(cs1);

MATCH (p1:Policy {id: '550e8400-e29b-41d4-a716-446655440001'})
MATCH (cc1:ComplianceControl {id: '550e8400-e29b-41d4-a716-446655440301'})
CREATE (p1)-[:MAPS_TO]->(cc1);

// ============================================================
// ASSESSMENT NODES
// ============================================================

CREATE (a1:Assessment {
    id: '550e8400-e29b-41d4-a716-446655440401',
    assessment_key: 'ASSESS-2026-001',
    assessment_type: 'compliance',
    status: 'completed',
    score: 85.50
});

MATCH (a1:Assessment {id: '550e8400-e29b-41d4-a716-446655440401'})
MATCH (t1:Target {id: '550e8400-e29b-41d4-a716-446655440901'})
CREATE (a1)-[:EVALUATES]->(t1);

MATCH (a1:Assessment {id: '550e8400-e29b-41d4-a716-446655440401'})
MATCH (e1:Evidence {id: '550e8400-e29b-41d4-a716-446655440801'})
CREATE (a1)-[:PRODUCES]->(e1);

print("Neo4j seed data inserted successfully");
```

---

## 8. Backup and Restore Procedures

### 8.1 Backup Strategy Overview

| Data Model | Backup Type | Frequency | Retention | Storage |
|-----------|------------|-----------|-----------|---------|
| PostgreSQL (all tables) | Full | Daily | 30 days | S3/GCS (encrypted) |
| PostgreSQL | WAL archiving | Continuous | 7 days | S3/GCS (encrypted) |
| MongoDB | Full (mongodump) | Daily | 30 days | S3/GCS (encrypted) |
| MongoDB | Oplog | Continuous | 48 hours | S3/GCS (encrypted) |
| Neo4j | Full (neo4j-admin) | Daily | 30 days | S3/GCS (encrypted) |
| TimescaleDB | Full | Daily | 30 days | S3/GCS (encrypted) |
| TimescaleDB | Continuous archiving | Real-time | 7 days | S3/GCS (encrypted) |

### 8.2 PostgreSQL Backup (pgBackRest)

```bash
#!/bin/bash
# scripts/backup/postgresql_backup.sh
# PostgreSQL backup using pgBackRest

set -euo pipefail

# Configuration
STANZA="grc_claw"
BACKUP_DIR="/backup/postgresql"
LOG_FILE="/var/log/grc-claw/backup-postgresql.log"
DATE=$(date +%F)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Full backup
log "Starting full backup for stanza: $STANZA"
pgbackrest --stanza="$STANZA" --type=full backup 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Full backup completed successfully"
else
    log "ERROR: Full backup failed"
    exit 1
fi

# Verify backup integrity
log "Verifying backup integrity"
pgbackrest --stanza="$STANZA" verify 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Backup verification completed successfully"
else
    log "ERROR: Backup verification failed"
    exit 1
fi

# Upload to S3 (encrypted)
log "Uploading backup to S3"
aws s3 sync "$BACKUP_DIR" "s3://grc-claw-backups/postgresql/$DATE/" \
    --storage-class STANDARD_IA \
    --sse AES256 2>&1 | tee -a "$LOG_FILE"

log "PostgreSQL backup completed successfully"
```

### 8.3 PostgreSQL Restore

```bash
#!/bin/bash
# scripts/restore/postgresql_restore.sh
# PostgreSQL restore using pgBackRest

set -euo pipefail

# Configuration
STANZA="grc_claw"
RESTORE_DIR="/var/lib/postgresql/restore"
LOG_FILE="/var/log/grc-claw/restore-postgresql.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Restore to point-in-time
TARGET_TIME="${1:-latest}"

log "Starting restore for stanza: $STANZA to target: $TARGET_TIME"

# Stop PostgreSQL
log "Stopping PostgreSQL"
systemctl stop postgresql

# Restore from backup
if [ "$TARGET_TIME" = "latest" ]; then
    pgbackrest --stanza="$STANZA" --type=time --target="latest" \
        --target-action=promote restore 2>&1 | tee -a "$LOG_FILE"
else
    pgbackrest --stanza="$STANZA" --type=time --target="$TARGET_TIME" \
        --target-action=promote restore 2>&1 | tee -a "$LOG_FILE"
fi

if [ $? -eq 0 ]; then
    log "Restore completed successfully"
else
    log "ERROR: Restore failed"
    exit 1
fi

# Start PostgreSQL
log "Starting PostgreSQL"
systemctl start postgresql

# Verify data integrity
log "Verifying data integrity"
psql -c "SELECT count(*) FROM grc_claw.policies;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.enforcement_actions;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.assessments;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.compliance_status;" 2>&1 | tee -a "$LOG_FILE"

log "PostgreSQL restore completed successfully"
```

### 8.4 MongoDB Backup

```bash
#!/bin/bash
# scripts/backup/mongodb_backup.sh
# MongoDB backup using mongodump

set -euo pipefail

# Configuration
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
BACKUP_DIR="/backup/mongodb"
LOG_FILE="/var/log/grc-claw/backup-mongodb.log"
DATE=$(date +%F)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Full backup
log "Starting MongoDB full backup"
mongodump --uri="$MONGO_URI" \
    --archive="$BACKUP_DIR/$DATE/mongodb-$DATE.archive" \
    --gzip 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "MongoDB full backup completed successfully"
else
    log "ERROR: MongoDB full backup failed"
    exit 1
fi

# Upload to S3 (encrypted)
log "Uploading backup to S3"
aws s3 cp "$BACKUP_DIR/$DATE/mongodb-$DATE.archive" \
    "s3://grc-claw-backups/mongodb/$DATE/" \
    --storage-class STANDARD_IA \
    --sse AES256 2>&1 | tee -a "$LOG_FILE"

# Cleanup old backups (keep 30 days)
log "Cleaning up old backups"
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

log "MongoDB backup completed successfully"
```

### 8.5 MongoDB Restore

```bash
#!/bin/bash
# scripts/restore/mongodb_restore.sh
# MongoDB restore using mongorestore

set -euo pipefail

# Configuration
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
BACKUP_FILE="${1:-}"
LOG_FILE="/var/log/grc-claw/restore-mongodb.log"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting MongoDB restore from: $BACKUP_FILE"

# Restore from backup
mongorestore --uri="$MONGO_URI" \
    --archive="$BACKUP_FILE" \
    --gzip \
    --drop 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "MongoDB restore completed successfully"
else
    log "ERROR: MongoDB restore failed"
    exit 1
fi

# Verify data integrity
log "Verifying data integrity"
mongosh --uri="$MONGO_URI" --eval "db.evidence.countDocuments()" 2>&1 | tee -a "$LOG_FILE"
mongosh --uri="$MONGO_URI" --eval "db.policy_versions.countDocuments()" 2>&1 | tee -a "$LOG_FILE"
mongosh --uri="$MONGO_URI" --eval "db.assessment_reports.countDocuments()" 2>&1 | tee -a "$LOG_FILE"

log "MongoDB restore completed successfully"
```

### 8.6 Neo4j Backup

```bash
#!/bin/bash
# scripts/backup/neo4j_backup.sh
# Neo4j backup using neo4j-admin

set -euo pipefail

# Configuration
NEO4J_HOME="${NEO4J_HOME:-/var/lib/neo4j}"
BACKUP_DIR="/backup/neo4j"
LOG_FILE="/var/log/grc-claw/backup-neo4j.log"
DATE=$(date +%F)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Full backup
log "Starting Neo4j full backup"
neo4j-admin database backup \
    --to-path="$BACKUP_DIR/$DATE" \
    grc_claw 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Neo4j full backup completed successfully"
else
    log "ERROR: Neo4j full backup failed"
    exit 1
fi

# Upload to S3 (encrypted)
log "Uploading backup to S3"
aws s3 sync "$BACKUP_DIR/$DATE" \
    "s3://grc-claw-backups/neo4j/$DATE/" \
    --storage-class STANDARD_IA \
    --sse AES256 2>&1 | tee -a "$LOG_FILE"

# Cleanup old backups (keep 30 days)
log "Cleaning up old backups"
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

log "Neo4j backup completed successfully"
```

### 8.7 Neo4j Restore

```bash
#!/bin/bash
# scripts/restore/neo4j_restore.sh
# Neo4j restore using neo4j-admin

set -euo pipefail

# Configuration
NEO4J_HOME="${NEO4J_HOME:-/var/lib/neo4j}"
BACKUP_PATH="${1:-}"
LOG_FILE="/var/log/grc-claw/restore-neo4j.log"

if [ -z "$BACKUP_PATH" ]; then
    echo "Usage: $0 <backup-path>"
    exit 1
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Neo4j restore from: $BACKUP_PATH"

# Stop Neo4j
log "Stopping Neo4j"
systemctl stop neo4j

# Restore from backup
neo4j-admin database restore \
    --from-path="$BACKUP_PATH" \
    grc_claw 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "Neo4j restore completed successfully"
else
    log "ERROR: Neo4j restore failed"
    exit 1
fi

# Start Neo4j
log "Starting Neo4j"
systemctl start neo4j

# Verify data integrity
log "Verifying data integrity"
cypher-shell -u neo4j -p password "MATCH (p:Policy) RETURN count(p) AS policy_count;" 2>&1 | tee -a "$LOG_FILE"
cypher-shell -u neo4j -p password "MATCH (e:EnforcementAction) RETURN count(e) AS enforcement_count;" 2>&1 | tee -a "$LOG_FILE"

log "Neo4j restore completed successfully"
```

### 8.8 TimescaleDB Backup

```bash
#!/bin/bash
# scripts/backup/timescaledb_backup.sh
# TimescaleDB backup (inherits pgBackRest)

set -euo pipefail

# Configuration
STANZA="grc_claw_ts"
BACKUP_DIR="/backup/timescaledb"
LOG_FILE="/var/log/grc-claw/backup-timescaledb.log"
DATE=$(date +%F)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Full backup
log "Starting TimescaleDB full backup"
pgbackrest --stanza="$STANZA" --type=full backup 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "TimescaleDB full backup completed successfully"
else
    log "ERROR: TimescaleDB full backup failed"
    exit 1
fi

# Continuous archiving via WAL-G
log "Pushing WAL archives"
wal-g wal-push /var/lib/postgresql/wal/ 2>&1 | tee -a "$LOG_FILE"

# Upload to S3 (encrypted)
log "Uploading backup to S3"
aws s3 sync "$BACKUP_DIR" "s3://grc-claw-backups/timescaledb/$DATE/" \
    --storage-class STANDARD_IA \
    --sse AES256 2>&1 | tee -a "$LOG_FILE"

log "TimescaleDB backup completed successfully"
```

### 8.9 Backup Verification

```bash
#!/bin/bash
# scripts/backup/verify_backups.sh
# Verify backup integrity

set -euo pipefail

LOG_FILE="/var/log/grc-claw/verify-backups.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup verification"

# Verify PostgreSQL backup
log "Verifying PostgreSQL backup"
pgbackrest --stanza=grc_claw verify 2>&1 | tee -a "$LOG_FILE"

# Verify MongoDB backup
log "Verifying MongoDB backup"
LATEST_MONGO_BACKUP=$(find /backup/mongodb -name "*.archive" -type f | sort | tail -1)
if [ -n "$LATEST_MONGO_BACKUP" ]; then
    mongorestore --archive="$LATEST_MONGO_BACKUP" --gzip --dryRun 2>&1 | tee -a "$LOG_FILE"
fi

# Verify Neo4j backup
log "Verifying Neo4j backup"
LATEST_NEO4J_BACKUP=$(find /backup/neo4j -type d -name "grc_claw*" | sort | tail -1)
if [ -n "$LATEST_NEO4J_BACKUP" ]; then
    neo4j-admin database check --from-path="$LATEST_NEO4J_BACKUP" grc_claw 2>&1 | tee -a "$LOG_FILE"
fi

# Verify encryption
log "Verifying backup encryption"
aws s3 ls s3://grc-claw-backups/ --recursive --human-readable --summarize 2>&1 | tee -a "$LOG_FILE"

log "Backup verification completed"
```

### 8.10 Recovery Procedures

#### Scenario 1: Single Table Corruption

```sql
-- 1. Identify corruption point
-- 2. Restore table from latest good backup
-- 3. Replay WAL to point just before corruption
-- 4. Export affected table
-- 5. Restore to production

-- Example: Restore policies table
BEGIN;
-- Export current (corrupted) data for comparison
CREATE TABLE grc_claw_archive.policies_corrupted AS SELECT * FROM grc_claw.policies;

-- Restore from backup (via pgBackRest to staging)
-- Then import only the policies table
-- INSERT INTO grc_claw.policies SELECT * FROM staging.policies;

-- Verify
SELECT count(*) FROM grc_claw.policies;
COMMIT;
```

#### Scenario 2: Complete Database Loss

```bash
#!/bin/bash
# scripts/restore/complete_recovery.sh
# Complete database recovery procedure

set -euo pipefail

LOG_FILE="/var/log/grc-claw/complete-recovery.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting complete database recovery"

# 1. Provision new database instance
log "Provisioning new database instance"
# (Infrastructure provisioning steps here)

# 2. Restore PostgreSQL from latest full backup
log "Restoring PostgreSQL from latest full backup"
pgbackrest --stanza=grc_claw --type=full restore 2>&1 | tee -a "$LOG_FILE"

# 3. Replay WAL archives to current time
log "Replaying WAL archives"
pgbackrest --stanza=grc_claw --type=time --target="latest" \
    --target-action=promote restore 2>&1 | tee -a "$LOG_FILE"

# 4. Verify data integrity
log "Verifying PostgreSQL data integrity"
psql -c "SELECT count(*) FROM grc_claw.policies;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.enforcement_actions;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.assessments;" 2>&1 | tee -a "$LOG_FILE"
psql -c "SELECT count(*) FROM grc_claw.compliance_status;" 2>&1 | tee -a "$LOG_FILE"

# 5. Restore MongoDB
log "Restoring MongoDB"
LATEST_MONGO_BACKUP=$(aws s3 ls s3://grc-claw-backups/mongodb/ --recursive | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://grc-claw-backups/mongodb/$LATEST_MONGO_BACKUP" /tmp/mongodb-backup.archive
mongorestore --archive=/tmp/mongodb-backup.archive --gzip --drop 2>&1 | tee -a "$LOG_FILE"

# 6. Restore Neo4j
log "Restoring Neo4j"
LATEST_NEO4J_BACKUP=$(aws s3 ls s3://grc-claw-backups/neo4j/ --recursive | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://grc-claw-backups/neo4j/$LATEST_NEO4J_BACKUP" /tmp/neo4j-backup
neo4j-admin database restore --from-path=/tmp/neo4j-backup grc_claw 2>&1 | tee -a "$LOG_FILE"

# 7. Rebuild secondary backends from primary
log "Rebuilding secondary backends"
python scripts/rebuild_mongodb.py 2>&1 | tee -a "$LOG_FILE"
python scripts/rebuild_neo4j.py 2>&1 | tee -a "$LOG_FILE"

# 8. Verify consistency
log "Verifying cross-backend consistency"
python scripts/reconcile_check.py --verify 2>&1 | tee -a "$LOG_FILE"

log "Complete database recovery finished"
```

#### Scenario 3: Cross-Backend Inconsistency

```bash
#!/bin/bash
# scripts/restore/reconcile_backends.sh
# Reconcile cross-backend inconsistencies

set -euo pipefail

LOG_FILE="/var/log/grc-claw/reconcile-backends.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting cross-backend reconciliation"

# 1. Identify drift via reconciliation job
log "Identifying drift"
python scripts/reconcile_check.py --report 2>&1 | tee -a "$LOG_FILE"

# 2. Rebuild affected secondary backends
log "Rebuilding Neo4j graph"
python scripts/rebuild_neo4j.py --framework=compliance 2>&1 | tee -a "$LOG_FILE"

log "Rebuilding MongoDB collections"
python scripts/rebuild_mongodb.py --collection=policy_versions 2>&1 | tee -a "$LOG_FILE"

# 3. Verify consistency
log "Verifying consistency"
python scripts/reconcile_check.py --verify 2>&1 | tee -a "$LOG_FILE"

log "Cross-backend reconciliation completed"
```

### 8.11 Recovery Objectives

| Metric | Target | Measurement |
|--------|--------|-------------|
| **RPO (Recovery Point Objective)** | ≤ 5 minutes | Maximum data loss acceptable |
| **RTO (Recovery Time Objective)** | ≤ 4 hours | Maximum downtime acceptable |
| **RTO (critical tables)** | ≤ 1 hour | Policies, active enforcement actions |

### 8.12 Backup Verification Schedule

| Check | Frequency | Method |
|-------|-----------|--------|
| Backup completion | Daily | Automated alert on backup job failure |
| Backup integrity | Weekly | `pgbackrest verify`, `mongodump --test` |
| Restore test | Monthly | Full restore to staging environment |
| Recovery drill | Quarterly | End-to-end recovery simulation |
| Encryption verification | Weekly | Verify all backups are encrypted |

### 8.13 Disaster Recovery

| Aspect | Implementation |
|--------|---------------|
| **DR region** | Secondary cloud region (cross-region replication) |
| **Replication lag** | < 30 seconds (PostgreSQL streaming replication) |
| **Failover** | Automated via orchestrator (Patroni for PostgreSQL) |
| **DR testing** | Quarterly failover drill |
| **DR documentation** | Runbook maintained in `docs/runbooks/disaster-recovery.md` |

---

## Appendix A: Environment Variables

```bash
# Database connection strings
export DATABASE_URL="postgresql://grc_app:password@localhost:5432/grc_claw"
export MONGODB_URI="mongodb://localhost:27017/grc_claw"
export NEO4J_URI="bolt://localhost:7687"
export TIMESCALEDB_URL="postgresql://grc_app:password@localhost:5432/grc_claw"

# Backup configuration
export BACKUP_S3_BUCKET="grc-claw-backups"
export BACKUP_REGION="us-east-1"
export BACKUP_ENCRYPTION_KEY="alias/grc-claw-backup"

# Recovery configuration
export RECOVERY_TARGET_TIME="latest"
export RECOVERY_STAGING_DIR="/staging/restore"
```

## Appendix B: Quick Reference

### Common PostgreSQL Commands

```sql
-- List all tables
\dt grc_claw.*

-- Show table size
SELECT pg_size_pretty(pg_total_relation_size('grc_claw.policies'));

-- Show index usage
SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'grc_claw';

-- Show slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

### Common MongoDB Commands

```javascript
// List collections
show collections

// Count documents
db.evidence.countDocuments()

// Find by policy
db.evidence.find({ policy_id: "550e8400-e29b-41d4-a716-446655440001" })

// Aggregation pipeline
db.evidence.aggregate([
    { $group: { _id: "$evidence_type", count: { $sum: 1 } } }
])
```

### Common Neo4j Commands

```cypher
// Count nodes by label
MATCH (p:Policy) RETURN count(p);

// Find all relationships
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 100;

// Impact analysis
MATCH (e:EnforcementAction)-[:TARGETS]->(t:Target {target_id: 'model-gpt4'})
RETURN e, t;
```

---

*End of Database Implementation Guide*</longcat_think>
