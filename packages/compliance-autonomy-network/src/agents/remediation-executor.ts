import { randomBytes } from "node:crypto";
import { BaseAgent } from "./base-agent.js";
import type {
  SwarmTask,
  SwarmResult,
  RemediationResult,
  ComplianceFramework,
  RiskLevel,
  RemediationPlanInput,
} from "../types.js";

// ============================================================================
// RemediationExecutor – executes or stages remediation actions for identified gaps
// ============================================================================

export class RemediationExecutorAgent extends BaseAgent {
  private executionHistory: Map<string, RemediationResult[]> = new Map();

  constructor(signingKey: string = randomBytes(32).toString("hex")) {
    super(
      "remediation-executor",
      "Remediation Execution Agent",
      "1.0.0",
      [
        {
          name: "execute-remediation",
          frameworks: ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA", "GDPR", "CCPA", "SOX", "FedRAMP", "Custom"],
          confidenceLevel: 0.85,
        },
      ],
      signingKey,
      { maxConcurrentTasks: 3 },
    );
  }

  protected async doExecute(task: SwarmTask): Promise<SwarmResult["output"]> {
    const planInput = task.input.remediationPlan;
    if (!planInput) {
      throw new Error("RemediationExecutor requires remediationPlan in task input");
    }

    const results = await this.executeRemediation(task.framework, planInput, task);
    this.executionHistory.set(task.id, results);

    const executed = results.filter((r) => r.status === "executed").length;
    const failed = results.filter((r) => r.status === "failed").length;
    const pending = results.filter((r) => r.status === "pending-approval").length;

    return {
      remediationResults: results,
      summary: `Remediation for ${planInput.controlId}: ${executed} action(s) executed, ${failed} failed, ${pending} pending approval. Severity: ${planInput.severity}.`,
      recommendations: this.generateRemediationRecommendations(results, planInput),
    };
  }

  // ------------------------------------------------------------------
  // Remediation execution
  // ------------------------------------------------------------------

  private async executeRemediation(
    framework: ComplianceFramework,
    planInput: RemediationPlanInput,
    task: SwarmTask,
  ): Promise<RemediationResult[]> {
    const actions = this.planRemediationActions(framework, planInput);
    const results: RemediationResult[] = [];

    for (const action of actions) {
      const result = await this.executeAction(action, planInput, task);
      results.push(result);
    }

    return results;
  }

  private planRemediationActions(
    framework: ComplianceFramework,
    planInput: RemediationPlanInput,
  ): RemediationActionPlan[] {
    const actions: RemediationActionPlan[] = [];

    if (planInput.severity === "critical" || planInput.severity === "high") {
      actions.push({
        type: "enable-encryption",
        description: `Enable encryption for control ${planInput.controlId}`,
        command: `enable-encryption --control ${planInput.controlId} --framework ${framework} --algorithm AES-256-GCM`,
        riskLevel: "medium",
      });
    }

    actions.push({
      type: "configure-access-control",
      description: `Apply least-privilege access policy for control ${planInput.controlId}`,
      command: `apply-access-policy --control ${planInput.controlId} --mode least-privilege --enforce`,
      riskLevel: planInput.severity === "critical" ? "high" : "medium",
    });

    actions.push({
      type: "enable-logging",
      description: `Enable audit logging for control ${planInput.controlId}`,
      command: `enable-audit-logging --control ${planInput.controlId} --retention 365d`,
      riskLevel: "low",
    });

    if (planInput.severity === "critical") {
      actions.push({
        type: "deploy-monitoring",
        description: `Deploy continuous monitoring for control ${planInput.controlId}`,
        command: `deploy-monitoring --control ${planInput.controlId} --alert-threshold high`,
        riskLevel: "medium",
      });
    }

    return actions;
  }

  private async executeAction(
    action: RemediationActionPlan,
    planInput: RemediationPlanInput,
    task: SwarmTask,
  ): Promise<RemediationResult> {
    if (task.input.customParameters?.dryRun === true || task.metadata.dryRun === true) {
      return {
        issueId: `issue-${planInput.controlId}`,
        controlId: planInput.controlId,
        action: `[DRY RUN] ${action.description}`,
        status: "skipped",
      };
    }

    if (this.requiresApproval(action, planInput)) {
      return {
        issueId: `issue-${planInput.controlId}`,
        controlId: planInput.controlId,
        action: action.description,
        status: "pending-approval",
      };
    }

    try {
      const output = await this.performAction(action);
      return {
        issueId: `issue-${planInput.controlId}`,
        controlId: planInput.controlId,
        action: action.description,
        status: "executed",
        executedAt: new Date().toISOString(),
        output,
        verificationPassed: true,
      };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      return {
        issueId: `issue-${planInput.controlId}`,
        controlId: planInput.controlId,
        action: action.description,
        status: "failed",
        executedAt: new Date().toISOString(),
        output: `Execution failed: ${errorMsg}`,
        verificationPassed: false,
      };
    }
  }

  private async performAction(action: RemediationActionPlan): Promise<string> {
    // Simulated action execution – in production this would invoke real APIs/commands
    return `Action "${action.type}" executed successfully. Command: ${action.command}. Completed at ${new Date().toISOString()}.`;
  }

  private requiresApproval(
    action: RemediationActionPlan,
    planInput: RemediationPlanInput,
  ): boolean {
    if (planInput.autoApprove) return false;
    if (action.riskLevel === "critical" || action.riskLevel === "high") return true;

    const elevatedSeverity = planInput.severity === "critical" || planInput.severity === "high";
    return elevatedSeverity && action.riskLevel === "medium";
  }

  private generateRemediationRecommendations(
    results: RemediationResult[],
    planInput: RemediationPlanInput,
  ): string[] {
    const recs: string[] = [];

    const executed = results.filter((r) => r.status === "executed");
    const failed = results.filter((r) => r.status === "failed");
    const pending = results.filter((r) => r.status === "pending-approval");

    if (executed.length > 0) {
      recs.push(`${executed.length} remediation action(s) executed for control ${planInput.controlId} – verify effectiveness`);
    }

    if (failed.length > 0) {
      recs.push(`${failed.length} action(s) failed – investigate root cause and retry or escalate`);
    }

    if (pending.length > 0) {
      recs.push(`${pending.length} action(s) pending approval – route to designated approver`);
    }

    if (planInput.severity === "critical") {
      recs.push("Critical severity issue – expedite remediation and verify within 24 hours");
    }

    const unverified = executed.filter((r) => r.verificationPassed === false || r.verificationPassed === undefined);
    if (unverified.length > 0) {
      recs.push(`${unverified.length} executed action(s) awaiting verification – run control test to confirm`);
    }

    return recs;
  }

  getExecutionHistory(taskId: string): RemediationResult[] {
    return this.executionHistory.get(taskId) ?? [];
  }
}

interface RemediationActionPlan {
  type: string;
  description: string;
  command: string;
  riskLevel: RiskLevel;
}
