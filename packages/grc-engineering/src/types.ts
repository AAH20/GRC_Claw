import type { ComplianceControl, ControlStatus, Severity } from '@grc-claw/core';

export type { Severity } from '@grc-claw/core';
export type { ComplianceControl } from '@grc-claw/core';

// ── GrcConfig (grcfile format) ────────────────────────────────────────────

export type GrcFileFormat = 'json' | 'yaml' | 'toml';

export interface GrcConfig {
  version: string;
  org: GrcOrgMetadata;
  frameworks: GrcFrameworkBinding[];
  controls: ControlDefinition[];
  evidenceSources: EvidenceSource[];
  complianceRules: ComplianceRule[];
  pipelines?: GrcPipelineRef[];
  branchProtection?: BranchProtectionConfig;
}

export interface GrcOrgMetadata {
  name: string;
  tenantId: number;
  slug: string;
  complianceEmail?: string;
}

export interface GrcFrameworkBinding {
  code: string;
  version?: string;
  enabledControls: string[];
}

export interface BranchProtectionConfig {
  requireReview: boolean;
  requireStatusChecks: string[];
  requireSignedCommits: boolean;
  restrictPushes: boolean;
}

export interface GrcPipelineRef {
  name: string;
  path: string;
}

// ── ControlDefinition ─────────────────────────────────────────────────────

export interface ControlDefinition {
  id: string;
  controlCode: string;
  title: string;
  frameworkCode: string;
  domain?: string;
  description?: string;
  implementationStatus: ControlStatus;
  evidenceRequired: EvidenceRequirement[];
  autoCollect?: AutoCollectConfig;
  schedule?: string;
  tags?: string[];
}

export interface EvidenceRequirement {
  type: EvidenceType;
  description: string;
  minimumCount: number;
  maxAgeDays?: number;
}

export type EvidenceType =
  | 'screenshot'
  | 'document'
  | 'log_excerpt'
  | 'config_dump'
  | 'policy_hash'
  | 'scan_result'
  | 'api_response'
  | 'manual attestation';

export interface AutoCollectConfig {
  method: 'api_poll' | 'webhook' | 'cron' | 'git_hook';
  endpoint?: string;
  cron?: string;
  headers?: Record<string, string>;
}

// ── EvidenceSource ────────────────────────────────────────────────────────

export interface EvidenceSource {
  id: string;
  name: string;
  type: EvidenceSourceType;
  endpoint?: string;
  authRef?: string;
  pollIntervalMs?: number;
  config: Record<string, unknown>;
}

export type EvidenceSourceType =
  | 'cloud_api'
  | 'siem'
  | 'scanner'
  | 'ticket_system'
  | 'git_repo'
  | 'ci_cd'
  | 'manual'
  | 'custom_webhook';

// ── ComplianceRule ────────────────────────────────────────────────────────

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  severity: Severity;
  frameworkCode: string;
  controlIds: string[];
  ruleType: ComplianceRuleType;
  condition: RuleCondition;
  autoRemediate?: RemediationAction;
}

export type ComplianceRuleType =
  | 'config_check'
  | 'evidence_freshness'
  | 'control_status'
  | 'policy_violation'
  | 'drift_detection'
  | 'custom';

export interface RuleCondition {
  field: string;
  operator: RuleOperator;
  value: unknown;
}

export type RuleOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'greater_than'
  | 'less_than'
  | 'is_empty'
  | 'is_not_empty'
  | 'regex_match';

export interface RemediationAction {
  type: 'auto_fix' | 'create_ticket' | 'notify' | 'block_deploy';
  config: Record<string, unknown>;
}

// ── AuditTrail ────────────────────────────────────────────────────────────

export interface AuditTrail {
  entries: AuditEntry[];
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  action: AuditAction;
  actor: string;
  targetType: 'control' | 'evidence' | 'config' | 'pipeline' | 'rule';
  targetId: string;
  before?: unknown;
  after?: unknown;
  metadata?: Record<string, unknown>;
}

