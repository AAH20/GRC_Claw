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

export type GapSeverity = "info" | "low" | "medium" | "high" | "critical";

export type ActionType =
  | "create_jira_ticket"
  | "send_slack_notification"
  | "call_api_endpoint"
  | "update_control_status";

export type RemediationStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed"
  | "verification_failed";

export type VerificationOutcome =
  | "gap_closed"
  | "gap_partially_closed"
  | "gap_persists"
  | "new_gap_detected";

// ─── Control Gap ──────────────────────────────────────────────────────

export interface ControlGap {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  controlId: string;
  controlCode: string;
  controlTitle: string;
  severity: GapSeverity;
  detectedAt: string;
  description: string;
  missingEvidence: string[];
  riskScore: number;
  autoRemediable: boolean;
  metadata: Record<string, unknown>;
}

// ─── Remediation Action ───────────────────────────────────────────────

export interface RemediationAction {
  type: ActionType;
  label: string;
  params: Record<string, unknown>;
  retryable: boolean;
  maxRetries: number;
  timeoutMs: number;
}

export interface RemediationStep {
  order: number;
  action: RemediationAction;
  description: string;
  executed: boolean;
  executedAt?: string;
  output?: Record<string, unknown>;
  error?: string;
}

// ─── Remediation Workflow ─────────────────────────────────────────────

export interface RemediationWorkflow {
  id: string;
  gapId: string;
  tenantId: string;
  controlCode: string;
  steps: RemediationStep[];
  status: RemediationStatus;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: RemediationResult;
}

// ─── Remediation Result ───────────────────────────────────────────────

export interface RemediationResult {
  workflowId: string;
  success: boolean;
  message: string;
  actionsExecuted: number;
  actionsFailed: number;
  evidenceCollected: string[];
  durationMs: number;
  residualRisk: number;
}

// ─── Verification Result ──────────────────────────────────────────────

export interface VerificationResult {
  gapId: string;
  workflowId: string;
  outcome: VerificationOutcome;
  verifiedAt: string;
  remainingGaps: string[];
  evidencePresent: string[];
  residualRisk: number;
  recommendation: string;
}

// ─── Full Cycle Report ────────────────────────────────────────────────

export interface FullCycleReport {
  id: string;
  tenantId: string;
  frameworkCode: FrameworkCode;
  startedAt: string;
  completedAt: string;
  gapsDetected: number;
  workflowsCreated: number;
  workflowsSucceeded: number;
  workflowsFailed: number;
  verificationResults: VerificationResult[];
  overallResidualRisk: number;
  summary: string;
}

// ─── Action Executor Interface ────────────────────────────────────────

export interface ActionExecutor {
  execute(action: RemediationAction, context: Record<string, unknown>): Promise<Record<string, unknown>>;
}

// ─── Gap Detector Interface ───────────────────────────────────────────

export interface ControlRecord {
  controlId: string;
  controlCode: string;
  title: string;
  frameworkCode: FrameworkCode;
  implemented: boolean;
  evidenceHashes: string[];
  lastVerifiedAt: string;
  owner?: string;
}

export interface GapDetector {
  getControls(frameworkCode: FrameworkCode): Promise<ControlRecord[]>;
}
