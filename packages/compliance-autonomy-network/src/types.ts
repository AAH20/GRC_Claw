import type { Hash } from "node:crypto";

// ============================================================================
// Framework & Domain Types
// ============================================================================

export type ComplianceFramework =
  | "SOC2"
  | "ISO27001"
  | "NIST_CSF"
  | "PCI_DSS"
  | "HIPAA"
  | "GDPR"
  | "CCPA"
  | "SOX"
  | "FedRAMP"
  | "Custom";

export type TaskPriority = "critical" | "high" | "medium" | "low";

export type AgentRole =
  | "evidence-collector"
  | "control-tester"
  | "risk-quantifier"
  | "audit-preparer"
  | "remediation-executor"
  | "verifier";

export type TaskStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "timeout"
  | "cancelled";

export type EvidenceKind =
  | "configuration"
  | "log"
  | "policy"
  | "scan"
  | "audit"
  | "metric"
  | "screenshot"
  | "api-response"
  | "system-info";

export type RiskLevel = "critical" | "high" | "medium" | "low" | "informational";

// ============================================================================
// Trust & Integrity Types
// ============================================================================

export interface TrustSignature {
  readonly agentId: string;
  readonly agentRole: AgentRole;
  readonly timestamp: string;
  readonly contentHash: string;
  readonly previousHash: string;
  readonly nonce: number;
  readonly signature: string;
}

export interface TrustChainLink {
  readonly taskId: string;
  readonly agentId: string;
  readonly role: AgentRole;
  readonly action: string;
  readonly inputHash: string;
  readonly outputHash: string;
  readonly timestamp: string;
  readonly previousLinkHash: string;
}

// ============================================================================
// Core Swarm Types
// ============================================================================

export interface SwarmTask {
  readonly id: string;
  readonly goalId: string;
  readonly type: TaskType;
  readonly framework: ComplianceFramework;
  readonly priority: TaskPriority;
  readonly description: string;
  readonly input: TaskInput;
  readonly assignedAgent?: AgentRole;
  readonly dependencies: string[];
  readonly timeoutMs: number;
  readonly createdAt: string;
  readonly metadata: Record<string, unknown>;
}

export type TaskType =
  | "evidence-collection"
  | "control-testing"
  | "risk-quantification"
  | "audit-preparation"
  | "remediation-execution"
  | "verification"
  | "cross-framework-mapping";

export interface TaskInput {
  readonly controlIds?: string[];
  readonly evidenceCriteria?: EvidenceCriteria;
  readonly riskScope?: RiskScope;
  readonly auditWindow?: AuditWindow;
  readonly remediationPlan?: RemediationPlanInput;
  readonly scope?: string[];
  readonly customParameters?: Record<string, unknown>;
}

export interface EvidenceCriteria {
  readonly framework: ComplianceFramework;
  readonly controlFamilies: string[];
  readonly evidenceTypes: EvidenceKind[];
  readonly sources: string[];
  readonly dateRange?: { from: string; to: string };
}

export interface RiskScope {
  readonly assetCategories: string[];
  readonly threatCategories: string[];
  readonly businessImpact: "critical" | "high" | "medium" | "low";
  readonly regulatoryRisk: boolean;
}

export interface AuditWindow {
  readonly startDate: string;
  readonly endDate: string;
  readonly frameworks: ComplianceFramework[];
  readonly includeHistoricalEvidence: boolean;
}

export interface RemediationPlanInput {
  readonly issueId: string;
  readonly controlId: string;
  readonly severity: RiskLevel;
  readonly autoApprove: boolean;
}

// ============================================================================
// Agent Types
// ============================================================================

export interface SwarmAgent {
  readonly id: string;
  readonly role: AgentRole;
  readonly name: string;
  readonly version: string;
  readonly capabilities: AgentCapability[];
  readonly trustScore: number;
  readonly status: AgentStatus;
  readonly maxConcurrentTasks: number;
  readonly currentTaskCount: number;
}

export type AgentStatus = "idle" | "busy" | "offline" | "error";

export interface AgentCapability {
  readonly name: string;
  readonly frameworks: ComplianceFramework[];
  readonly confidenceLevel: number;
}

// ============================================================================
// Result Types
// ============================================================================

export interface SwarmResult {
  readonly taskId: string;
  readonly agentId: string;
  readonly agentRole: AgentRole;
  readonly status: TaskStatus;
  readonly output: TaskOutput;
  readonly trustSignature: TrustSignature;
  readonly executionTimeMs: number;
  readonly startedAt: string;
  readonly completedAt: string;
  readonly error?: string;
}

