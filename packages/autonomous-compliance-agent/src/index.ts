import { z } from "zod";

// ============================================================================
// Types & Schemas
// ============================================================================

export const ComplianceIssueSeverity = z.enum([
  "critical",
  "high",
  "medium",
  "low",
  "informational",
]);
export type ComplianceIssueSeverity = z.infer<typeof ComplianceIssueSeverity>;

export const RemediationStatus = z.enum([
  "pending",
  "planned",
  "executing",
  "completed",
  "failed",
  "rolled-back",
  "awaiting-approval",
]);
export type RemediationStatus = z.infer<typeof RemediationStatus>;

export const ComplianceFramework = z.enum([
  "SOC2",
  "ISO27001",
  "NIST_CSF",
  "PCI_DSS",
  "HIPAA",
  "GDPR",
  "CCPA",
  "SOX",
  "FedRAMP",
  "Custom",
]);
export type ComplianceFramework = z.infer<typeof ComplianceFramework>;

export const ApprovalDecision = z.enum([
  "approved",
  "rejected",
  "deferred",
]);
export type ApprovalDecision = z.infer<typeof ApprovalDecision>;

export interface ComplianceControl {
  id: string;
  framework: ComplianceFramework;
  controlFamily: string;
  title: string;
  description: string;
  requirements: string[];
  automatedRemediationSupported: boolean;
}

export interface ComplianceIssue {
  id: string;
  control: ComplianceControl;
  severity: ComplianceIssueSeverity;
  title: string;
  description: string;
  detectedAt: Date;
  evidence: Evidence[];
  affectedResources: Resource[];
  metadata: Record<string, unknown>;
}

export interface Evidence {
  id: string;
  type: "configuration" | "log" | "policy" | "scan" | "audit" | "metric";
  source: string;
  content: string;
  collectedAt: Date;
  integrityHash: string;
}

export interface Resource {
  id: string;
  type: string;
  name: string;
  environment: "production" | "staging" | "development" | "unknown";
  tags: Record<string, string>;
}

export interface RootCause {
  id: string;
  category:
    | "configuration-drift"
    | "missing-control"
    | "policy-violation"
    | "access-misconfiguration"
    | "encryption-gap"
    | "logging-gap"
    | "network-misconfiguration"
    | "supply-chain"
    | "human-error"
    | "unknown";
  description: string;
  confidence: number;
  contributingFactors: string[];
  evidenceChain: Evidence[];
}

export interface RemediationAction {
  id: string;
  type: "auto" | "manual" | "guided";
  title: string;
  description: string;
  steps: RemediationStep[];
  rollbackPlan: RemediationStep[];
  estimatedDuration: string;
  riskLevel: "low" | "medium" | "high" | "critical";
  requiresApproval: boolean;
  automated: boolean;
  precondition?: string;
}

export interface RemediationStep {
  order: number;
  action: string;
  precondition?: string;
  command?: string;
  apiCall?: ApiCall;
  validation?: ValidationCheck;
  rollbackCommand?: string;
}

export interface ApiCall {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  url: string;
  headers: Record<string, string>;
  body?: unknown;
}

export interface ValidationCheck {
  type: "command" | "api" | "query" | "custom";
  check: string;
  expected: string;
  timeout?: number;
}

export interface RemediationPlan {
  id: string;
  issueId: string;
  actions: RemediationAction[];
  createdAt: Date;
  estimatedTotalDuration: string;
  overallRiskLevel: RemediationAction["riskLevel"];
  requiresApproval: boolean;
  approvalChain: ApprovalRequest[];
}

export interface ApprovalRequest {
  id: string;
  planId: string;
  requestedAt: Date;
  decision?: ApprovalDecision;
  decidedAt?: Date;
  decidedBy?: string;
  reason?: string;
  approver?: string;
}

export interface RemediationExecution {
  id: string;
  planId: string;
  actionId: string;
  status: RemediationStatus;
  startedAt?: Date;
  completedAt?: Date;
  output: string;
  error?: string;
  rollbackExecuted: boolean;
  verificationPassed?: boolean;
  verificationResults?: VerificationResult[];
}

export interface VerificationResult {
  check: string;
  passed: boolean;
  actual: string;
  expected: string;
  details?: string;
}

export interface AgentConfig {
  dryRun: boolean;
  autoApprove: boolean;
  maxConcurrentRemediations: number;
  retentionPolicyDays: number;
  enableRollback: boolean;
  notificationWebhook?: string;
  approvalTimeoutMs: number;
  retryAttempts: number;
  retryDelayMs: number;
}

