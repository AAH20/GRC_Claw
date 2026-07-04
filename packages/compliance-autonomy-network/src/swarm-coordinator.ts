import { randomBytes, createHash } from "node:crypto";
import type {
  SwarmTask,
  SwarmResult,
  SwarmAgent,
  AgentRole,
  AgentMessage,
  ComplianceGoal,
  GoalDecomposition,
  ExecutionPlan,
  ExecutionPhase,
  ComplianceReport,
  ComplianceFramework,
  TaskPriority,
  TrustChainLink,
  EvidenceItem,
  ControlStatus,
  EvidenceSummary,
  RemediationSummary,
  CrossFrameworkMapping,
  SwarmCoordinatorConfig,
  TaskType,
  AuditPackage,
  RiskAssessment,
} from "./types.js";

import { EvidenceCollector } from "./agents/evidence-collector.js";
import { ControlTester } from "./agents/control-tester.js";
import { RiskQuantifier } from "./agents/risk-quantifier.js";
import { AuditPreparer } from "./agents/audit-preparer.js";
import { RemediationExecutorAgent } from "./agents/remediation-executor.js";
import { Verifier } from "./agents/verifier.js";

// ============================================================================
// Default configuration
// ============================================================================

const DEFAULT_CONFIG: SwarmCoordinatorConfig = {
  maxConcurrentTasks: 6,
  taskTimeoutMs: 120_000,
  enablePolicyFirewall: true,
  enableTrustChain: true,
  logToTrustNetwork: true,
  retryAttempts: 2,
  retryDelayMs: 1_000,
  dryRun: false,
};

// ============================================================================
// SwarmCoordinator – the commander of the CAN swarm
// ============================================================================

export class SwarmCoordinator {
  private readonly agents: Map<AgentRole, SwarmAgent> = new Map();
  private readonly messages: AgentMessage[] = [];
  private readonly trustChain: TrustChainLink[] = [];
  private readonly taskResults: Map<string, SwarmResult[]> = new Map();
  private readonly config: SwarmCoordinatorConfig;

  private previousLinkHash = "0".repeat(64);

