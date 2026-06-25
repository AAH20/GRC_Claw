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
