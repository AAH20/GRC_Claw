import { createHash, randomUUID } from 'node:crypto';

// ─── Core Types ─────────────────────────────────────────────────────

export type ControlStatus = 'compliant' | 'non_compliant' | 'partial' | 'unknown';
export type GapSeverity = 'critical' | 'high' | 'medium' | 'low';
export type RemediationStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'verified';
export type AuditAction = 'monitor' | 'detect' | 'remediate' | 'verify' | 'report' | 'sign';

export interface Control {
  id: string;
  controlId: string;
  title: string;
  framework: string;
  status: ControlStatus;
  owner?: string;
  lastCheckedAt?: string;
}

export interface EvidenceRecord {
  id: string;
  controlId: string;
  tenantId: number;
  sha256: string;
  uri: string;
  collectedAt: string;
  lineage: { parentHash?: string; source: string };
}

export interface ComplianceGap {
  id: string;
  controlId: string;
  controlTitle: string;
  framework: string;
  severity: GapSeverity;
  description: string;
  detectedAt: string;
  evidenceCount: number;
}

export interface RemediationPlan {
  id: string;
  gapId: string;
  controlId: string;
  framework: string;
  actions: RemediationAction[];
  status: RemediationStatus;
  createdAt: string;
  completedAt?: string;
  verifiedAt?: string;
  signature?: string;
}

export interface RemediationAction {
  id: string;
  type: 'collect_evidence' | 'update_control' | 'generate_report' | 'notify_owner' | 'custom';
  description: string;
  parameters: Record<string, unknown>;
  status: RemediationStatus;
  executedAt?: string;
}

export interface ComplianceReport {
  id: string;
  framework: string;
  generatedAt: string;
  totalControls: number;
  compliantControls: number;
  nonCompliantControls: number;
  partialControls: number;
  unknownControls: number;
  complianceScore: number;
  gaps: ComplianceGap[];
  remediations: RemediationPlan[];
  signature?: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  action: AuditAction;
  actor: string;
  target: string;
  details: Record<string, unknown>;
  previousHash: string;
  hash: string;
  signature?: string;
}

export interface AutopilotConfig {
  frameworks: string[];
  tenantId: number;
  monitorIntervalMs?: number;
  autoRemediate?: boolean;
  maxConcurrentRemediations?: number;
  evidenceDb?: EvidenceDatabase;
  signingKey?: string;
}

export interface EvidenceDatabase {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>;
  execute(sql: string, params?: unknown[]): Promise<void>;
}

export interface MonitorResult {
  timestamp: string;
  frameworksChecked: string[];
  controlsChecked: number;
  gapsFound: number;
  gaps: ComplianceGap[];
}

export interface CycleResult {
  cycleId: string;
  startedAt: string;
  completedAt: string;
  monitor: MonitorResult;
  remediations: RemediationPlan[];
  verificationResults: VerificationResult[];
  report?: ComplianceReport;
  auditTrail: AuditEntry[];
}

export interface VerificationResult {
  remediationId: string;
  controlId: string;
  verified: boolean;
  previousStatus: ControlStatus;
  currentStatus: ControlStatus;
  verifiedAt: string;
}