  constructor(config: Partial<SwarmCoordinatorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.registerDefaultAgents();
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  /**
   * Execute a high-level compliance goal by decomposing it into agent tasks,
   * running them in parallel where possible, and producing a final report.
   */
  async executeGoal(goal: ComplianceGoal): Promise<ComplianceReport> {
    const decomposition = this.decomposeGoal(goal);

    this.broadcastMessage({
      kind: "task-delegation",
      task: decomposition.tasks[0],
    } as AgentMessage["payload"], decomposition.tasks[0]);

    const allResults = await this.executeTasks(decomposition);

    const report = await this.assembleReport(goal, decomposition, allResults);

    if (this.config.enableTrustChain) {
      this.appendTrustLink("coordinator", "goal-completed", goal.id, report.integrityHash);
    }

    return report;
  }

  /**
   * Execute a single task directly through the appropriate agent.
   */
  async executeTask(task: SwarmResult["taskId"] extends string ? SwarmTask : never): Promise<SwarmResult> {
    const swarmTask = task as SwarmTask;
    const agent = this.selectAgent(swarmTask);
    if (!agent) {
      throw new Error(`No available agent for task ${swarmTask.id} (role: ${swarmTask.assignedAgent ?? "any"})`);
    }

    const result = await this.executeWithRetry(swarmTask, agent);
    this.appendTrustLink(agent.role, swarmTask.type, swarmTask.id, result.trustSignature.contentHash);

    return result;
  }

  /**
   * Register a custom agent with the coordinator.
   */
  registerAgent(agent: SwarmAgent): void {
    this.agents.set(agent.role, agent);
  }

  /**
   * Get all registered agents.
   */
  getAgents(): SwarmAgent[] {
    return Array.from(this.agents.values());
  }

  /**
   * Get message log.
   */
  getMessages(): AgentMessage[] {
    return [...this.messages];
  }

  /**
   * Get trust chain audit log.
   */
  getTrustChain(): TrustChainLink[] {
    return [...this.trustChain];
  }

  /**
   * Get results for a specific task.
   */
  getTaskResults(taskId: string): SwarmResult[] {
    return this.taskResults.get(taskId) ?? [];
  }

  // ------------------------------------------------------------------
  // Goal decomposition
  // ------------------------------------------------------------------

  private decomposeGoal(goal: ComplianceGoal): GoalDecomposition {
    const tasks: SwarmTask[] = [];
    const taskId = () => `task-${randomBytes(8).toString("hex")}`;

    // Phase 1: Evidence collection (parallel per framework)
    const evidenceTaskIds: string[] = [];
    for (const framework of goal.targetFrameworks) {
      const id = taskId();
      evidenceTaskIds.push(id);
      tasks.push({
        id,
        goalId: goal.id,
        type: "evidence-collection",
        framework,
        priority: goal.priority,
        description: `Collect compliance evidence for ${framework}`,
        input: {
          evidenceCriteria: {
            framework,
            controlFamilies: this.getControlFamiliesForFramework(framework),
            evidenceTypes: ["configuration", "log", "policy", "scan", "metric"],
            sources: goal.scope.length > 0 ? goal.scope : ["system"],
          },
        },
        assignedAgent: "evidence-collector",
        dependencies: [],
        timeoutMs: this.config.taskTimeoutMs,
        createdAt: new Date().toISOString(),
        metadata: { phase: 1, dryRun: this.config.dryRun },
      });
    }

    // Phase 2: Control testing (depends on evidence, parallel per framework)
    const controlTestTaskIds: string[] = [];
    for (const framework of goal.targetFrameworks) {
      const id = taskId();
      controlTestTaskIds.push(id);
      tasks.push({
        id,
        goalId: goal.id,
        type: "control-testing",
        framework,
        priority: goal.priority,
        description: `Test compliance controls for ${framework}`,
        input: {
          controlIds: this.getControlIdsForFramework(framework),
        },
        assignedAgent: "control-tester",
        dependencies: evidenceTaskIds.filter((eid) => {
          const t = tasks.find((tt) => tt.id === eid);
          return t?.framework === framework;
        }),
        timeoutMs: this.config.taskTimeoutMs,
        createdAt: new Date().toISOString(),
        metadata: { phase: 2, dryRun: this.config.dryRun },
      });
    }

    // Phase 3: Risk quantification (depends on control testing)
    const riskTaskId = taskId();
    tasks.push({
      id: riskTaskId,
      goalId: goal.id,
      type: "risk-quantification",
      framework: goal.targetFrameworks[0] ?? "SOC2",
      priority: goal.priority,
      description: "Quantify compliance risk across all frameworks",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap", "regulatory"],
          businessImpact: goal.priority === "critical" ? "critical" : "high",
          regulatoryRisk: true,
        },
      },
      assignedAgent: "risk-quantifier",
      dependencies: controlTestTaskIds,
      timeoutMs: this.config.taskTimeoutMs,
      createdAt: new Date().toISOString(),
      metadata: { phase: 3, dryRun: this.config.dryRun },
    });

    // Phase 4: Audit preparation (depends on risk quantification)
    const auditTaskId = taskId();
    tasks.push({
      id: auditTaskId,
      goalId: goal.id,
      type: "audit-preparation",
      framework: goal.targetFrameworks[0] ?? "SOC2",
      priority: goal.priority,
      description: "Prepare audit-ready compliance package",
      input: {
        auditWindow: {
          startDate: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
          endDate: new Date().toISOString(),
          frameworks: goal.targetFrameworks,
          includeHistoricalEvidence: true,
        },
      },
      assignedAgent: "audit-preparer",
      dependencies: [riskTaskId],
      timeoutMs: this.config.taskTimeoutMs,
      createdAt: new Date().toISOString(),
      metadata: { phase: 4, dryRun: this.config.dryRun },
    });

    // Phase 5: Verification (depends on audit preparation)
    const verifyTaskId = taskId();
    tasks.push({
      id: verifyTaskId,
      goalId: goal.id,
      type: "verification",
      framework: goal.targetFrameworks[0] ?? "SOC2",
      priority: goal.priority,
      description: "Verify control effectiveness and evidence integrity",
      input: {
        controlIds: this.getControlIdsForFramework(goal.targetFrameworks[0] ?? "SOC2"),
      },
      assignedAgent: "verifier",
      dependencies: [auditTaskId],
      timeoutMs: this.config.taskTimeoutMs,
      createdAt: new Date().toISOString(),
      metadata: { phase: 5, dryRun: this.config.dryRun },
    });