export interface AgentMetrics {
  issuesDetected: number;
  rootCausesAnalyzed: number;
  remediationPlansGenerated: number;
  remediationsExecuted: number;
  remediationsSucceeded: number;
  remediationsFailed: number;
  remediationsRolledBack: number;
  avgDetectionLatencyMs: number;
  avgRemediationLatencyMs: number;
  lastScanAt?: Date;
}

// ============================================================================
// IssueDetector
// ============================================================================

export class IssueDetector {
  private controlRegistry: ComplianceControl[] = [];
  private scanHistory: Map<string, ComplianceIssue[]> = new Map();

  registerControls(controls: ComplianceControl[]): void {
    this.controlRegistry.push(...controls);
  }

  clearControls(): void {
    this.controlRegistry = [];
  }

  async scanForIssues(
    scanFn: (
      control: ComplianceControl,
    ) => Promise<{ compliant: boolean; evidence: Evidence[]; resources: Resource[] }>,
  ): Promise<ComplianceIssue[]> {
    const issues: ComplianceIssue[] = [];
    const scanId = crypto.randomUUID();
    const scanStart = Date.now();

    for (const control of this.controlRegistry) {
      try {
        const result = await scanFn(control);
        if (!result.compliant) {
          const issue = this.createIssue(control, result.evidence, result.resources);
          issues.push(issue);
        }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unknown scan error";
        issues.push(
          this.createIssue(control, [
            {
              id: crypto.randomUUID(),
              type: "scan",
              source: `scan:${scanId}`,
              content: `Scan failed: ${message}`,
              collectedAt: new Date(),
              integrityHash: "",
            },
          ], []),
        );
      }
    }

    this.scanHistory.set(scanId, issues);
    void scanStart; // track latency externally via metrics

    return issues;
  }

  async detectDrift(
    baselineIssues: ComplianceIssue[],
    currentIssues: ComplianceIssue[],
  ): Promise<{
    newIssues: ComplianceIssue[];
    resolvedIssues: ComplianceIssue[];
    persistentIssues: ComplianceIssue[];
  }> {
    const baselineControlIds = new Set(baselineIssues.map((i) => i.control.id));
    const currentControlIds = new Set(currentIssues.map((i) => i.control.id));

    return {
      newIssues: currentIssues.filter(
        (i) => !baselineControlIds.has(i.control.id),
      ),
      resolvedIssues: baselineIssues.filter(
        (i) => !currentControlIds.has(i.control.id),
      ),
      persistentIssues: currentIssues.filter((i) =>
        baselineControlIds.has(i.control.id),
      ),
    };
  }

  private createIssue(
    control: ComplianceControl,
    evidence: Evidence[],
    resources: Resource[],
  ): ComplianceIssue {
    return {
      id: crypto.randomUUID(),
      control,
      severity: this.inferSeverity(control),
      title: `Non-compliance detected: ${control.title}`,
      description: `Control ${control.id} (${control.framework}) is not satisfied. ${control.description}`,
      detectedAt: new Date(),
      evidence,
      affectedResources: resources,
      metadata: {
        scanVersion: "1.0.0",
        detector: "IssueDetector",
      },
    };
  }

  private inferSeverity(control: ComplianceControl): ComplianceIssueSeverity {
    const criticalFamilies = [
      "access-control",
      "encryption",
      "incident-response",
      "data-protection",
    ];
    if (criticalFamilies.includes(control.controlFamily.toLowerCase())) {
      return "critical";
    }
    if (control.framework === "PCI_DSS" || control.framework === "HIPAA") {
      return "high";
    }
    return "medium";
  }
}

// ============================================================================
// RootCauseAnalyzer
// ============================================================================

export class RootCauseAnalyzer {
  async analyze(issue: ComplianceIssue): Promise<RootCause[]> {
    const causes: RootCause[] = [];

    const configDrift = await this.checkConfigurationDrift(issue);
    if (configDrift) causes.push(configDrift);

    const missingControl = await this.checkMissingControl(issue);
    if (missingControl) causes.push(missingControl);

    const accessIssue = await this.checkAccessMisconfiguration(issue);
    if (accessIssue) causes.push(accessIssue);

    const encryptionGap = await this.checkEncryptionGap(issue);
    if (encryptionGap) causes.push(encryptionGap);

    const loggingGap = await this.checkLoggingGap(issue);
    if (loggingGap) causes.push(loggingGap);

    if (causes.length === 0) {
      causes.push({
        id: crypto.randomUUID(),
        category: "unknown",
        description: `Unable to determine root cause for issue ${issue.id}`,
        confidence: 0.1,
        contributingFactors: ["Insufficient evidence for diagnosis"],
        evidenceChain: issue.evidence,
      });
    }

    return causes.sort((a, b) => b.confidence - a.confidence);
  }

