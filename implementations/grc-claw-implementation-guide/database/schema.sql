-- GRC_Claw Database Schema (PostgreSQL)
-- Version: 1.0.0
-- Description: Complete schema for the 5 core abstractions + supporting entities

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════════════════════════
-- CORE TABLES
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─── Policies ────────────────────────────────────────────────────────────────
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    owner VARCHAR(255) NOT NULL,
    content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'active', 'deprecated', 'archived')),
    category VARCHAR(100) DEFAULT 'custom',
    policy_language VARCHAR(50) DEFAULT 'cedar',
    scope JSONB DEFAULT '{}',
    framework_mappings JSONB DEFAULT '[]',
    default_action VARCHAR(50) DEFAULT 'deny',
    on_timeout VARCHAR(50) DEFAULT 'deny',
    enforcement_strategy VARCHAR(50) DEFAULT 'deny_overrides',
    effective_date TIMESTAMPTZ,
    expiration_date TIMESTAMPTZ,
    review_cycle VARCHAR(50) DEFAULT 'quarterly',
    approvers JSONB DEFAULT '[]',
    parent_policy_id UUID REFERENCES policies(id),
    change_description TEXT,
    tags JSONB DEFAULT '[]',
    labels JSONB DEFAULT '{}',
    compiled_rules JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    UNIQUE(name, version)
);

CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_category ON policies(category);
CREATE INDEX idx_policies_owner ON policies(owner);

-- ─── Policy Rules ────────────────────────────────────────────────────────────
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    condition JSONB NOT NULL,
    effect VARCHAR(50) NOT NULL CHECK (effect IN ('allow', 'deny', 'warn', 'require_approval', 'transform', 'escalate', 'throttle', 'log')),
    priority INTEGER DEFAULT 0,
    approvers JSONB DEFAULT '[]',
    limit_expression VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_policy_rules_policy ON policy_rules(policy_id);
CREATE INDEX idx_policy_rules_priority ON policy_rules(priority DESC);

-- ─── Evidence ────────────────────────────────────────────────────────────────
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id VARCHAR(255) UNIQUE NOT NULL,
    schema_version VARCHAR(50) NOT NULL DEFAULT 'grcclaw/evidence/v1',
    type VARCHAR(100) NOT NULL CHECK (type IN ('policy_evaluation', 'assessment_result', 'incident_record', 'audit_event', 'compliance_mapping', 'risk_assessment')),
    subject JSONB NOT NULL,
    policy_id UUID REFERENCES policies(id),
    policy_version VARCHAR(50),
    rule_id VARCHAR(255),
    decision JSONB NOT NULL,
    context JSONB DEFAULT '{}',
    compliance_tags JSONB DEFAULT '[]',
    proof JSONB NOT NULL,
    title VARCHAR(500),
    description TEXT,
    verification_level VARCHAR(10) DEFAULT 'L0' CHECK (verification_level IN ('L0', 'L1', 'L2', 'L3', 'L4')),
    verification_details JSONB DEFAULT '{}',
    chain_of_custody JSONB DEFAULT '[]',
    oscal_version VARCHAR(20) DEFAULT '1.1',
    retention_class VARCHAR(100) DEFAULT 'security_log',
    retention_period VARCHAR(50) DEFAULT '7years',
    expires_at TIMESTAMPTZ,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evidence_type ON evidence(type);
CREATE INDEX idx_evidence_timestamp ON evidence(timestamp);
CREATE INDEX idx_evidence_compliance_tags ON evidence USING GIN(compliance_tags);
CREATE INDEX idx_evidence_policy ON evidence(policy_id);
CREATE INDEX idx_evidence_verification ON evidence(verification_level);