    const phases: ExecutionPhase[] = [
      { id: "p1", name: "Evidence Collection", taskIds: evidenceTaskIds, dependsOn: [], parallel: true, estimatedMs: 15_000 },
      { id: "p2", name: "Control Testing", taskIds: controlTestTaskIds, dependsOn: ["p1"], parallel: true, estimatedMs: 20_000 },
      { id: "p3", name: "Risk Quantification", taskIds: [riskTaskId], dependsOn: ["p2"], parallel: false, estimatedMs: 10_000 },
      { id: "p4", name: "Audit Preparation", taskIds: [auditTaskId], dependsOn: ["p3"], parallel: false, estimatedMs: 15_000 },
      { id: "p5", name: "Verification", taskIds: [verifyTaskId], dependsOn: ["p4"], parallel: false, estimatedMs: 10_000 },
    ];

    return {
      goalId: goal.id,
      tasks,
      executionPlan: {
        phases,
        totalEstimatedMs: phases.reduce((sum, p) => sum + p.estimatedMs, 0),
        criticalPath: phases.map((p) => p.id),
      },
      estimatedDurationMs: phases.reduce((sum, p) => sum + p.estimatedMs, 0),
      requiredAgents: ["evidence-collector", "control-tester", "risk-quantifier", "audit-preparer", "verifier"],
      parallelizableGroups: [evidenceTaskIds, controlTestTaskIds],
    };
  }

  // ------------------------------------------------------------------
  // Task execution
  // ------------------------------------------------------------------

  private async executeTasks(decomposition: GoalDecomposition): Promise<Map<string, SwarmResult>> {
    const results = new Map<string, SwarmResult>();
    const completed = new Set<string>();

    for (const phase of decomposition.executionPlan.phases) {
      const phaseTasks = decomposition.tasks.filter(
        (t) => phase.taskIds.includes(t.id) && !completed.has(t.id),
      );

      // Verify dependencies are met
      for (const task of phaseTasks) {
        const depsMet = task.dependencies.every((dep) => completed.has(dep));
        if (!depsMet) {
          const missing = task.dependencies.filter((dep) => !completed.has(dep));
          throw new Error(`Task ${task.id} dependencies not met: ${missing.join(", ")}`);
        }
      }

      // Execute tasks in parallel within phase
      const taskPromises = phaseTasks.map(async (task) => {
        const agent = this.selectAgent(task);
        if (!agent) {
          results.set(task.id, {
            taskId: task.id,
            agentId: "none",
            agentRole: task.assignedAgent ?? "evidence-collector",
            status: "failed",
            output: { summary: `No available agent for role ${task.assignedAgent}`, recommendations: [] },
            trustSignature: {
              agentId: "coordinator",
              agentRole: "evidence-collector",
              timestamp: new Date().toISOString(),
              contentHash: "",
              previousHash: this.previousLinkHash,
              nonce: 0,
              signature: "",
            },
            executionTimeMs: 0,
            startedAt: new Date().toISOString(),
            completedAt: new Date().toISOString(),
            error: `No available agent for role ${task.assignedAgent}`,
          });
          return;
        }

        this.broadcastMessage(
          { kind: "task-delegation", task } as AgentMessage["payload"],
          task,
        );

        const result = await this.executeWithRetry(task, agent);
        results.set(task.id, result);

        this.broadcastMessage(
          { kind: "task-completed", result } as AgentMessage["payload"],
          task,
        );

        this.appendTrustLink(agent.role, task.type, task.id, result.trustSignature.contentHash);
      });

      await Promise.all(taskPromises);

      phaseTasks.forEach((t) => completed.add(t.id));
    }

    return results;
  }

  private async executeWithRetry(task: SwarmTask, agent: SwarmAgent): Promise<SwarmResult> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retryAttempts; attempt++) {
      try {
        return await agent.execute(task);
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        if (attempt < this.config.retryAttempts) {
          await this.sleep(this.config.retryDelayMs * (attempt + 1));
        }
      }
    }

    throw lastError ?? new Error("Execution failed after retries");
  }

  private selectAgent(task: SwarmTask): SwarmAgent | null {
    if (task.assignedAgent) {
      const agent = this.agents.get(task.assignedAgent);
      if (agent && agent.canHandle(task)) return agent;
    }

    for (const agent of this.agents.values()) {
      if (agent.canHandle(task)) return agent;
    }

    return null;
  }

  // ------------------------------------------------------------------
  // Report assembly
  // ------------------------------------------------------------------

  private async assembleReport(
    goal: ComplianceGoal,
    decomposition: GoalDecomposition,
    results: Map<string, SwarmResult>,
  ): Promise<ComplianceReport> {
    const allResults = Array.from(results.values());
    const completedResults = allResults.filter((r) => r.status === "completed");

    // Aggregate evidence
    const allEvidence = completedResults.flatMap((r) => r.output.evidence ?? []);

    // Aggregate control statuses
    const allControlStatuses = completedResults.flatMap((r) => r.output.controlStatuses ?? []);

    // Get risk assessment from results
    const riskResult = completedResults.find((r) => r.output.riskAssessment);
    const riskAssessment = riskResult?.output.riskAssessment ?? this.createDefaultRiskAssessment(goal.targetFrameworks[0] ?? "SOC2");

    // Get audit package
    const auditResult = completedResults.find((r) => r.output.auditPackage);
    const auditPackage = auditResult?.output.auditPackage;

    // Cross-framework mappings
    const crossFrameworkMappings = this.generateCrossFrameworkMappings(goal.targetFrameworks, allControlStatuses);

    // Calculate compliance score
    const overallComplianceScore = allControlStatuses.length > 0
      ? allControlStatuses.filter((s) => s.status === "compliant").length / allControlStatuses.length
      : 0;

    // Aggregate remediation results
    const allRemediations = completedResults.flatMap((r) => r.output.remediationResults ?? []);
    const remediationsSummary = this.summarizeRemediations(allRemediations);

    // Aggregate verification results
    const allVerifications = completedResults.flatMap((r) => r.output.verificationResults ?? []);

    // Evidence summary
    const evidenceSummary = this.summarizeEvidence(allEvidence, goal.targetFrameworks);

    // Collect recommendations
    const recommendations = [...new Set(completedResults.flatMap((r) => r.output.recommendations))];

    // Next steps
    const nextSteps = this.generateNextSteps(overallComplianceScore, allControlStatuses, auditPackage);

    // Integrity hash
    const reportContent = JSON.stringify({
      goalId: goal.id,
      score: overallComplianceScore,
      controlCount: allControlStatuses.length,
      evidenceCount: allEvidence.length,
      riskLevel: riskAssessment.riskLevel,
    });
    const integrityHash = createHash("sha256").update(reportContent).digest("hex");

    return {
      id: `report-${randomBytes(8).toString("hex")}`,
      goalId: goal.id,
      goal,
      generatedAt: new Date().toISOString(),
      frameworks: goal.targetFrameworks,
      overallComplianceScore,
      riskAssessment,
      controlStatuses: allControlStatuses,
      evidenceSummary,
      auditPackage,
      remediationsSummary,
      crossFrameworkMappings,
      agentActivityLog: [...this.trustChain],
      recommendations,
      nextSteps,
      integrityHash,
    };
  }

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------

  private createDefaultRiskAssessment(framework: ComplianceFramework): RiskAssessment {
    return {
      overallScore: 5.0,
      riskLevel: "medium",
      frameworkBreakdown: [
        {
          framework,
          score: 5.0,
          riskLevel: "medium",
          controlsCompliant: 0,
          controlsNonCompliant: 0,
          controlsPartial: 0,
          controlsTotal: 0,
        },
      ],
      topRisks: [],
      mitigatedRisks: [],
      residualRiskScore: 5.0,
      calculatedAt: new Date().toISOString(),
    };
  }

  private generateCrossFrameworkMappings(
    frameworks: ComplianceFramework[],
    controlStatuses: ControlStatus[],
  ): CrossFrameworkMapping[] {
    const mappings: CrossFrameworkMapping[] = [];

    if (frameworks.length < 2) return mappings;

    const mappingRules: Record<string, { target: ComplianceFramework; targetId: string; score: number }>[] = [
      [{ target: "ISO27001", targetId: "A8.1", score: 0.95 }, { target: "NIST_CSF", targetId: "PR.AC-1", score: 0.88 }],
      [{ target: "SOC2", targetId: "CC6.1", score: 0.92 }, { target: "ISO27001", targetId: "A9.4", score: 0.90 }],
      [{ target: "SOC2", targetId: "CC7.1", score: 0.85 }, { target: "NIST_CSF", targetId: "DE.CM-1", score: 0.82 }],
    ];

    for (const rule of mappingRules) {
      for (const mapping of rule) {
        if (frameworks.includes("SOC2") && frameworks.includes(mapping.target)) {
          mappings.push({
            sourceControlId: rule[0].targetId,
            sourceFramework: "SOC2",
            targetControlId: mapping.targetId,
            targetFramework: mapping.target,
            equivalenceScore: mapping.score,
            mappingType: mapping.score >= 0.9 ? "direct" : "partial",
          });
        }
      }
    }

    return mappings;
  }

  private summarizeEvidence(
    evidence: EvidenceItem[],
    frameworks: ComplianceFramework[],
  ): EvidenceSummary {
    const byFramework: Partial<Record<ComplianceFramework, number>> = {};
    const byKind: Partial<Record<string, number>> = {};

    for (const item of evidence) {
      byFramework[item.framework] = (byFramework[item.framework] ?? 0) + 1;
      byKind[item.kind] = (byKind[item.kind] ?? 0) + 1;
    }

    const allIntegrityValid = evidence.every((e) => {
      const computedHash = createHash("sha256").update(e.content).digest("hex");
      return computedHash === e.contentHash;
    });

    return {
      totalItems: evidence.length,
      byFramework: byFramework as Record<ComplianceFramework, number>,
      byKind: byKind as Record<string, number>,
      integrityVerified: allIntegrityValid,
    };
  }

  private summarizeRemediations(
    remediations: SwarmResult["output"]["remediationResults"],
  ): RemediationSummary {
    const items = remediations ?? [];
    return {
      totalIssues: items.length,
      remediated: items.filter((r) => r.status === "executed").length,
      pending: items.filter((r) => r.status === "pending-approval").length,
      failed: items.filter((r) => r.status === "failed").length,
      autoRemediated: items.filter((r) => r.status === "executed").length,
      manualRequired: items.filter((r) => r.status === "pending-approval").length,
    };
  }

  private generateNextSteps(
    complianceScore: number,
    controlStatuses: ControlStatus[],
    auditPackage?: AuditPackage,
  ): string[] {
    const steps: string[] = [];

    if (complianceScore >= 0.95) {
      steps.push("Schedule external audit engagement – compliance posture is strong");
      steps.push("Implement continuous monitoring to maintain compliance levels");
    } else if (complianceScore >= 0.8) {
      steps.push("Close remaining compliance gaps before audit engagement");
      steps.push("Conduct internal pre-audit review of non-compliant controls");
    } else {
      steps.push("Develop comprehensive remediation roadmap for non-compliant controls");
      steps.push("Engage executive sponsorship for compliance resource allocation");
      steps.push("Prioritize critical-risk controls for immediate remediation");
    }

    const nonCompliant = controlStatuses.filter((s) => s.status === "non-compliant");
    if (nonCompliant.length > 0) {
      steps.push(`Remediate ${nonCompliant.length} non-compliant control(s): ${nonCompliant.map((s) => s.controlId).join(", ")}`);
    }

    if (auditPackage?.readinessLevel === "not-ready") {
      steps.push("Audit readiness: NOT READY – full remediation program required before audit");
    }

    steps.push("Re-run compliance assessment after remediation to verify improvements");

    return steps;
  }

  private getControlFamiliesForFramework(framework: ComplianceFramework): string[] {
    const families: Record<ComplianceFramework, string[]> = {
      SOC2: ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6", "CC7", "CC8", "CC9"],
      ISO27001: ["A5", "A6", "A7", "A8", "A9"],
      NIST_CSF: ["ID", "PR", "DE", "RS", "RC"],
      PCI_DSS: ["Req1", "Req2", "Req3", "Req4", "Req5", "Req6", "Req7", "Req8", "Req9", "Req10"],
      HIPAA: ["Admin", "Technical", "Physical"],
      GDPR: ["Art5", "Art6", "Art12", "Art13", "Art14", "Art17", "Art25", "Art32", "Art33"],
      CCPA: ["1798.100", "1798.105", "1798.110", "1798.120", "1798.130"],
      SOX: ["Section302", "Section404"],
      FedRAMP: ["AC", "AU", "CM", "IA", "IR", "RA", "SA", "SC"],
      Custom: ["Custom"],
    };
    return families[framework] ?? ["General"];
  }

  private getControlIdsForFramework(framework: ComplianceFramework): string[] {
    const ids: Record<ComplianceFramework, string[]> = {
      SOC2: ["CC6.1", "CC6.6", "CC7.1", "CC8.1", "CC1.1", "CC2.1", "CC3.1", "CC4.1", "CC5.1", "CC9.1"],
      ISO27001: ["A5.1", "A5.2", "A6.1", "A7.1", "A8.1", "A8.2", "A8.3", "A9.1", "A9.2", "A9.4"],
      NIST_CSF: ["PR.AC-1", "PR.AC-4", "PR.DS-1", "PR.DS-2", "DE.CM-1", "DE.AE-1", "RS.RP-1", "RC.RP-1"],
      PCI_DSS: ["Req1.1", "Req2.1", "Req3.1", "Req4.1", "Req5.1", "Req6.1", "Req7.1", "Req8.1", "Req9.1", "Req10.1"],
      HIPAA: ["164.312a1", "164.312d1", "164.308a1", "164.310b1", "164.316b1"],
      GDPR: ["Art5.1", "Art6.1", "Art12.1", "Art25.1", "Art32.1", "Art33.1"],
      CCPA: ["1798.100a", "1798.105a", "1798.110a", "1798.120a", "1798.130a"],
      SOX: ["Section302a", "Section404a"],
      FedRAMP: ["AC-1", "AU-1", "CM-1", "IA-1", "IR-1", "RA-1", "SA-1", "SC-1"],
      Custom: ["Custom.1"],
    };
    return ids[framework] ?? ["General.1"];
  }

  // ------------------------------------------------------------------
  // Trust chain & messaging
  // ------------------------------------------------------------------

  private appendTrustLink(
    agentRole: AgentRole,
    action: string,
    taskId: string,
    outputHash: string,
  ): void {
    if (!this.config.enableTrustChain) return;

    const link: TrustChainLink = {
      taskId,
      agentId: agentRole,
      role: agentRole,
      action,
      inputHash: this.previousLinkHash,
      outputHash,
      timestamp: new Date().toISOString(),
      previousLinkHash: this.previousLinkHash,
    };

    this.trustChain.push(link);
    this.previousLinkHash = createHash("sha256").update(JSON.stringify(link)).digest("hex");
  }

  private broadcastMessage(
    payload: AgentMessage["payload"],
    task: SwarmTask,
  ): void {
    const message: AgentMessage = {
      id: `msg-${randomBytes(8).toString("hex")}`,
      from: task.assignedAgent ?? "evidence-collector",
      to: "broadcast",
      type: "status-update",
      taskId: task.id,
      goalId: task.goalId,
      payload,
      timestamp: new Date().toISOString(),
      requiresResponse: false,
    };

    this.messages.push(message);
  }

  private registerDefaultAgents(): void {
    this.agents.set("evidence-collector", new EvidenceCollector());
    this.agents.set("control-tester", new ControlTester());
    this.agents.set("risk-quantifier", new RiskQuantifier());
    this.agents.set("audit-preparer", new AuditPreparer());
    this.agents.set("remediation-executor", new RemediationExecutorAgent());
    this.agents.set("verifier", new Verifier());
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