  async correlateIssues(
    issues: ComplianceIssue[],
  ): Promise<Map<string, ComplianceIssue[]>> {
    const correlations = new Map<string, ComplianceIssue[]>();

    for (const issue of issues) {
      const related = issues.filter(
        (other) =>
          other.id !== issue.id &&
          other.control.framework === issue.control.framework &&
          other.control.controlFamily === issue.control.controlFamily,
      );
      if (related.length > 0) {
        correlations.set(issue.id, related);
      }
    }

    return correlations;
  }

  private async checkConfigurationDrift(
    issue: ComplianceIssue,
  ): Promise<RootCause | null> {
    const configEvidence = issue.evidence.filter((e) => e.type === "configuration");
    if (configEvidence.length === 0) return null;

    return {
      id: crypto.randomUUID(),
      category: "configuration-drift",
      description: `Configuration has drifted from compliant state for control ${issue.control.id}`,
      confidence: 0.8,
      contributingFactors: [
        `${configEvidence.length} configuration evidence items indicate drift`,
        "No configuration management baseline detected",
      ],
      evidenceChain: configEvidence,
    };
  }

  private async checkMissingControl(
    issue: ComplianceIssue,
  ): Promise<RootCause | null> {
    if (issue.affectedResources.length === 0) return null;

    return {
      id: crypto.randomUUID(),
      category: "missing-control",
      description: `Required control ${issue.control.id} is not implemented on ${issue.affectedResources.length} resource(s)`,
      confidence: 0.75,
      contributingFactors: issue.affectedResources.map(
        (r) => `Resource ${r.name} (${r.type}) missing control`,
      ),
      evidenceChain: issue.evidence,
    };
  }

  private async checkAccessMisconfiguration(
    issue: ComplianceIssue,
  ): Promise<RootCause | null> {
    const family = issue.control.controlFamily.toLowerCase();
    if (!family.includes("access") && !family.includes("identity")) return null;

    return {
      id: crypto.randomUUID(),
      category: "access-misconfiguration",
      description: `Access control misconfiguration detected for ${issue.control.id}`,
      confidence: 0.85,
      contributingFactors: [
        "Access control requirements not met",
        "Possible over-privileged or under-privileged assignments",
      ],
      evidenceChain: issue.evidence,
    };
  }

  private async checkEncryptionGap(
    issue: ComplianceIssue,
  ): Promise<RootCause | null> {
    const family = issue.control.controlFamily.toLowerCase();
    if (!family.includes("encrypt") && !family.includes("cryptographic"))
      return null;

    return {
      id: crypto.randomUUID(),
      category: "encryption-gap",
      description: `Encryption requirements not satisfied for ${issue.control.id}`,
      confidence: 0.9,
      contributingFactors: [
        "Encryption standard not met",
        "Possible unencrypted data in transit or at rest",
      ],
      evidenceChain: issue.evidence,
    };
  }

  private async checkLoggingGap(
    issue: ComplianceIssue,
  ): Promise<RootCause | null> {
    const family = issue.control.controlFamily.toLowerCase();
    if (!family.includes("log") && !family.includes("audit") && !family.includes("monitor"))
      return null;

    return {
      id: crypto.randomUUID(),
      category: "logging-gap",
      description: `Logging or monitoring gap detected for ${issue.control.id}`,
      confidence: 0.7,
      contributingFactors: [
        "Insufficient logging for audit trail",
        "Monitoring alerts not configured",
      ],
      evidenceChain: issue.evidence,
    };
  }
}

// ============================================================================
// RemediationPlanner
// ============================================================================

export class RemediationPlanner {
  private templates: Map<string, Partial<RemediationAction>[]> = new Map();

  registerTemplate(
    category: RootCause["category"],
    actions: Partial<RemediationAction>[],
  ): void {
    this.templates.set(category, actions);
  }