export interface TaskOutput {
  readonly evidence?: EvidenceItem[];
  readonly controlStatuses?: ControlStatus[];
  readonly riskAssessment?: RiskAssessment;
  readonly auditPackage?: AuditPackage;
  readonly remediationResults?: RemediationResult[];
  readonly verificationResults?: VerificationResult[];
  readonly crossFrameworkMappings?: CrossFrameworkMapping[];
  readonly summary: string;
  readonly recommendations: string[];
}

export interface EvidenceItem {
  readonly id: string;
  readonly kind: EvidenceKind;
  readonly source: string;
  readonly controlId: string;
  readonly framework: ComplianceFramework;
  readonly content: string;
  readonly contentHash: string;
  readonly collectedAt: string;
  readonly collectorAgentId: string;
  readonly trustSignature: TrustSignature;
  readonly metadata: Record<string, unknown>;
}

export interface ControlStatus {
  readonly controlId: string;
  readonly framework: ComplianceFramework;
  readonly title: string;
  readonly status: "compliant" | "non-compliant" | "partial" | "not-assessed";
  readonly confidence: number;
  readonly evidenceCount: number;
  readonly findings: Finding[];
  readonly lastTestedAt: string;
  readonly testedBy: string;
}

export interface Finding {
  readonly id: string;
  readonly severity: RiskLevel;
  readonly title: string;
  readonly description: string;
  readonly affectedResources: string[];
  readonly recommendation: string;
}

export interface RiskAssessment {
  readonly overallScore: number;
  readonly riskLevel: RiskLevel;
  readonly frameworkBreakdown: FrameworkRiskBreakdown[];
  readonly topRisks: RiskItem[];
  readonly mitigatedRisks: string[];
  readonly residualRiskScore: number;
  readonly calculatedAt: string;
}

export interface FrameworkRiskBreakdown {
  readonly framework: ComplianceFramework;
  readonly score: number;
  readonly riskLevel: RiskLevel;
  readonly controlsCompliant: number;
  readonly controlsNonCompliant: number;
  readonly controlsPartial: number;
  readonly controlsTotal: number;
}

export interface RiskItem {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly riskLevel: RiskLevel;
  readonly likelihood: number;
  readonly impact: number;
  readonly score: number;
  readonly relatedControls: string[];
  readonly mitigationStatus: "unmitigated" | "partially-mitigated" | "fully-mitigated";
}

export interface AuditPackage {
  readonly id: string;
  readonly title: string;
  readonly frameworks: ComplianceFramework[];
  readonly period: { from: string; to: string };
  readonly sections: AuditSection[];
  readonly executiveSummary: string;
  readonly complianceScore: number;
  readonly readinessLevel: "ready" | "mostly-ready" | "gaps-identified" | "not-ready";
  readonly gaps: AuditGap[];
  readonly generatedAt: string;
  readonly generatedBy: string;
}

export interface AuditSection {
  readonly title: string;
  readonly framework: ComplianceFramework;
  readonly controlFamily: string;
  readonly narrative: string;
  readonly evidenceIds: string[];
  readonly controlStatuses: ControlStatus[];
}

export interface AuditGap {
  readonly controlId: string;
  readonly framework: ComplianceFramework;
  readonly gapDescription: string;
  readonly severity: RiskLevel;
  readonly remediation: string;
  readonly estimatedEffort: string;
}

export interface RemediationResult {
  readonly issueId: string;
  readonly controlId: string;
  readonly action: string;
  readonly status: "executed" | "failed" | "skipped" | "pending-approval" | "rolled-back";
  readonly executedAt?: string;
  readonly output?: string;
  readonly verificationPassed?: boolean;
}

export interface VerificationResult {
  readonly controlId: string;
  readonly framework: ComplianceFramework;
  readonly checkType: string;
  readonly passed: boolean;
  readonly expected: string;
  readonly actual: string;
  readonly verifiedAt: string;
  readonly verifiedBy: string;
}

export interface CrossFrameworkMapping {
  readonly sourceControlId: string;
  readonly sourceFramework: ComplianceFramework;
  readonly targetControlId: string;
  readonly targetFramework: ComplianceFramework;
  readonly equivalenceScore: number;
  readonly mappingType: "direct" | "partial" | "derived";
}

// ============================================================================
// Message Types (Inter-Agent Communication)
// ============================================================================

export interface AgentMessage {
  readonly id: string;
  readonly from: AgentRole;
  readonly to: AgentRole | "coordinator" | "broadcast";
  readonly type: MessageType;
  readonly taskId: string;
  readonly goalId: string;
  readonly payload: MessagePayload;
  readonly timestamp: string;
  readonly replyTo?: string;
  readonly requiresResponse: boolean;
}