-- ─── Assessments ─────────────────────────────────────────────────────────────
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) UNIQUE NOT NULL,
    system_id VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(100) NOT NULL CHECK (assessment_type IN ('fairness', 'bias', 'robustness', 'explainability', 'security', 'llm_evaluation', 'red_team')),
    criteria JSONB NOT NULL,
    results JSONB NOT NULL,
    overall_score DECIMAL(5,4),
    overall_result VARCHAR(50) DEFAULT 'not_assessed',
    assessor VARCHAR(255),
    assessor_type VARCHAR(50) DEFAULT 'automated',
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'failed', 'expired')),
    framework VARCHAR(100),
    control_ids JSONB DEFAULT '[]',
    methodology TEXT,
    risks_identified INTEGER DEFAULT 0,
    risks_mitigated INTEGER DEFAULT 0,
    risks_accepted INTEGER DEFAULT 0,
    residual_risk_score DECIMAL(5,4),
    previous_assessment_id VARCHAR(255),
    change_summary TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    next_assessment_date TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessments_system ON assessments(system_id);
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_assessments_framework ON assessments(framework);

-- ─── Compliance Mappings ────────────────────────────────────────────────────
CREATE TABLE compliance_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mapping_id VARCHAR(255) UNIQUE NOT NULL,
    control_id VARCHAR(255) NOT NULL,
    control_name VARCHAR(255) NOT NULL,
    description TEXT,
    framework_mappings JSONB NOT NULL,
    evidence_requirements JSONB DEFAULT '[]',
    assessment_criteria JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_compliance_mappings_control ON compliance_mappings(control_id);

-- ─── Compliance Posture ─────────────────────────────────────────────────────
CREATE TABLE compliance_postures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id VARCHAR(100) NOT NULL,
    scope_type VARCHAR(50) DEFAULT 'organization',
    scope_id VARCHAR(255),
    scope_name VARCHAR(255),
    framework VARCHAR(100) NOT NULL,
    framework_version VARCHAR(50),
    framework_name VARCHAR(255),
    overall_status VARCHAR(50) DEFAULT 'not_assessed',
    compliance_score DECIMAL(5,4) DEFAULT 0.0,
    trend VARCHAR(20) DEFAULT 'unknown',
    control_mappings JSONB DEFAULT '[]',
    total_controls INTEGER DEFAULT 0,
    compliant_controls INTEGER DEFAULT 0,
    partial_controls INTEGER DEFAULT 0,
    non_compliant_controls INTEGER DEFAULT 0,
    not_applicable_controls INTEGER DEFAULT 0,
    not_assessed_controls INTEGER DEFAULT 0,
    coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    total_evidence_items INTEGER DEFAULT 0,
    evidence_by_type JSONB DEFAULT '{}',
    evidence_by_verification_level JSONB DEFAULT '{}',
    oldest_evidence TIMESTAMPTZ,
    newest_evidence TIMESTAMPTZ,
    last_report_generated TIMESTAMPTZ,
    report_ids JSONB DEFAULT '[]',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    UNIQUE(organization_id, framework)
);

CREATE INDEX idx_compliance_postures_org ON compliance_postures(organization_id);
CREATE INDEX idx_compliance_postures_framework ON compliance_postures(framework);

-- ─── Enforcement Decisions ──────────────────────────────────────────────────
CREATE TABLE enforcement_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id VARCHAR(255) UNIQUE NOT NULL,
    decision VARCHAR(50) NOT NULL CHECK (decision IN ('allow', 'deny', 'warn', 'require_approval', 'transform', 'escalate', 'throttle', 'log')),
    agent_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    tool_name VARCHAR(255),
    resource VARCHAR(255),
    parameters JSONB DEFAULT '{}',
    policy_id UUID REFERENCES policies(id),
    policy_version VARCHAR(50),
    rules_evaluated JSONB DEFAULT '[]',
    evaluation_context JSONB DEFAULT '{}',
    decision_reason TEXT,
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    deterministic BOOLEAN DEFAULT TRUE,
    redaction_fields JSONB DEFAULT '[]',
    redaction_method VARCHAR(50) DEFAULT 'mask',
    escalation_id UUID,
    escalated_to VARCHAR(255),
    escalation_status VARCHAR(50),
    quarantine_id UUID,
    quarantine_scope VARCHAR(50),
    evidence_ids JSONB DEFAULT '[]',
    audit_trail_id UUID,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    decided_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    evaluation_latency_ms INTEGER DEFAULT 0,
    total_latency_ms INTEGER DEFAULT 0
);