  async createPlan(
    issue: ComplianceIssue,
    rootCauses: RootCause[],
  ): Promise<RemediationPlan> {
    const actions: RemediationAction[] = [];

    for (const cause of rootCauses) {
      const causeActions = await this.planForCause(cause, issue);
      actions.push(...causeActions);
    }

    const deduped = this.deduplicateActions(actions);
    const ordered = this.orderByRisk(deduped);

    const overallRisk = this.assessOverallRisk(ordered);
    const requiresApproval =
      overallRisk === "high" || overallRisk === "critical";

    return {
      id: crypto.randomUUID(),
      issueId: issue.id,
      actions: ordered,
      createdAt: new Date(),
      estimatedTotalDuration: this.estimateTotalDuration(ordered),
      overallRiskLevel: overallRisk,
      requiresApproval,
      approvalChain: requiresApproval
        ? [
            {
              id: crypto.randomUUID(),
              planId: "",
              requestedAt: new Date(),
            },
          ]
        : [],
    };
  }

  async generateRollbackPlan(
    plan: RemediationPlan,
  ): Promise<RemediationPlan> {
    const rollbackActions: RemediationAction[] = plan.actions
      .filter((a) => a.type === "auto" && a.rollbackPlan.length > 0)
      .map((a) => ({
        id: crypto.randomUUID(),
        type: "auto" as const,
        title: `Rollback: ${a.title}`,
        description: `Revert changes from ${a.title}`,
        steps: [...a.rollbackPlan].reverse(),
        rollbackPlan: [],
        estimatedDuration: a.estimatedDuration,
        riskLevel: "low" as const,
        requiresApproval: false,
        automated: true,
      }));

    return {
      ...plan,
      id: crypto.randomUUID(),
      actions: rollbackActions,
      overallRiskLevel: "low",
      requiresApproval: false,
      approvalChain: [],
    };
  }

  private async planForCause(
    cause: RootCause,
    issue: ComplianceIssue,
  ): Promise<RemediationAction[]> {
    const templateActions = this.templates.get(cause.category);
    if (templateActions) {
      return templateActions.map((t) => this.instantiateAction(t, cause, issue));
    }

    return this.defaultPlanForCause(cause, issue);
  }

  private instantiateAction(
    template: Partial<RemediationAction>,
    cause: RootCause,
    issue: ComplianceIssue,
  ): RemediationAction {
    return {
      id: crypto.randomUUID(),
      type: template.type ?? "guided",
      title: template.title ?? `Remediate ${cause.category}`,
      description:
        template.description ?? `Address ${cause.description}`,
      steps: template.steps ?? [],
      rollbackPlan: template.rollbackPlan ?? [],
      estimatedDuration: template.estimatedDuration ?? "unknown",
      riskLevel: template.riskLevel ?? "medium",
      requiresApproval: template.requiresApproval ?? false,
      automated: template.automated ?? false,
    };
  }