export type MessageType =
  | "task-delegation"
  | "task-completed"
  | "task-failed"
  | "evidence-shared"
  | "risk-alert"
  | "status-update"
  | "policy-violation"
  | "coordination-request"
  | "audit-ready";

export type MessagePayload =
  | TaskDelegationPayload
  | TaskCompletedPayload
  | TaskFailedPayload
  | EvidenceSharedPayload
  | RiskAlertPayload
  | StatusUpdatePayload
  | PolicyViolationPayload
  | CoordinationRequestPayload
  | AuditReadyPayload;

export interface TaskDelegationPayload {
  readonly kind: "task-delegation";
  readonly task: SwarmTask;
}

export interface TaskCompletedPayload {
  readonly kind: "task-completed";
  readonly result: SwarmResult;
}

export interface TaskFailedPayload {
  readonly kind: "task-failed";
  readonly taskId: string;
  readonly error: string;
}

export interface EvidenceSharedPayload {
  readonly kind: "evidence-shared";
  readonly evidence: EvidenceItem[];
}

export interface RiskAlertPayload {
  readonly kind: "risk-alert";
  readonly risks: RiskItem[];
  readonly severity: RiskLevel;
}

export interface StatusUpdatePayload {
  readonly kind: "status-update";
  readonly agentStatus: AgentStatus;
  readonly progress: number;
  readonly message: string;
}

export interface PolicyViolationPayload {
  readonly kind: "policy-violation";
  readonly violation: string;
  readonly policyId: string;
  readonly blocked: boolean;
}

export interface CoordinationRequestPayload {
  readonly kind: "coordination-request";
  readonly requestType: string;
  readonly data: Record<string, unknown>;
}

export interface AuditReadyPayload {
  readonly kind: "audit-ready";
  readonly package: AuditPackage;
}

// ============================================================================
// Compliance Goal Types
// ============================================================================

export interface ComplianceGoal {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly targetFrameworks: ComplianceFramework[];
  readonly targetDate: string;
  readonly priority: TaskPriority;
  readonly scope: string[];
  readonly metadata: Record<string, unknown>;
}

export interface GoalDecomposition {
  readonly goalId: string;
  readonly tasks: SwarmTask[];
  readonly executionPlan: ExecutionPlan;
  readonly estimatedDurationMs: number;
  readonly requiredAgents: AgentRole[];
  readonly parallelizableGroups: string[][];
}

export interface ExecutionPlan {
  readonly phases: ExecutionPhase[];
  readonly totalEstimatedMs: number;
  readonly criticalPath: string[];
}

export interface ExecutionPhase {
  readonly id: string;
  readonly name: string;
  readonly taskIds: string[];
  readonly dependsOn: string[];
  readonly parallel: boolean;
  readonly estimatedMs: number;
}

// ============================================================================
// Compliance Report Types
// ============================================================================

export interface ComplianceReport {
  readonly id: string;
  readonly goalId: string;
  readonly goal: ComplianceGoal;
  readonly generatedAt: string;
  readonly frameworks: ComplianceFramework[];
  readonly overallComplianceScore: number;
  readonly riskAssessment: RiskAssessment;
  readonly controlStatuses: ControlStatus[];
  readonly evidenceSummary: EvidenceSummary;
  readonly auditPackage?: AuditPackage;
  readonly remediationsSummary: RemediationSummary;
  readonly crossFrameworkMappings: CrossFrameworkMapping[];
  readonly agentActivityLog: TrustChainLink[];
  readonly recommendations: string[];
  readonly nextSteps: string[];
  readonly integrityHash: string;
}

export interface EvidenceSummary {
  readonly totalItems: number;
  readonly byFramework: Record<ComplianceFramework, number>;
  readonly byKind: Record<EvidenceKind, number>;
  readonly integrityVerified: boolean;
}

export interface RemediationSummary {
  readonly totalIssues: number;
  readonly remediated: number;
  readonly pending: number;
  readonly failed: number;
  readonly autoRemediated: number;
  readonly manualRequired: number;
}

// ============================================================================
// Coordinator Config
// ============================================================================

export interface SwarmCoordinatorConfig {
  readonly maxConcurrentTasks: number;
  readonly taskTimeoutMs: number;
  readonly enablePolicyFirewall: boolean;
  readonly enableTrustChain: boolean;
  readonly logToTrustNetwork: boolean;
  readonly retryAttempts: number;
  readonly retryDelayMs: number;
  readonly dryRun: boolean;
}
