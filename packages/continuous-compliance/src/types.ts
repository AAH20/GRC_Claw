export type FrameworkCode =
  | "iso27001"
  | "nist-csf"
  | "soc2"
  | "iso42001"
  | "eu-ai-act"
  | "dora"
  | "nis2"
  | "hipaa"
  | "pci-dss"
  | "fedramp"
  | "cmmc"
  | "gdpr"
  | "lgpd"
  | "pipl"
  | "tisax"
  | "popia";

export type MonitorType = "realtime" | "periodic" | "event_driven" | "continuous";
export type DriftSeverity = "info" | "low" | "medium" | "high" | "critical";
export type RemediationAction = "auto_fix" | "alert" | "quarantine" | "rollback" | "escalate" | "block" | "log_evidence";
export type PostureTrend = "improving" | "stable" | "degrading" | "critical";

export interface ComplianceBaseline {
  frameworkCode: FrameworkCode;
  tenantId: string;
  controls: ControlBaseline[];
  snapshotAt: string;
  version: number;
}

export interface ControlBaseline {
  controlId: string;
  controlCode: string;
  expectedStatus: "implemented" | "not_applicable" | "in_progress";
  evidenceHashes: string[];
  lastVerifiedAt: string;
  owner?: string;
}

export interface DriftEvent {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  controlId: string;
  controlCode: string;
  detectedAt: string;
  severity: DriftSeverity;
  driftType: DriftType;
  description: string;
  evidenceBefore?: string;
  evidenceAfter?: string;
  remediable: boolean;
  autoRemediation?: RemediationAction;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
}

export type DriftType =
  | "evidence_missing"
  | "evidence_tampered"
  | "control_disabled"
  | "config_changed"
  | "new_risk_detected"
  | "access_violation"
  | "policy_violation"
  | "regulatory_change";

export interface CompliancePosture {
  tenantId: string;
  frameworkCode: FrameworkCode;
  overallScore: number;
  controlScores: Map<string, ControlPosture>;
  trend: PostureTrend;
  driftCount: number;
  unresolvedDrifts: number;
  lastCalculatedAt: string;
  riskAreas: RiskArea[];
}

export interface ControlPosture {
  controlId: string;
  controlCode: string;
  score: number;
  status: "healthy" | "degraded" | "critical" | "unknown";
  lastCheckedAt: string;
  driftEvents: DriftEvent[];
  evidenceIntegrity: boolean;
  owner?: string;
}

export interface RiskArea {
  domain: string;
  riskScore: number;
  affectedControls: string[];
  recommendation: string;
}

export interface RemediationPlan {
  id: string;
  tenantId: string;
  driftEventId: string;
  controlId: string;
  actions: RemediationStep[];
  createdAt: string;
  executedAt?: string;
  completedAt?: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  result?: RemediationResult;
}

export interface RemediationStep {
  order: number;
  action: RemediationAction;
  description: string;
  automated: boolean;
  script?: string;
  requiresApproval: boolean;
  executed: boolean;
  executedAt?: string;
  output?: string;
}

export interface RemediationResult {
  success: boolean;
  message: string;
  evidenceProduced?: string;
  actionsTaken: string[];
}

export interface MonitorConfig {
  id: string;
  name: string;
  type: MonitorType;
  tenantId: string;
  frameworkCodes: FrameworkCode[];
  intervalMs?: number;
  enabled: boolean;
  alertChannels: string[];
  autoRemediate: boolean;
  maxAutoRemediationSeverity: DriftSeverity;
}

export interface ComplianceSnapshot {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  timestamp: string;
  overallScore: number;
  controlCount: number;
  passingControls: number;
  failingControls: number;
  driftEvents: DriftEvent[];
}