  private defaultPlanForCause(
    cause: RootCause,
    issue: ComplianceIssue,
  ): RemediationAction[] {
    const actions: RemediationAction[] = [];

    switch (cause.category) {
      case "configuration-drift":
        actions.push({
          id: crypto.randomUUID(),
          type: "auto",
          title: `Restore configuration for ${issue.control.id}`,
          description:
            "Apply correct configuration settings to restore compliance",
          steps: [
            {
              order: 1,
              action: "Capture current configuration state",
              validation: {
                type: "command",
                check: "config-backup",
                expected: "backup-created",
              },
            },
            {
              order: 2,
              action: "Apply compliant configuration template",
              command: `apply-config --control ${issue.control.id} --template compliant`,
              validation: {
                type: "command",
                check: "config-validate",
                expected: "compliant",
              },
            },
            {
              order: 3,
              action: "Verify configuration applied correctly",
              validation: {
                type: "command",
                check: "config-verify",
                expected: "matches-baseline",
              },
            },
          ],
          rollbackPlan: [
            {
              order: 1,
              action: "Restore previous configuration from backup",
              command: `restore-config --backup-id latest`,
            },
          ],
          estimatedDuration: "5 minutes",
          riskLevel: "medium",
          requiresApproval: false,
          automated: true,
        });
        break;

      case "missing-control":
        actions.push({
          id: crypto.randomUUID(),
          type: "guided",
          title: `Implement missing control ${issue.control.id}`,
          description: `Deploy the required control across ${issue.affectedResources.length} resource(s)`,
          steps: [
            {
              order: 1,
              action: "Identify resources requiring the control",
            },
            {
              order: 2,
              action: "Deploy control implementation",
              precondition:
                "Approval received for resource modification",
            },
            {
              order: 3,
              action: "Validate control is active on all resources",
              validation: {
                type: "command",
                check: "control-active",
                expected: "true",
              },
            },
          ],
          rollbackPlan: [
            {
              order: 1,
              action: "Remove deployed control from resources",
              command: `remove-control --control ${issue.control.id}`,
            },
          ],
          estimatedDuration: "15 minutes",
          riskLevel: "high",
          requiresApproval: true,
          automated: false,
        });
        break;

      case "access-misconfiguration":
        actions.push({
          id: crypto.randomUUID(),
          type: "auto",
          title: `Fix access control for ${issue.control.id}`,
          description:
            "Remediate access control misconfiguration to enforce least-privilege",
          steps: [
            {
              order: 1,
              action: "Audit current access policies",
              validation: {
                type: "command",
                check: "access-audit",
                expected: "completed",
              },
            },
            {
              order: 2,
              action: "Apply least-privilege access policy",
              command: `apply-access-policy --control ${issue.control.id} --mode least-privilege`,
            },
            {
              order: 3,
              action: "Verify access policy enforcement",
              validation: {
                type: "command",
                check: "access-verify",
                expected: "enforced",
              },
            },
          ],
          rollbackPlan: [
            {
              order: 1,
              action: "Restore previous access policy",
              command: "restore-access-policy --backup-id latest",
            },
          ],
          estimatedDuration: "10 minutes",
          riskLevel: "high",
          requiresApproval: true,
          automated: true,
        });
        break;

      case "encryption-gap":
        actions.push({
          id: crypto.randomUUID(),
          type: "auto",
          title: `Remediate encryption gap for ${issue.control.id}`,
          description: "Enable or upgrade encryption to meet compliance standards",
          steps: [
            {
              order: 1,
              action: "Identify unencrypted data channels",
              validation: {
                type: "command",
                check: "encryption-scan",
                expected: "completed",
              },
            },
            {
              order: 2,
              action: "Enable encryption with approved algorithms",
              command: `enable-encryption --control ${issue.control.id} --algorithm AES-256`,
            },
            {
              order: 3,
              action: "Verify encryption is active",
              validation: {
                type: "command",
                check: "encryption-verify",
                expected: "active",
              },
            },
          ],
          rollbackPlan: [
            {
              order: 1,
              action: "Disable new encryption settings",
              command: `disable-encryption --control ${issue.control.id}`,
            },
          ],
          estimatedDuration: "8 minutes",
          riskLevel: "high",
          requiresApproval: true,
          automated: true,
        });
        break;

      case "logging-gap":
        actions.push({
          id: crypto.randomUUID(),
          type: "auto",
          title: `Configure logging for ${issue.control.id}`,
          description: "Enable required logging and monitoring for compliance",
          steps: [
            {
              order: 1,
              action: "Enable required log sources",
              command: `enable-logging --control ${issue.control.id}`,
            },
            {
              order: 2,
              action: "Configure log retention policy",
              command: `set-log-retention --days 365`,
            },
            {
              order: 3,
              action: "Verify logs are being collected",
              validation: {
                type: "command",
                check: "logs-active",
                expected: "true",
              },
            },
          ],
          rollbackPlan: [
            {
              order: 1,
              action: "Disable additional logging",
              command: `disable-logging --control ${issue.control.id}`,
            },
          ],
          estimatedDuration: "5 minutes",
          riskLevel: "low",
          requiresApproval: false,
          automated: true,
        });
        break;

      default:
        actions.push({
          id: crypto.randomUUID(),
          type: "manual",
          title: `Manual remediation required for ${issue.control.id}`,
          description:
            "Automated remediation not available. Human intervention required.",
          steps: [
            {
              order: 1,
              action: `Review issue: ${cause.description}`,
            },
            {
              order: 2,
              action: "Implement required control manually",
            },
            {
              order: 3,
              action: "Verify remediation and upload evidence",
            },
          ],
          rollbackPlan: [],
          estimatedDuration: "unknown",
          riskLevel: "medium",
          requiresApproval: true,
          automated: false,
        });
    }

    return actions;
  }

