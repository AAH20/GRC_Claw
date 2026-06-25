export type FrameworkCode = "iso27001" | "nist-csf" | "soc2" | "iso42001" | "eu-ai-act" | "gdpr" | "hipaa" | "pci-dss" | "fedramp";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: string;
  settings: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  tenantId: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  lastLoginAt?: string;
  createdAt: string;
}

export interface Framework {
  id: string;
  code: FrameworkCode;
  name: string;
  version: string;
  controls: Record<string, unknown>[];
  createdAt: string;
}

export interface Control {
  id: string;
  frameworkId: string;
  controlId: string;
  title: string;
  description: string;
  domain: string;
  status: string;
  evidenceCount: number;
  createdAt: string;
}

export interface ComplianceStateRecord {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  overallScore: number;
  controlScores: Record<string, number>;
  driftCount: number;
  lastCalculatedAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface EvidenceRecord {
  id: string;
  tenantId: string;
  controlId: string;
  sha256: string;
  uri: string;
  metadata: Record<string, unknown>;
  lineage: { parentId?: string; depth: number };
  collectedAt: string;
  createdAt: string;
}

export interface DriftEventRecord {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  controlId: string;
  controlCode: string;
  severity: string;
  driftType: string;
  description: string;
  remediable: boolean;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
  detectedAt: string;
  createdAt: string;
}

export interface SecurityEventRecord {
  id: string;
  tenantId: string;
  eventUuid: string;
  eventType: string;
  severity: string;
  sourceSystem: string;
  complianceImpact: { controlIds: string[]; rationale: string };
  eventData: Record<string, unknown>;
  ingestedAt: string;
  createdAt: string;
}

export interface AgentRecord {
  id: string;
  tenantId: string;
  did: string;
  name: string;
  status: string;
  trustScore: number;
  riskLevel: string;
  dimensions: Record<string, number>;
  lastScoredAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AgentCredentialRecord {
  id: string;
  agentId: string;
  type: string;
  claims: Record<string, unknown>;
  issuer: string;
  signature: string;
  issuedAt: string;
  expiresAt: string;
  revoked: boolean;
  createdAt: string;
}

export interface PlaybookExecutionRecord {
  id: string;
  tenantId: string;
  playbookName: string;
  status: string;
  steps: Record<string, unknown>[];
  slaMs: number;
  startedAt?: string;
  completedAt?: string;
  evidenceHashes: string[];
  createdAt: string;
}

export interface RegulatoryChangeRecord {
  id: string;
  sourceId: string;
  title: string;
  summary: string;
  fullText: string;
  changeType: string;
  jurisdiction: string;
  frameworkCode: FrameworkCode;
  affectedControls: string[];
  impactLevel: string;
  impactAnalysis: Record<string, unknown>;
  status: string;
  detectedAt: string;
  createdAt: string;
}

export interface TrustScoreRecord {
  id: string;
  agentId: string;
  overallScore: number;
  dimensions: Record<string, number>;
  riskFactors: Record<string, unknown>[];
  trigger: string;
  scoredAt: string;
  createdAt: string;
}

export interface ActionLedgerRecord {
  id: string;
  tenantId: string;
  agentId?: string;
  action: string;
  toolName: string;
  toolTier: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
  sha256: string;
  parentId?: string;
  executedAt: string;
  createdAt: string;
}

export interface RemediationPlanRecord {
  id: string;
  tenantId: string;
  driftEventId: string;
  controlId: string;
  actions: Record<string, unknown>[];
  status: string;
  result: Record<string, unknown>;
  executedAt?: string;
  completedAt?: string;
  createdAt: string;
}

export interface ComplianceSnapshotRecord {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  overallScore: number;
  controlCount: number;
  passingControls: number;
  failingControls: number;
  driftEvents: Record<string, unknown>[];
  snapshotAt: string;
  createdAt: string;
}

export const MIGRATION_SQL = `
-- GRC_Claw Schema Migration
-- Requires PostgreSQL 13+ (for gen_random_uuid)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. tenants
CREATE TABLE IF NOT EXISTS tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  plan VARCHAR(50) NOT NULL DEFAULT 'free',
  settings JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'viewer',
  permissions JSONB NOT NULL DEFAULT '[]',
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);

-- 3. frameworks
CREATE TABLE IF NOT EXISTS frameworks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  version VARCHAR(50) NOT NULL,
  controls JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. controls
CREATE TABLE IF NOT EXISTS controls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  framework_id UUID NOT NULL REFERENCES frameworks(id) ON DELETE CASCADE,
  control_id VARCHAR(100) NOT NULL,
  title VARCHAR(500) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  domain VARCHAR(255) NOT NULL DEFAULT '',
  status VARCHAR(50) NOT NULL DEFAULT 'unmapped',
  evidence_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_controls_framework ON controls(framework_id);
CREATE INDEX IF NOT EXISTS idx_controls_status ON controls(status);

-- 5. compliance_state
CREATE TABLE IF NOT EXISTS compliance_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  framework_code VARCHAR(50) NOT NULL,
  overall_score DECIMAL(5,2) NOT NULL DEFAULT 0,
  control_scores JSONB NOT NULL DEFAULT '{}',
  drift_count INT NOT NULL DEFAULT 0,
  last_calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_compliance_state_tenant_framework
  ON compliance_state(tenant_id, framework_code);

-- 6. evidence
CREATE TABLE IF NOT EXISTS evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  control_id UUID NOT NULL,
  sha256 VARCHAR(64) NOT NULL,
  uri TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  lineage JSONB NOT NULL DEFAULT '{"depth":0}',
  collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_evidence_tenant ON evidence(tenant_id);
CREATE INDEX IF NOT EXISTS idx_evidence_control ON evidence(control_id);

-- 7. drift_events
CREATE TABLE IF NOT EXISTS drift_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  framework_code VARCHAR(50) NOT NULL,
  control_id UUID NOT NULL,
  control_code VARCHAR(100) NOT NULL,
  severity VARCHAR(50) NOT NULL DEFAULT 'medium',
  drift_type VARCHAR(50) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  remediable BOOLEAN NOT NULL DEFAULT false,
  resolved BOOLEAN NOT NULL DEFAULT false,
  resolved_at TIMESTAMPTZ,
  resolved_by UUID,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_drift_events_tenant ON drift_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_drift_events_unresolved ON drift_events(tenant_id, resolved) WHERE resolved = false;

-- 8. security_events
CREATE TABLE IF NOT EXISTS security_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  event_uuid UUID NOT NULL UNIQUE,
  event_type VARCHAR(100) NOT NULL,
  severity VARCHAR(50) NOT NULL DEFAULT 'info',
  source_system VARCHAR(255) NOT NULL,
  compliance_impact JSONB NOT NULL DEFAULT '{"controlIds":[],"rationale":""}',
  event_data JSONB NOT NULL DEFAULT '{}',
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_security_events_tenant ON security_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);

-- 9. agents
CREATE TABLE IF NOT EXISTS agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  did VARCHAR(500) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  trust_score DECIMAL(5,2) NOT NULL DEFAULT 0,
  risk_level VARCHAR(50) NOT NULL DEFAULT 'unknown',
  dimensions JSONB NOT NULL DEFAULT '{}',
  last_scored_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);

-- 10. agent_credentials
CREATE TABLE IF NOT EXISTS agent_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  claims JSONB NOT NULL DEFAULT '{}',
  issuer VARCHAR(255) NOT NULL,
  signature TEXT NOT NULL,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_agent_credentials_agent ON agent_credentials(agent_id);

-- 11. playbook_executions
CREATE TABLE IF NOT EXISTS playbook_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  playbook_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  steps JSONB NOT NULL DEFAULT '[]',
  sla_ms BIGINT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  evidence_hashes JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_playbook_executions_tenant ON playbook_executions(tenant_id);

-- 12. regulatory_changes
CREATE TABLE IF NOT EXISTS regulatory_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id VARCHAR(255) NOT NULL UNIQUE,
  title VARCHAR(500) NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  full_text TEXT NOT NULL DEFAULT '',
  change_type VARCHAR(50) NOT NULL,
  jurisdiction VARCHAR(255) NOT NULL,
  framework_code VARCHAR(50) NOT NULL,
  affected_controls JSONB NOT NULL DEFAULT '[]',
  impact_level VARCHAR(50) NOT NULL DEFAULT 'low',
  impact_analysis JSONB NOT NULL DEFAULT '{}',
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_regulatory_changes_framework ON regulatory_changes(framework_code);

-- 13. trust_scores
CREATE TABLE IF NOT EXISTS trust_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  overall_score DECIMAL(5,2) NOT NULL,
  dimensions JSONB NOT NULL DEFAULT '{}',
  risk_factors JSONB NOT NULL DEFAULT '[]',
  trigger VARCHAR(255) NOT NULL,
  scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_trust_scores_agent ON trust_scores(agent_id);

-- 14. action_ledger
CREATE TABLE IF NOT EXISTS action_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  agent_id UUID,
  action VARCHAR(255) NOT NULL,
  tool_name VARCHAR(255) NOT NULL,
  tool_tier VARCHAR(50) NOT NULL,
  args JSONB NOT NULL DEFAULT '{}',
  result JSONB NOT NULL DEFAULT '{}',
  sha256 VARCHAR(64) NOT NULL,
  parent_id UUID,
  executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_action_ledger_tenant ON action_ledger(tenant_id);
CREATE INDEX IF NOT EXISTS idx_action_ledger_agent ON action_ledger(agent_id);

-- 15. remediation_plans
CREATE TABLE IF NOT EXISTS remediation_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  drift_event_id UUID NOT NULL,
  control_id UUID NOT NULL,
  actions JSONB NOT NULL DEFAULT '[]',
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  result JSONB NOT NULL DEFAULT '{}',
  executed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_remediation_plans_tenant ON remediation_plans(tenant_id);
CREATE INDEX IF NOT EXISTS idx_remediation_plans_status ON remediation_plans(status);

-- 16. compliance_snapshots
CREATE TABLE IF NOT EXISTS compliance_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  framework_code VARCHAR(50) NOT NULL,
  overall_score DECIMAL(5,2) NOT NULL,
  control_count INT NOT NULL DEFAULT 0,
  passing_controls INT NOT NULL DEFAULT 0,
  failing_controls INT NOT NULL DEFAULT 0,
  drift_events JSONB NOT NULL DEFAULT '[]',
  snapshot_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compliance_snapshots_tenant ON compliance_snapshots(tenant_id);
`;