CREATE INDEX idx_enforcement_agent ON enforcement_decisions(agent_id);
CREATE INDEX idx_enforcement_policy ON enforcement_decisions(policy_id);
CREATE INDEX idx_enforcement_decision ON enforcement_decisions(decision);
CREATE INDEX idx_enforcement_timestamp ON enforcement_decisions(decided_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- AUDIT TRAIL (Merkle Chain)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE audit_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id VARCHAR(255) UNIQUE NOT NULL,
    sequence_number BIGINT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(255),
    actor_type VARCHAR(50) DEFAULT 'system',
    resource VARCHAR(255),
    outcome VARCHAR(100),
    details JSONB DEFAULT '{}',
    previous_hash VARCHAR(256) NOT NULL,
    entry_hash VARCHAR(256) NOT NULL,
    merkle_root VARCHAR(256),
    signature VARCHAR(512),
    tenant_id VARCHAR(100),
    trace_id UUID,
    span_id UUID
);

CREATE INDEX idx_audit_timestamp ON audit_entries(timestamp);
CREATE INDEX idx_audit_event_type ON audit_entries(event_type);
CREATE INDEX idx_audit_actor ON audit_entries(actor);
CREATE INDEX idx_audit_tenant ON audit_entries(tenant_id);
CREATE INDEX idx_audit_sequence ON audit_entries(sequence_number);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SUPPORTING TABLES
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─── Agents ─────────────────────────────────────────────────────────────────
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'autonomous' CHECK (type IN ('autonomous', 'semi_autonomous', 'human_in_loop', 'human_on_loop')),
    status VARCHAR(50) DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved', 'active', 'deprecated', 'terminated')),
    unique_id VARCHAR(500),
    attestation TEXT,
    trust_score DECIMAL(3,2) DEFAULT 0.5,
    capabilities JSONB DEFAULT '[]',
    owner VARCHAR(255),
    owning_team VARCHAR(255),
    business_unit VARCHAR(255),
    policy_ids JSONB DEFAULT '[]',
    enforcement_profile VARCHAR(255),
    assessment_schedule VARCHAR(100),
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    deprecated_at TIMESTAMPTZ,
    termination_reason TEXT
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_owner ON agents(owner);

-- ─── Controls ───────────────────────────────────────────────────────────────
CREATE TABLE controls (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    family VARCHAR(255),
    frameworks JSONB DEFAULT '[]',
    implementation_type VARCHAR(50) DEFAULT 'automated',
    policy_ids JSONB DEFAULT '[]',
    evidence_requirements JSONB DEFAULT '[]',
    test_procedure TEXT,
    related_controls JSONB DEFAULT '[]',
    parent_control VARCHAR(255)
);

-- ─── Frameworks ─────────────────────────────────────────────────────────────
CREATE TABLE frameworks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    type VARCHAR(50) DEFAULT 'standards' CHECK (type IN ('regulatory', 'standards', 'internal', 'custom')),
    domains JSONB DEFAULT '[]',
    crosswalks JSONB DEFAULT '[]',
    source_url TEXT,
    effective_date VARCHAR(50),
    review_cycle VARCHAR(50)
);

-- ─── Risks ──────────────────────────────────────────────────────────────────
CREATE TABLE risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) CHECK (category IN ('model', 'data', 'security', 'compliance', 'operational', 'reputational')),
    likelihood VARCHAR(50) CHECK (likelihood IN ('rare', 'unlikely', 'possible', 'likely', 'almost_certain')),
    impact VARCHAR(50) CHECK (impact IN ('negligible', 'minor', 'moderate', 'major', 'catastrophic')),
    risk_score DECIMAL(5,2),
    risk_tier VARCHAR(50) CHECK (risk_tier IN ('low', 'medium', 'high', 'critical')),
    treatment VARCHAR(50) CHECK (treatment IN ('avoid', 'transfer', 'mitigate', 'accept')),
    treatment_plan TEXT,
    residual_risk DECIMAL(5,2),
    risk_owner VARCHAR(255),
    review_date TIMESTAMPTZ,
    related_controls JSONB DEFAULT '[]',
    related_policies JSONB DEFAULT '[]',
    related_agents JSONB DEFAULT '[]',
    related_findings JSONB DEFAULT '[]'
);