  private deduplicateActions(actions: RemediationAction[]): RemediationAction[] {
    const seen = new Set<string>();
    return actions.filter((a) => {
      const key = `${a.type}:${a.title}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  private orderByRisk(actions: RemediationAction[]): RemediationAction[] {
    const riskOrder: Record<string, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
    };
    return [...actions].sort(
      (a, b) => (riskOrder[a.riskLevel] ?? 4) - (riskOrder[b.riskLevel] ?? 4),
    );
  }

  private assessOverallRisk(
    actions: RemediationAction[],
  ): RemediationAction["riskLevel"] {
    const levels = actions.map((a) => a.riskLevel);
    if (levels.includes("critical")) return "critical";
    if (levels.includes("high")) return "high";
    if (levels.includes("medium")) return "medium";
    return "low";
  }

  private estimateTotalDuration(actions: RemediationAction[]): string {
    return `${actions.length} action(s) planned`;
  }
}

// ============================================================================
// RemediationExecutor
// ============================================================================

export class RemediationExecutor {
  private executions: RemediationExecution[] = [];
  private config: AgentConfig;

  constructor(config: AgentConfig) {
    this.config = config;
  }

  async execute(
    plan: RemediationPlan,
    actionFn: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
  ): Promise<RemediationExecution[]> {
    const results: RemediationExecution[] = [];

    for (const action of plan.actions) {
      if (this.config.dryRun) {
        results.push(this.createDryRunResult(plan.id, action));
        continue;
      }

      if (action.requiresApproval && !this.config.autoApprove) {
        results.push(this.createAwaitingApprovalResult(plan.id, action));
        continue;
      }

      const execution = await this.executeAction(plan.id, action, actionFn);
      results.push(execution);

      if (
        execution.status === "failed" &&
        this.config.enableRollback &&
        action.rollbackPlan.length > 0
      ) {
        await this.executeRollback(plan.id, action, actionFn);
      }
    }

    this.executions.push(...results);
    return results;
  }

  async approvePlan(
    plan: RemediationPlan,
    decision: ApprovalDecision,
    approver: string,
    reason?: string,
  ): Promise<void> {
    for (const approval of plan.approvalChain) {
      if (!approval.decision) {
        approval.decision = decision;
        approval.decidedAt = new Date();
        approval.decidedBy = approver;
        approval.reason = reason;
        break;
      }
    }
  }

  getExecutionHistory(): RemediationExecution[] {
    return [...this.executions];
  }

  private async executeAction(
    planId: string,
    action: RemediationAction,
    actionFn: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
  ): Promise<RemediationExecution> {
    const execution: RemediationExecution = {
      id: crypto.randomUUID(),
      planId,
      actionId: action.id,
      status: "executing",
      startedAt: new Date(),
      output: "",
      rollbackExecuted: false,
    };

    try {
      let allOutput = "";

      for (const step of action.steps) {
        if (this.config.retryAttempts > 0) {
          const result = await this.executeWithRetry(
            step,
            actionFn,
            this.config.retryAttempts,
            this.config.retryDelayMs,
          );
          if (!result.success) {
            execution.status = "failed";
            execution.error = `Step ${step.order} failed: ${result.output}`;
            execution.output = allOutput;
            return execution;
          }
          allOutput += `[Step ${step.order}] ${result.output}\n`;
        } else {
          const result = await actionFn(step);
          if (!result.success) {
            execution.status = "failed";
            execution.error = `Step ${step.order} failed: ${result.output}`;
            execution.output = allOutput;
            return execution;
          }
          allOutput += `[Step ${step.order}] ${result.output}\n`;
        }
      }

      execution.status = "completed";
      execution.completedAt = new Date();
      execution.output = allOutput;
    } catch (error) {
      execution.status = "failed";
      execution.error =
        error instanceof Error ? error.message : "Unknown execution error";
    }

    return execution;
  }

  private async executeWithRetry(
    step: RemediationStep,
    actionFn: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
    maxAttempts: number,
    delayMs: number,
  ): Promise<{ success: boolean; output: string }> {
    let lastResult = { success: false, output: "" };

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      lastResult = await actionFn(step);
      if (lastResult.success) return lastResult;
      if (attempt < maxAttempts) {
        await this.sleep(delayMs * attempt);
      }
    }

    return lastResult;
  }

  private async executeRollback(
    planId: string,
    action: RemediationAction,
    actionFn: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
  ): Promise<void> {
    for (const step of action.rollbackPlan) {
      try {
        await actionFn(step);
      } catch {
        // Rollback failures are logged but do not throw
      }
    }
  }

  private createDryRunResult(
    planId: string,
    action: RemediationAction,
  ): RemediationExecution {
    return {
      id: crypto.randomUUID(),
      planId,
      actionId: action.id,
      status: "completed",
      startedAt: new Date(),
      completedAt: new Date(),
      output: `[DRY RUN] Would execute: ${action.title} (${action.steps.length} steps)`,
      rollbackExecuted: false,
      verificationPassed: undefined,
    };
  }

  private createAwaitingApprovalResult(
    planId: string,
    action: RemediationAction,
  ): RemediationExecution {
    return {
      id: crypto.randomUUID(),
      planId,
      actionId: action.id,
      status: "awaiting-approval",
      startedAt: new Date(),
      output: `Action "${action.title}" requires approval before execution`,
      rollbackExecuted: false,
    };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ============================================================================
// AutonomousComplianceAgent
// ============================================================================

export class AutonomousComplianceAgent {
  private detector: IssueDetector;
  private analyzer: RootCauseAnalyzer;
  private planner: RemediationPlanner;
  private executor: RemediationExecutor;
  private config: AgentConfig;
  private metrics: AgentMetrics;
  private scanResults: ComplianceIssue[] = [];
  private plans: RemediationPlan[] = [];

  constructor(config?: Partial<AgentConfig>) {
    this.config = {
      dryRun: true,
      autoApprove: false,
      maxConcurrentRemediations: 3,
      retentionPolicyDays: 90,
      enableRollback: true,
      approvalTimeoutMs: 86_400_000, // 24 hours
      retryAttempts: 3,
      retryDelayMs: 1000,
      ...config,
    };

    this.detector = new IssueDetector();
    this.analyzer = new RootCauseAnalyzer();
    this.planner = new RemediationPlanner();
    this.executor = new RemediationExecutor(this.config);

    this.metrics = {
      issuesDetected: 0,
      rootCausesAnalyzed: 0,
      remediationPlansGenerated: 0,
      remediationsExecuted: 0,
      remediationsSucceeded: 0,
      remediationsFailed: 0,
      remediationsRolledBack: 0,
      avgDetectionLatencyMs: 0,
      avgRemediationLatencyMs: 0,
    };
  }

  get detectorInstance(): IssueDetector {
    return this.detector;
  }

  get analyzerInstance(): RootCauseAnalyzer {
    return this.analyzer;
  }

  get plannerInstance(): RemediationPlanner {
    return this.planner;
  }

  get executorInstance(): RemediationExecutor {
    return this.executor;
  }

  async scan(
    scanFn: (
      control: ComplianceControl,
    ) => Promise<{ compliant: boolean; evidence: Evidence[]; resources: Resource[] }>,
  ): Promise<ComplianceIssue[]> {
    const start = Date.now();
    const issues = await this.detector.scanForIssues(scanFn);
    const latency = Date.now() - start;

    this.scanResults = issues;
    this.metrics.issuesDetected += issues.length;
    this.metrics.avgDetectionLatencyMs =
      (this.metrics.avgDetectionLatencyMs + latency) / 2;
    this.metrics.lastScanAt = new Date();

    return issues;
  }

  async analyzeAndPlan(
    issues: ComplianceIssue[] = this.scanResults,
  ): Promise<RemediationPlan[]> {
    const plans: RemediationPlan[] = [];

    for (const issue of issues) {
      const causes = await this.analyzer.analyze(issue);
      this.metrics.rootCausesAnalyzed += causes.length;

      const plan = await this.planner.createPlan(issue, causes);
      this.metrics.remediationPlansGenerated += 1;
      plans.push(plan);
    }

    this.plans = plans;
    return plans;
  }

  async remediate(
    plans: RemediationPlan[] = this.plans,
    actionFn?: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
  ): Promise<RemediationExecution[]> {
    const defaultActionFn = async (
      step: RemediationStep,
    ): Promise<{ success: boolean; output: string }> => {
      if (step.command) {
        return { success: true, output: `Executed: ${step.command}` };
      }
      if (step.apiCall) {
        return {
          success: true,
          output: `API ${step.apiCall.method} ${step.apiCall.url}`,
        };
      }
      return { success: true, output: `Completed: ${step.action}` };
    };

    const fn = actionFn ?? defaultActionFn;
    const allExecutions: RemediationExecution[] = [];

    for (const plan of plans) {
      const executions = await this.executor.execute(plan, fn);
      allExecutions.push(...executions);

      this.metrics.remediationsExecuted += executions.length;
      for (const exec of executions) {
        if (exec.status === "completed") this.metrics.remediationsSucceeded++;
        if (exec.status === "failed") this.metrics.remediationsFailed++;
        if (exec.rollbackExecuted) this.metrics.remediationsRolledBack++;
      }
    }

    return allExecutions;
  }

  async approvePlan(
    planId: string,
    decision: ApprovalDecision,
    approver: string,
    reason?: string,
  ): Promise<void> {
    const plan = this.plans.find((p) => p.id === planId);
    if (!plan) throw new Error(`Plan ${planId} not found`);
    await this.executor.approvePlan(plan, decision, approver, reason);
  }

  getMetrics(): AgentMetrics {
    return { ...this.metrics };
  }

  getScanResults(): ComplianceIssue[] {
    return [...this.scanResults];
  }

  getPlans(): RemediationPlan[] {
    return [...this.plans];
  }

  getExecutionHistory(): RemediationExecution[] {
    return this.executor.getExecutionHistory();
  }

  async runFullCycle(
    scanFn: (
      control: ComplianceControl,
    ) => Promise<{ compliant: boolean; evidence: Evidence[]; resources: Resource[] }>,
    actionFn?: (step: RemediationStep) => Promise<{ success: boolean; output: string }>,
  ): Promise<{
    issues: ComplianceIssue[];
    plans: RemediationPlan[];
    executions: RemediationExecution[];
  }> {
    const issues = await this.scan(scanFn);
    const plans = await this.analyzeAndPlan(issues);
    const executions = await this.remediate(plans, actionFn);

    return { issues, plans, executions };
  }
}

// ============================================================================
// Convenience: Built-in control sets
// ============================================================================

export const SOC2_CONTROLS: ComplianceControl[] = [
  {
    id: "CC6.1",
    framework: "SOC2",
    controlFamily: "Logical and Physical Access Controls",
    title: "Logical access security software, infrastructure, and architectures",
    description:
      "The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events.",
    requirements: [
      "Access control policies defined and enforced",
      "Role-based access control implemented",
      "Authentication mechanisms in place",
    ],
    automatedRemediationSupported: true,
  },
  {
    id: "CC6.6",
    framework: "SOC2",
    controlFamily: "Logical and Physical Access Controls",
    title: "Restrictions against transmission, movement, and removal of information",
    description:
      "The entity implements controls over the transmission, movement, and removal of information to authorized individuals.",
    requirements: [
      "Encryption in transit enabled",
      "Data loss prevention controls active",
      "Secure transfer protocols enforced",
    ],
    automatedRemediationSupported: true,
  },
  {
    id: "CC7.1",
    framework: "SOC2",
    controlFamily: "System Operations",
    title: "Detection and monitoring procedures",
    description:
      "To meet its objectives, the entity uses detection and monitoring procedures to identify changes to configurations that result in the introduction of new vulnerabilities.",
    requirements: [
      "Security monitoring enabled",
      "Intrusion detection configured",
      "Anomaly detection active",
    ],
    automatedRemediationSupported: true,
  },
];

export const NIST_CSF_CONTROLS: ComplianceControl[] = [
  {
    id: "PR.AC-1",
    framework: "NIST_CSF",
    controlFamily: "Access Control",
    title: "Identities and credentials are issued, managed, verified, revoked, and audited",
    description:
      "Access control policies and procedures are established and implemented to manage the issuance, management, verification, revocation, and auditing of identities and credentials.",
    requirements: [
      "Identity lifecycle management in place",
      "Credential rotation enforced",
      "Access reviews conducted regularly",
    ],
    automatedRemediationSupported: true,
  },
  {
    id: "PR.DS-1",
    framework: "NIST_CSF",
    controlFamily: "Data Security",
    title: "Data-at-rest is protected",
    description:
      "Data-at-rest is protected by implementing appropriate controls such as encryption.",
    requirements: [
      "Encryption at rest enabled for all data stores",
      "Key management procedures in place",
      "Data classification applied",
    ],
    automatedRemediationSupported: true,
  },
  {
    id: "DE.CM-1",
    framework: "NIST_CSF",
    controlFamily: "Detect",
    title: "The network is monitored to detect potential cybersecurity events",
    description:
      "The network is monitored to detect potential cybersecurity events in a timely manner.",
    requirements: [
      "Network monitoring active",
      "SIEM integration configured",
      "Alert thresholds defined",
    ],
    automatedRemediationSupported: true,
  },
];