export type AuditAction =
  | 'config.create'
  | 'config.update'
  | 'config.validate'
  | 'control.update_status'
  | 'evidence.collected'
  | 'evidence.attached'
  | 'pipeline.run_started'
  | 'pipeline.run_completed'
  | 'pipeline.stage_passed'
  | 'pipeline.stage_failed'
  | 'rule.violation'
  | 'rule.remediated'
  | 'drift.detected'
  | 'drift.resolved'
  | 'branch_protection.updated';

// ── GrcPlan (diff) ────────────────────────────────────────────────────────

export interface GrcPlan {
  id: string;
  createdAt: string;
  configHash: string;
  additions: GrcPlanChange[];
  modifications: GrcPlanChange[];
  deletions: GrcPlanChange[];
  validationErrors: ValidationError[];
  isValid: boolean;
}

export interface GrcPlanChange {
  type: 'control' | 'evidence_source' | 'compliance_rule' | 'pipeline' | 'framework_binding';
  id: string;
  before?: unknown;
  after?: unknown;
  impact: ChangeImpact;
}

export type ChangeImpact = 'none' | 'low' | 'medium' | 'high' | 'critical';

export interface ValidationError {
  path: string;
  message: string;
  severity: 'error' | 'warning';
}

// ── GrcDiff ───────────────────────────────────────────────────────────────

export interface GrcDiff {
  summary: DiffSummary;
  changes: GrcPlanChange[];
  timestamp: string;
}

export interface DiffSummary {
  controlsAdded: number;
  controlsModified: number;
  controlsRemoved: number;
  evidenceSourcesChanged: number;
  rulesChanged: number;
  pipelinesChanged: number;
  overallRisk: ChangeImpact;
}

// ── Pipeline types ────────────────────────────────────────────────────────

export type PipelineStageName = 'lint' | 'validate' | 'test' | 'deploy' | 'monitor';

export interface PipelineStageConfig {
  name: PipelineStageName;
  enabled: boolean;
  timeoutMs?: number;
  retries?: number;
  continueOnFailure?: boolean;
}

export interface PipelineRun {
  id: string;
  pipelineName: string;
  triggeredBy: string;
  startedAt: string;
  completedAt?: string;
  status: PipelineRunStatus;
  stages: PipelineStageResult[];
  evidence: PipelineEvidence[];
}

export type PipelineRunStatus =
  | 'pending'
  | 'running'
  | 'passed'
  | 'failed'
  | 'cancelled';

export interface PipelineStageResult {
  stage: PipelineStageName;
  status: PipelineRunStatus;
  startedAt: string;
  completedAt?: string;
  durationMs?: number;
  findings: StageFinding[];
  logs: string[];
}

export interface StageFinding {
  ruleId: string;
  severity: Severity;
  message: string;
  file?: string;
  line?: number;
}

export interface PipelineEvidence {
  id: string;
  stage: PipelineStageName;
  controlId: string;
  contentHash: string;
  collectedAt: string;
  uri: string;
}

// ── GitOps types ──────────────────────────────────────────────────────────

export interface DriftReport {
  detectedAt: string;
  repoState: RepoComplianceState;
  liveState: LiveComplianceState;
  driftItems: DriftItem[];
  totalDrift: number;
  severity: ChangeImpact;
}

export interface RepoComplianceState {
  commitSha: string;
  branch: string;
  configHash: string;
  controls: ComplianceControl[];
  rules: ComplianceRule[];
}

export interface LiveComplianceState {
  timestamp: string;
  controls: ComplianceControl[];
  rules: ComplianceRule[];
}

export interface DriftItem {
  type: 'control_status' | 'evidence_missing' | 'rule_changed' | 'config_field';
  id: string;
  description: string;
  repoValue: unknown;
  liveValue: unknown;
  severity: ChangeImpact;
}

export interface CompliancePRDescription {
  title: string;
  body: string;
  labels: string[];
  diff: GrcDiff;
  driftItems: DriftItem[];
  checklist: PRChecklistItem[];
}

export interface PRChecklistItem {
  label: string;
  checked: boolean;
  required: boolean;
}