-- ─── Findings ───────────────────────────────────────────────────────────────
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(50) CHECK (severity IN ('critical', 'high', 'medium', 'low', 'informational')),
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'accepted', 'false_positive')),
    source VARCHAR(50) CHECK (source IN ('assessment', 'monitoring', 'incident', 'audit', 'manual')),
    source_id VARCHAR(255),
    control_id VARCHAR(255),
    policy_id UUID REFERENCES policies(id),
    agent_id UUID REFERENCES agents(id),
    evidence_ids JSONB DEFAULT '[]',
    remediation_plan TEXT,
    assigned_to VARCHAR(255),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    verified_by VARCHAR(255),
    identified_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    sla_breach BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_findings_status ON findings(status);
CREATE INDEX idx_findings_severity ON findings(severity);

-- ─── Event Store (for CQRS/Event Sourcing) ─────────────────────────────────
CREATE TABLE event_store (
    event_id UUID PRIMARY KEY,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    event_type VARCHAR(200) NOT NULL,
    event_version INTEGER NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sequence_number BIGSERIAL NOT NULL,
    correlation_id UUID,
    causation_id UUID,
    payload JSONB NOT NULL,
    metadata JSONB,
    UNIQUE (aggregate_id, event_version)
);

CREATE INDEX idx_event_store_aggregate ON event_store (aggregate_id, event_version);
CREATE INDEX idx_event_store_tenant ON event_store (tenant_id, timestamp);
CREATE INDEX idx_event_store_type ON event_store (event_type, timestamp);
CREATE INDEX idx_event_store_correlation ON event_store (correlation_id);

-- ─── Saga Instances ─────────────────────────────────────────────────────────
CREATE TABLE saga_instances (
    saga_id UUID PRIMARY KEY,
    saga_name VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('STARTED', 'COMPLETED', 'COMPENSATING', 'COMPENSATED', 'COMPENSATION_FAILED')),
    current_step INTEGER NOT NULL DEFAULT 0,
    input JSONB NOT NULL,
    step_results JSONB NOT NULL DEFAULT '{}',
    compensated_steps TEXT[] DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tenant_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_saga_status ON saga_instances (status, started_at);
CREATE INDEX idx_saga_tenant ON saga_instances (tenant_id, started_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- VIEWS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Compliance summary view
CREATE VIEW v_compliance_summary AS
SELECT
    cp.organization_id,
    cp.framework,
    cp.framework_name,
    cp.overall_status,
    cp.compliance_score,
    cp.trend,
    cp.coverage_percentage,
    cp.compliant_controls,
    cp.partial_controls,
    cp.non_compliant_controls,
    cp.not_assessed_controls,
    cp.total_controls,
    cp.computed_at
FROM compliance_postures cp;

-- Agent governance view
CREATE VIEW v_agent_governance AS
SELECT
    a.id AS agent_id,
    a.name AS agent_name,
    a.status,
    a.trust_score,
    COUNT(DISTINCT ed.id) AS total_enforcements,
    COUNT(DISTINCT CASE WHEN ed.decision = 'deny' THEN ed.id END) AS deny_count,
    COUNT(DISTINCT CASE WHEN ed.decision = 'allow' THEN ed.id END) AS allow_count,
    COUNT(DISTINCT CASE WHEN ed.decision = 'require_approval' THEN ed.id END) AS approval_count,
    COUNT(DISTINCT p.id) AS policy_count
FROM agents a
LEFT JOIN enforcement_decisions ed ON ed.agent_id = a.name
LEFT JOIN policies p ON p.status = 'active'
GROUP BY a.id, a.name, a.status, a.trust_score;

-- Evidence coverage view
CREATE VIEW v_evidence_coverage AS
SELECT
    e.type,
    e.verification_level,
    COUNT(*) AS count,
    MIN(e.timestamp) AS oldest,
    MAX(e.timestamp) AS newest
FROM evidence e
GROUP BY e.type, e.verification_level;

-- ═══════════════════════════════════════════════════════════════════════════════
-- FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════════

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_evidence_updated_at
    BEFORE UPDATE ON evidence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_assessments_updated_at
    BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_compliance_mappings_updated_at
    BEFORE UPDATE ON compliance_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
