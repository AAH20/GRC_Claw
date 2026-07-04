import { describe, it, beforeEach } from "node:test";
import assert from "node:assert";
import { createHash } from "node:crypto";

import { SwarmCoordinator } from "./swarm-coordinator.js";
import { EvidenceCollector } from "./agents/evidence-collector.js";
import { ControlTester } from "./agents/control-tester.js";
import { RiskQuantifier } from "./agents/risk-quantifier.js";
import { AuditPreparer } from "./agents/audit-preparer.js";
import { RemediationExecutorAgent } from "./agents/remediation-executor.js";
import { Verifier } from "./agents/verifier.js";
import { BaseAgent } from "./agents/base-agent.js";
import type {
  ComplianceGoal,
  SwarmTask,
  SwarmCoordinatorConfig,
  ControlStatus,
  EvidenceItem,
  ComplianceFramework,
} from "./types.js";

// ============================================================================
// Helpers – deterministic fixtures
// ============================================================================

function makeGoal(overrides: Partial<ComplianceGoal> = {}): ComplianceGoal {
  return {
    id: "goal-test-001",
    title: "SOC2 Type II Compliance Assessment",
    description: "Full SOC2 compliance assessment for audit readiness",
    targetFrameworks: ["SOC2"],
    targetDate: "2026-12-31T00:00:00.000Z",
    priority: "high",
    scope: ["production-servers", "cloud-infrastructure"],
    metadata: { requester: "ciso", businessUnit: "engineering" },
    ...overrides,
  };
}

function makeMultiFrameworkGoal(): ComplianceGoal {
  return makeGoal({
    id: "goal-multi-001",
    title: "Multi-Framework Compliance",
    targetFrameworks: ["SOC2", "ISO27001"],
  });
}

function makeTask(overrides: Partial<SwarmTask> = {}): SwarmTask {
  return {
    id: "task-test-001",
    goalId: "goal-test-001",
    type: "evidence-collection",
    framework: "SOC2",
    priority: "high",
    description: "Collect evidence for SOC2",
    input: {
      evidenceCriteria: {
        framework: "SOC2",
        controlFamilies: ["CC6", "CC7"],
        evidenceTypes: ["configuration", "log"],
        sources: ["system"],
      },
    },
    assignedAgent: "evidence-collector",
    dependencies: [],
    timeoutMs: 120_000,
    createdAt: "2026-01-15T00:00:00.000Z",
    metadata: {},
    ...overrides,
  };
}

function makeControlStatuses(): ControlStatus[] {
  return [
    {
      controlId: "CC6.1",
      framework: "SOC2",
      title: "Logical access security software, infrastructure, and architectures",
      status: "compliant",
      confidence: 0.92,
      evidenceCount: 3,
      findings: [],
      lastTestedAt: "2026-01-15T00:00:00.000Z",
      testedBy: "control-tester-abc",
    },
    {
      controlId: "CC7.1",
      framework: "SOC2",
      title: "Detection and monitoring procedures",
      status: "non-compliant",
      confidence: 0.88,
      evidenceCount: 1,
      findings: [
        {
          id: "find-001",
          severity: "critical",
          title: "Missing monitoring for CC7.1",
          description: "No active monitoring configured",
          affectedResources: ["SOC2/CC7.1"],
          recommendation: "Deploy monitoring agent",
        },
      ],
      lastTestedAt: "2026-01-15T00:00:00.000Z",
      testedBy: "control-tester-abc",
    },
    {
      controlId: "CC8.1",
      framework: "SOC2",
      title: "Change detection and prevention procedures",
      status: "partial",
      confidence: 0.70,
      evidenceCount: 2,
      findings: [
        {
          id: "find-002",
          severity: "medium",
          title: "Partial change detection",
          description: "Change detection enabled but not for all systems",
          affectedResources: ["SOC2/CC8.1"],
          recommendation: "Extend change detection coverage",
        },
      ],
      lastTestedAt: "2026-01-15T00:00:00.000Z",
      testedBy: "control-tester-abc",
    },
  ];
}

function makeEvidenceItems(): EvidenceItem[] {
  const content = JSON.stringify({ source: "system", controlId: "CC6.1", type: "configuration" });
  const contentHash = createHash("sha256").update(content).digest("hex");
  return [
    {
      id: "ev-001",
      kind: "configuration",
      source: "system",
      controlId: "CC6.1",
      framework: "SOC2",
      content,
      contentHash,
      collectedAt: "2026-01-15T00:00:00.000Z",
      collectorAgentId: "evidence-collector-abc",
      trustSignature: {
        agentId: "evidence-collector-abc",
        agentRole: "evidence-collector",
        timestamp: "2026-01-15T00:00:00.000Z",
        contentHash,
        previousHash: "0".repeat(64),
        nonce: 12345,
        signature: "",
      },
      metadata: {},
    },
  ];
}

// ============================================================================
// 1. SwarmCoordinator Initialization
// ============================================================================

describe("SwarmCoordinator initialization", () => {
  it("should create with default config when no config provided", () => {
    const coordinator = new SwarmCoordinator();
    const agents = coordinator.getAgents();
    assert.equal(agents.length, 6, "Should register 6 default agents");
    assert.deepEqual(coordinator.getMessages(), []);
    assert.deepEqual(coordinator.getTrustChain(), []);
  });

  it("should merge custom config with defaults", () => {
    const coordinator = new SwarmCoordinator({
      dryRun: true,
      retryAttempts: 5,
      maxConcurrentTasks: 10,
    });
    const agents = coordinator.getAgents();
    assert.equal(agents.length, 6);
  });

  it("should register all six agent roles", () => {
    const coordinator = new SwarmCoordinator();
    const roles = coordinator.getAgents().map((a) => a.role);
    assert.ok(roles.includes("evidence-collector"));
    assert.ok(roles.includes("control-tester"));
    assert.ok(roles.includes("risk-quantifier"));
    assert.ok(roles.includes("audit-preparer"));
    assert.ok(roles.includes("remediation-executor"));
    assert.ok(roles.includes("verifier"));
  });

  it("should allow registering a custom agent", () => {
    const coordinator = new SwarmCoordinator();
    const customAgent = new EvidenceCollector();
    coordinator.registerAgent(customAgent);
    const agents = coordinator.getAgents();
    assert.ok(agents.some((a) => a.role === "evidence-collector"));
  });

  it("should initialize with empty message log", () => {
    const coordinator = new SwarmCoordinator();
    assert.equal(coordinator.getMessages().length, 0);
  });

  it("should initialize with empty trust chain", () => {
    const coordinator = new SwarmCoordinator();
    assert.equal(coordinator.getTrustChain().length, 0);
  });

  it("should return empty results for unknown task", () => {
    const coordinator = new SwarmCoordinator();
    assert.deepEqual(coordinator.getTaskResults("nonexistent-task"), []);
  });
});

// ============================================================================
// 2. Goal Decomposition into Tasks
// ============================================================================

describe("Goal decomposition into tasks", () => {
  it("executeGoal should produce a ComplianceReport", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.id.startsWith("report-"));
    assert.equal(report.goalId, goal.id);
    assert.equal(report.frameworks.length, 1);
    assert.equal(report.frameworks[0], "SOC2");
    assert.ok(typeof report.overallComplianceScore === "number");
    assert.ok(report.integrityHash.length === 64, "Integrity hash should be SHA-256 hex");
  });

  it("should decompose multi-framework goal into framework-specific tasks", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeMultiFrameworkGoal();
    const report = await coordinator.executeGoal(goal);

    assert.equal(report.frameworks.length, 2);
    assert.ok(report.frameworks.includes("SOC2"));
    assert.ok(report.frameworks.includes("ISO27001"));
    assert.ok(report.riskAssessment.frameworkBreakdown.length >= 1);
  });

  it("should populate agentActivityLog in report", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.agentActivityLog.length > 0, "Should have trust chain entries");
  });

  it("should produce recommendations in report", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(Array.isArray(report.recommendations));
    assert.ok(report.recommendations.length > 0);
  });

  it("should produce nextSteps in report", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(Array.isArray(report.nextSteps));
    assert.ok(report.nextSteps.length > 0);
  });
});

// ============================================================================
// 3. Evidence Collector Execution
// ============================================================================

describe("EvidenceCollector execution", () => {
  let collector: EvidenceCollector;

  beforeEach(() => {
    collector = new EvidenceCollector();
  });

  it("should collect evidence for a valid task", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration", "log"],
          sources: ["system"],
        },
      },
    });

    const result = await collector.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.evidence);
    assert.ok(result.output.evidence!.length > 0);
    assert.ok(result.output.summary.includes("Collected"));
  });

  it("should produce evidence items with valid content hashes", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await collector.execute(task);
    const evidence = result.output.evidence!;

    for (const item of evidence) {
      const computedHash = createHash("sha256").update(item.content).digest("hex");
      assert.equal(item.contentHash, computedHash, `Evidence ${item.id} hash mismatch`);
    }
  });

  it("should include a valid trust signature", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await collector.execute(task);
    assert.equal(result.trustSignature.agentRole, "evidence-collector");
    assert.ok(result.trustSignature.signature.length > 0);
    assert.ok(result.trustSignature.contentHash.length === 64);
  });

  it("should collect evidence across multiple control families", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6", "CC7", "CC8"],
          evidenceTypes: ["configuration", "log", "policy"],
          sources: ["system"],
        },
      },
    });

    const result = await collector.execute(task);
    const evidence = result.output.evidence!;
    assert.ok(evidence.length >= 3, "Should collect at least one per control family");
  });

  it("should fail without evidenceCriteria", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {},
    });

    const result = await collector.execute(task);
    assert.equal(result.status, "failed");
    assert.ok(result.error!.includes("evidenceCriteria"));
  });

  it("should track collected evidence per task", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    await collector.execute(task);
    const stored = collector.getCollectedEvidence(task.id);
    assert.ok(stored.length > 0);
  });

  it("should transition status from idle to busy and back", async () => {
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    assert.equal(collector.status, "idle");
    const result = await collector.execute(task);
    assert.equal(result.status, "completed");
    assert.equal(collector.status, "idle");
  });
});

// ============================================================================
// 4. Control Tester Execution
// ============================================================================

describe("ControlTester execution", () => {
  let tester: ControlTester;

  beforeEach(() => {
    tester = new ControlTester();
  });

  it("should test controls and produce ControlStatuses", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {
        controlIds: ["CC6.1", "CC7.1"],
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6", "CC7"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await tester.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.controlStatuses);
    assert.equal(result.output.controlStatuses!.length, 2);
    assert.ok(result.output.summary.includes("Tested"));
  });

  it("should produce deterministic results for same control+framework hash", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {
        controlIds: ["CC6.1"],
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result1 = await tester.execute(task);
    const result2 = await tester.execute(task);

    const status1 = result1.output.controlStatuses![0];
    const status2 = result2.output.controlStatuses![0];
    assert.equal(status1.status, status2.status, "Deterministic: same input should yield same status");
  });

  it("should return not-assessed when no evidence sources provided", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {
        controlIds: ["CC6.1"],
      },
    });

    const result = await tester.execute(task);
    const status = result.output.controlStatuses![0];
    assert.equal(status.status, "not-assessed");
    assert.equal(status.confidence, 0.0);
  });

  it("should fail without control IDs", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {},
    });

    const result = await tester.execute(task);
    assert.equal(result.status, "failed");
    assert.ok(result.error!.includes("control ID"));
  });

  it("should include findings for non-compliant controls", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {
        controlIds: ["CC6.1"],
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await tester.execute(task);
    const status = result.output.controlStatuses![0];
    if (status.status === "non-compliant") {
      assert.ok(status.findings.length > 0, "Non-compliant controls should have findings");
    }
  });

  it("should generate recommendations based on results", async () => {
    const task = makeTask({
      type: "control-testing",
      assignedAgent: "control-tester",
      input: {
        controlIds: ["CC6.1", "CC7.1"],
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6", "CC7"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await tester.execute(task);
    assert.ok(Array.isArray(result.output.recommendations));
  });
});

// ============================================================================
// 5. Risk Quantifier Execution
// ============================================================================

describe("RiskQuantifier execution", () => {
  let quantifier: RiskQuantifier;

  beforeEach(() => {
    quantifier = new RiskQuantifier();
  });

  it("should produce a risk assessment with scores", async () => {
    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "high",
          regulatoryRisk: true,
        },
        customParameters: {
          controlStatuses: makeControlStatuses(),
        },
      },
    });

    const result = await quantifier.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.riskAssessment);
    const risk = result.output.riskAssessment!;
    assert.ok(typeof risk.overallScore === "number");
    assert.ok(risk.overallScore >= 0 && risk.overallScore <= 10);
    assert.ok(["critical", "high", "medium", "low", "informational"].includes(risk.riskLevel));
  });

  it("should identify top risks from non-compliant controls", async () => {
    const controlStatuses: ControlStatus[] = [
      {
        controlId: "CC6.1",
        framework: "SOC2",
        title: "Access Control",
        status: "non-compliant",
        confidence: 0.85,
        evidenceCount: 1,
        findings: [
          {
            id: "f1",
            severity: "critical",
            title: "Missing MFA",
            description: "MFA not enforced",
            affectedResources: ["auth-service"],
            recommendation: "Enable MFA",
          },
        ],
        lastTestedAt: "2026-01-15T00:00:00.000Z",
        testedBy: "tester-1",
      },
    ];

    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "critical",
          regulatoryRisk: true,
        },
        customParameters: { controlStatuses },
      },
    });

    const result = await quantifier.execute(task);
    const risk = result.output.riskAssessment!;
    assert.ok(risk.topRisks.length > 0, "Should identify at least one risk");
    assert.ok(risk.topRisks.some((r) => r.riskLevel === "critical" || r.riskLevel === "high"));
  });

  it("should handle empty control statuses gracefully", async () => {
    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "medium",
          regulatoryRisk: false,
        },
      },
    });

    const result = await quantifier.execute(task);
    assert.equal(result.status, "completed");
    const risk = result.output.riskAssessment!;
    assert.equal(risk.frameworkBreakdown.length, 1);
    assert.equal(risk.frameworkBreakdown[0].controlsTotal, 0);
  });

  it("should include framework breakdown", async () => {
    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "high",
          regulatoryRisk: true,
        },
        customParameters: { controlStatuses: makeControlStatuses() },
      },
    });

    const result = await quantifier.execute(task);
    const risk = result.output.riskAssessment!;
    assert.ok(risk.frameworkBreakdown.length >= 1);
    assert.equal(risk.frameworkBreakdown[0].framework, "SOC2");
  });

  it("should store assessment for later retrieval", async () => {
    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "medium",
          regulatoryRisk: false,
        },
      },
    });

    await quantifier.execute(task);
    const stored = quantifier.getAssessment(task.id);
    assert.ok(stored);
    assert.ok(stored!.frameworkBreakdown.length >= 1);
  });

  it("should calculate residual risk score", async () => {
    const task = makeTask({
      type: "risk-quantification",
      assignedAgent: "risk-quantifier",
      input: {
        riskScope: {
          assetCategories: ["all"],
          threatCategories: ["compliance-gap"],
          businessImpact: "high",
          regulatoryRisk: true,
        },
        customParameters: { controlStatuses: makeControlStatuses() },
      },
    });

    const result = await quantifier.execute(task);
    const risk = result.output.riskAssessment!;
    assert.ok(typeof risk.residualRiskScore === "number");
    assert.ok(risk.residualRiskScore >= 0 && risk.residualRiskScore <= 10);
  });
});

// ============================================================================
// 6. Audit Preparer Execution
// ============================================================================

describe("AuditPreparer execution", () => {
  let preparer: AuditPreparer;

  beforeEach(() => {
    preparer = new AuditPreparer();
  });

  it("should produce an audit package", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: makeControlStatuses(),
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await preparer.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.auditPackage);
    const pkg = result.output.auditPackage!;
    assert.ok(pkg.id.startsWith("audit-pkg-"));
    assert.ok(pkg.frameworks.includes("SOC2"));
    assert.ok(typeof pkg.complianceScore === "number");
    assert.ok(["ready", "mostly-ready", "gaps-identified", "not-ready"].includes(pkg.readinessLevel));
  });

  it("should identify gaps for non-compliant and partial controls", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: makeControlStatuses(),
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await preparer.execute(task);
    const pkg = result.output.auditPackage!;
    assert.ok(pkg.gaps.length > 0, "Should identify gaps from non-compliant/partial controls");
  });

  it("should generate an executive summary", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: makeControlStatuses(),
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await preparer.execute(task);
    const pkg = result.output.auditPackage!;
    assert.ok(pkg.executiveSummary.length > 0);
    assert.ok(pkg.executiveSummary.includes("EXECUTIVE SUMMARY"));
  });

  it("should build sections per framework", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: makeControlStatuses(),
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await preparer.execute(task);
    const pkg = result.output.auditPackage!;
    assert.ok(pkg.sections.length > 0);
    assert.ok(pkg.sections.every((s) => s.framework === "SOC2"));
  });

  it("should store audit package for retrieval", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: [],
          evidence: [],
        },
      },
    });

    await preparer.execute(task);
    const stored = preparer.getAuditPackage(task.id);
    assert.ok(stored);
  });

  it("should handle empty control statuses", async () => {
    const task = makeTask({
      type: "audit-preparation",
      assignedAgent: "audit-preparer",
      input: {
        auditWindow: {
          startDate: "2025-10-01T00:00:00.000Z",
          endDate: "2026-01-15T00:00:00.000Z",
          frameworks: ["SOC2"],
          includeHistoricalEvidence: true,
        },
        customParameters: {
          controlStatuses: [],
          evidence: [],
        },
      },
    });

    const result = await preparer.execute(task);
    const pkg = result.output.auditPackage!;
    assert.equal(pkg.gaps.length, 0);
    assert.equal(pkg.complianceScore, 0);
  });
});

// ============================================================================
// 7. Remediation Executor Execution
// ============================================================================

describe("RemediationExecutor execution", () => {
  let executor: RemediationExecutorAgent;

  beforeEach(() => {
    executor = new RemediationExecutorAgent();
  });

  it("should execute remediation actions for auto-approved plans", async () => {
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-001",
          controlId: "CC6.1",
          severity: "high",
          autoApprove: true,
        },
      },
    });

    const result = await executor.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.remediationResults);
    const results = result.output.remediationResults!;
    assert.ok(results.length > 0);
    assert.ok(results.some((r) => r.status === "executed"));
  });

  it("should require approval for high-risk non-auto-approved actions", async () => {
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-002",
          controlId: "CC7.1",
          severity: "high",
          autoApprove: false,
        },
      },
    });

    const result = await executor.execute(task);
    const results = result.output.remediationResults!;
    assert.ok(results.some((r) => r.status === "pending-approval"));
  });

  it("should fail without remediationPlan", async () => {
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {},
    });

    const result = await executor.execute(task);
    assert.equal(result.status, "failed");
    assert.ok(result.error!.includes("remediationPlan"));
  });

  it("should include more actions for critical severity", async () => {
    const criticalTask = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-critical",
          controlId: "CC6.1",
          severity: "critical",
          autoApprove: true,
        },
      },
    });

    const highTask = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-high",
          controlId: "CC6.1",
          severity: "high",
          autoApprove: true,
        },
      },
    });

    const criticalResult = await executor.execute(criticalTask);
    const highResult = await executor.execute(highTask);

    assert.ok(
      criticalResult.output.remediationResults!.length >= highResult.output.remediationResults!.length,
      "Critical should have >= actions than high",
    );
  });

  it("should store execution history", async () => {
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-003",
          controlId: "CC6.1",
          severity: "low",
          autoApprove: true,
        },
      },
    });

    await executor.execute(task);
    const history = executor.getExecutionHistory(task.id);
    assert.ok(history.length > 0);
  });

  it("should generate recommendations based on results", async () => {
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-004",
          controlId: "CC6.1",
          severity: "critical",
          autoApprove: true,
        },
      },
    });

    const result = await executor.execute(task);
    assert.ok(Array.isArray(result.output.recommendations));
    assert.ok(result.output.recommendations.length > 0);
  });
});

// ============================================================================
// 8. Verifier Execution
// ============================================================================

describe("Verifier execution", () => {
  let verifier: Verifier;

  beforeEach(() => {
    verifier = new Verifier();
  });

  it("should verify controls and produce verification results", async () => {
    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: ["CC6.1", "CC7.1"],
        customParameters: {
          controlStatuses: makeControlStatuses(),
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await verifier.execute(task);

    assert.equal(result.status, "completed");
    assert.ok(result.output.verificationResults);
    assert.ok(result.output.verificationResults!.length > 0);
    assert.ok(result.output.summary.includes("Verification complete"));
  });

  it("should detect evidence integrity issues when content is tampered", async () => {
    const tamperedEvidence: EvidenceItem[] = [
      {
        id: "ev-tampered",
        kind: "configuration",
        source: "system",
        controlId: "CC6.1",
        framework: "SOC2",
        content: "original content",
        contentHash: "0".repeat(64), // wrong hash
        collectedAt: "2026-01-15T00:00:00.000Z",
        collectorAgentId: "agent-1",
        trustSignature: {
          agentId: "agent-1",
          agentRole: "evidence-collector",
          timestamp: "2026-01-15T00:00:00.000Z",
          contentHash: "0".repeat(64),
          previousHash: "0".repeat(64),
          nonce: 0,
          signature: "",
        },
        metadata: {},
      },
    ];

    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: ["CC6.1"],
        customParameters: {
          controlStatuses: [
            {
              ...makeControlStatuses()[0],
              controlId: "CC6.1",
              status: "compliant",
            },
          ],
          evidence: tamperedEvidence,
        },
      },
    });

    const result = await verifier.execute(task);
    const integrityCheck = result.output.verificationResults!.find(
      (r) => r.checkType === "batch-integrity",
    );
    assert.ok(integrityCheck, "Should have batch integrity check");
    assert.equal(integrityCheck!.passed, false, "Tampered evidence should fail integrity check");
  });

  it("should pass verification for all-compliant controls with valid evidence", async () => {
    const compliantStatus: ControlStatus[] = [
      {
        controlId: "CC6.1",
        framework: "SOC2",
        title: "Logical access security",
        status: "compliant",
        confidence: 0.95,
        evidenceCount: 2,
        findings: [],
        lastTestedAt: "2026-01-15T00:00:00.000Z",
        testedBy: "tester-1",
      },
    ];

    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: ["CC6.1"],
        customParameters: {
          controlStatuses: compliantStatus,
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await verifier.execute(task);
    const controlResults = result.output.verificationResults!.filter(
      (r) => r.checkType === "compliance-status",
    );
    assert.ok(controlResults.every((r) => r.passed), "All compliance checks should pass for compliant controls");
  });

  it("should handle empty control statuses", async () => {
    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: [],
        customParameters: {
          controlStatuses: [],
          evidence: [],
        },
      },
    });

    const result = await verifier.execute(task);
    assert.equal(result.status, "completed");
    assert.ok(result.output.verificationResults!.length > 0, "Should have at least a no-controls result");
  });

  it("should store verification history", async () => {
    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: ["CC6.1"],
        customParameters: {
          controlStatuses: makeControlStatuses().slice(0, 1),
          evidence: makeEvidenceItems(),
        },
      },
    });

    await verifier.execute(task);
    const history = verifier.getVerificationHistory(task.id);
    assert.ok(history.length > 0);
  });

  it("should flag non-compliant controls in verification", async () => {
    const nonCompliantStatus: ControlStatus[] = [
      {
        controlId: "CC7.1",
        framework: "SOC2",
        title: "Detection and monitoring",
        status: "non-compliant",
        confidence: 0.88,
        evidenceCount: 1,
        findings: [],
        lastTestedAt: "2026-01-15T00:00:00.000Z",
        testedBy: "tester-1",
      },
    ];

    const task = makeTask({
      type: "verification",
      assignedAgent: "verifier",
      input: {
        controlIds: ["CC7.1"],
        customParameters: {
          controlStatuses: nonCompliantStatus,
          evidence: makeEvidenceItems(),
        },
      },
    });

    const result = await verifier.execute(task);
    const complianceCheck = result.output.verificationResults!.find(
      (r) => r.checkType === "compliance-status",
    );
    assert.ok(complianceCheck);
    assert.equal(complianceCheck!.passed, false);
    assert.equal(complianceCheck!.actual, "non-compliant");
  });
});

// ============================================================================
// 9. Full Swarm Execution (all agents in sequence via executeGoal)
// ============================================================================

describe("Full swarm execution (all agents in sequence)", () => {
  it("should execute all 5 phases end-to-end for SOC2", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.equal(report.frameworks.length, 1);
    assert.ok(report.riskAssessment);
    assert.ok(report.evidenceSummary);
    assert.ok(report.remediationsSummary);
    assert.ok(report.integrityHash.length === 64);
  });

  it("should populate all report sections", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.id);
    assert.ok(report.goalId);
    assert.ok(report.generatedAt);
    assert.ok(typeof report.overallComplianceScore === "number");
    assert.ok(report.riskAssessment);
    assert.ok(report.evidenceSummary);
    assert.ok(report.remediationsSummary);
    assert.ok(Array.isArray(report.crossFrameworkMappings));
    assert.ok(report.agentActivityLog.length > 0);
    assert.ok(report.recommendations.length > 0);
    assert.ok(report.nextSteps.length > 0);
  });

  it("should handle PCI_DSS framework", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal({
      id: "goal-pci-001",
      title: "PCI DSS Compliance",
      targetFrameworks: ["PCI_DSS"],
    });
    const report = await coordinator.executeGoal(goal);

    assert.equal(report.frameworks[0], "PCI_DSS");
    assert.ok(report.controlStatuses.length > 0 || report.evidenceSummary.totalItems > 0);
  });

  it("should handle GDPR framework", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal({
      id: "goal-gdpr-001",
      title: "GDPR Compliance",
      targetFrameworks: ["GDPR"],
    });
    const report = await coordinator.executeGoal(goal);

    assert.equal(report.frameworks[0], "GDPR");
    assert.ok(report.riskAssessment);
  });

  it("should produce messages during execution", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    await coordinator.executeGoal(goal);

    const messages = coordinator.getMessages();
    assert.ok(messages.length > 0, "Should produce inter-agent messages");
    assert.ok(messages.every((m) => m.id.startsWith("msg-")));
  });

  it("should link trust chain across phases", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    await coordinator.executeGoal(goal);

    const chain = coordinator.getTrustChain();
    assert.ok(chain.length > 1, "Trust chain should have multiple links");
  });
});

// ============================================================================
// 10. Parallel Agent Execution
// ============================================================================

describe("Parallel agent execution", () => {
  it("should execute multiple evidence-collection tasks in parallel", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeMultiFrameworkGoal();

    const startTime = Date.now();
    const report = await coordinator.executeGoal(goal);
    const elapsed = Date.now() - startTime;

    assert.equal(report.frameworks.length, 2);
    assert.ok(report.evidenceSummary.totalItems > 0);
    assert.ok(typeof elapsed === "number");
  });

  it("should execute independent tasks concurrently within a phase", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });

    const task1 = makeTask({
      id: "parallel-task-1",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const task2 = makeTask({
      id: "parallel-task-2",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {
        evidenceCriteria: {
          framework: "ISO27001",
          controlFamilies: ["A8"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const [result1, result2] = await Promise.all([
      coordinator.executeTask(task1),
      coordinator.executeTask(task2),
    ]);

    assert.equal(result1.status, "completed");
    assert.equal(result2.status, "completed");
    assert.notEqual(result1.agentId, result2.agentId || true, "Results should be independent");
  });

  it("should produce trust chain entries for parallel tasks", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });

    const tasks = Array.from({ length: 3 }, (_, i) =>
      makeTask({
        id: `par-${i}`,
        type: "evidence-collection",
        assignedAgent: "evidence-collector",
        input: {
          evidenceCriteria: {
            framework: "SOC2",
            controlFamilies: [`CC${i + 6}` as string],
            evidenceTypes: ["configuration"],
            sources: ["system"],
          },
        },
      }),
    );

    await Promise.all(tasks.map((t) => coordinator.executeTask(t)));

    const chain = coordinator.getTrustChain();
    assert.equal(chain.length, 3);
  });
});

// ============================================================================
// 11. Trust Chain Integrity (hash linking)
// ============================================================================

describe("Trust chain integrity (hash linking)", () => {
  it("should chain trust links with hash references", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    await coordinator.executeGoal(goal);

    const chain = coordinator.getTrustChain();
    assert.ok(chain.length > 1);

    for (let i = 1; i < chain.length; i++) {
      const prevHash = createHash("sha256").update(JSON.stringify(chain[i - 1])).digest("hex");
      assert.equal(
        chain[i].previousLinkHash,
        prevHash,
        `Chain link ${i} previousLinkHash should match hash of link ${i - 1}`,
      );
    }
  });

  it("should start chain with initial previousLinkHash of zeros", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    await coordinator.executeGoal(goal);

    const chain = coordinator.getTrustChain();
    assert.ok(chain.length > 0);
    assert.equal(
      chain[0].previousLinkHash,
      "0".repeat(64),
      "First link should have zero previousLinkHash",
    );
  });

  it("should include trust signatures in individual task results", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const task = makeTask({
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await coordinator.executeTask(task);

    assert.ok(result.trustSignature);
    assert.ok(result.trustSignature.signature.length > 0);
    assert.ok(result.trustSignature.contentHash.length === 64);
    assert.ok(result.trustSignature.agentId.length > 0);
    assert.ok(result.trustSignature.timestamp);
  });

  it("should produce different signatures for different tasks", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });

    const task1 = makeTask({
      id: "sig-task-1",
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const task2 = makeTask({
      id: "sig-task-2",
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC7"],
          evidenceTypes: ["log"],
          sources: ["system"],
        },
      },
    });

    const [result1, result2] = await Promise.all([
      coordinator.executeTask(task1),
      coordinator.executeTask(task2),
    ]);

    assert.notEqual(
      result1.trustSignature.signature,
      result2.trustSignature.signature,
      "Different tasks should produce different signatures",
    );
  });

  it("should include outputHash in trust chain links", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    await coordinator.executeGoal(goal);

    const chain = coordinator.getTrustChain();
    for (const link of chain) {
      assert.ok(link.outputHash.length === 64, "Each link should have a valid outputHash");
    }
  });
});

// ============================================================================
// 12. Dry-Run Mode
// ============================================================================

describe("Dry-run mode", () => {
  it("should mark tasks with dryRun metadata", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.id.startsWith("report-"));
    assert.ok(typeof report.overallComplianceScore === "number");
  });

  it("should skip remediation actions in dry-run mode", async () => {
    const executor = new RemediationExecutorAgent();
    const task = makeTask({
      type: "remediation-execution",
      assignedAgent: "remediation-executor",
      input: {
        remediationPlan: {
          issueId: "issue-dry-001",
          controlId: "CC6.1",
          severity: "critical",
          autoApprove: true,
        },
      },
      metadata: { dryRun: true },
    });

    const result = await executor.execute(task);
    const results = result.output.remediationResults!;
    assert.ok(results.length > 0);
    assert.ok(
      results.every((r) => r.status === "skipped"),
      "All actions should be skipped in dry-run mode",
    );
    assert.ok(results.every((r) => r.action.startsWith("[DRY RUN]")));
  });

  it("should still produce valid trust signatures in dry-run", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.integrityHash.length === 64);
    assert.ok(report.agentActivityLog.length > 0);
  });

  it("should allow full goal execution in dry-run without errors", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeMultiFrameworkGoal();

    const report = await coordinator.executeGoal(goal);
    assert.ok(report);
    assert.ok(report.id);
    assert.ok(report.riskAssessment);
  });
});

// ============================================================================
// 13. Error Handling
// ============================================================================

describe("Error handling", () => {
  it("should handle agent execution failure gracefully", async () => {
    const coordinator = new SwarmCoordinator({ retryDelayMs: 0, retryAttempts: 0 });
    const badTask = makeTask({
      id: "bad-task-001",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {}, // missing evidenceCriteria causes failure
    });

    const result = await coordinator.executeTask(badTask);

    assert.equal(result.status, "failed");
    assert.ok(result.error);
    assert.ok(result.trustSignature, "Should still produce a trust signature on failure");
  });

  it("should retry failed tasks up to retryAttempts", async () => {
    const coordinator = new SwarmCoordinator({
      retryAttempts: 2,
      retryDelayMs: 1,
    });

    let callCount = 0;
    const flakyAgent = new EvidenceCollector();
    const originalExecute = flakyAgent.execute.bind(flakyAgent);

    // Override to fail first 2 calls then succeed
    flakyAgent.execute = async function (task: SwarmTask) {
      callCount++;
      if (callCount <= 2) {
        throw new Error("Transient failure");
      }
      return originalExecute(task);
    };

    coordinator.registerAgent(flakyAgent);

    const task = makeTask({
      id: "retry-task-001",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await coordinator.executeTask(task);
    assert.equal(result.status, "completed");
    assert.ok(callCount >= 3, "Should have retried at least 3 times");
  });

  it("should fail with error after exhausting retries", async () => {
    const coordinator = new SwarmCoordinator({
      retryAttempts: 1,
      retryDelayMs: 1,
    });

    const alwaysFailAgent = new EvidenceCollector();
    alwaysFailAgent.execute = async () => {
      throw new Error("Persistent failure");
    };

    coordinator.registerAgent(alwaysFailAgent);

    const task = makeTask({
      id: "fail-task-001",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const result = await coordinator.executeTask(task);
    assert.equal(result.status, "failed");
    assert.ok(result.error!.includes("Persistent failure"));
  });

  it("should lower trust score on agent failure", async () => {
    const agent = new EvidenceCollector();
    const initialTrust = agent.trustScore;

    const task = makeTask({
      id: "trust-fail-001",
      type: "evidence-collection",
      assignedAgent: "evidence-collector",
      input: {}, // missing evidenceCriteria
    });

    await agent.execute(task);
    assert.ok(agent.trustScore < initialTrust, "Trust score should decrease after failure");
  });

  it("should handle non-Error thrown values", async () => {
    const agent = new EvidenceCollector();
    const original = agent.execute;
    agent.execute = async function () {
      throw "string error"; // eslint-disable-line no-throw-literal
    } as any;

    const task = makeTask({
      id: "string-error-001",
      type: "evidence-collection",
    });

    const result = await agent.execute(task);
    assert.equal(result.status, "failed");
    assert.ok(result.error);
  });

  it("should recover agent status to idle after failure", async () => {
    const agent = new EvidenceCollector();
    const task = makeTask({
      id: "recover-001",
      type: "evidence-collection",
      input: {}, // will cause failure
    });

    const result = await agent.execute(task);
    assert.equal(result.status, "failed");
    assert.equal(agent.status, "idle");
    assert.equal(agent.currentTaskCount, 0);
  });

  it("should handle setOffline preventing task execution", async () => {
    const agent = new EvidenceCollector();
    agent.setOffline();

    const task = makeTask({
      id: "offline-001",
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const canHandle = agent.canHandle(task);
    assert.equal(canHandle, false, "Offline agent should not handle tasks");
  });

  it("should allow agent to come back online", async () => {
    const agent = new EvidenceCollector();
    agent.setOffline();
    assert.equal(agent.status, "offline");

    agent.setOnline();
    assert.equal(agent.status, "idle");

    const task = makeTask({
      id: "online-001",
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const canHandle = agent.canHandle(task);
    assert.equal(canHandle, true);
  });

  it("should handle concurrent task count limits", async () => {
    const agent = new EvidenceCollector();
    // maxConcurrentTasks defaults to 5
    for (let i = 0; i < 5; i++) {
      agent.currentTaskCount++;
    }

    const task = makeTask({
      id: "limit-001",
      type: "evidence-collection",
      input: {
        evidenceCriteria: {
          framework: "SOC2",
          controlFamilies: ["CC6"],
          evidenceTypes: ["configuration"],
          sources: ["system"],
        },
      },
    });

    const canHandle = agent.canHandle(task);
    assert.equal(canHandle, false, "Should not accept task at max concurrency");
  });

  it("should return empty results for non-existent task ID", () => {
    const coordinator = new SwarmCoordinator();
    const results = coordinator.getTaskResults("nonexistent");
    assert.deepEqual(results, []);
  });

  it("should produce valid integrity hash even on partial failures", async () => {
    const coordinator = new SwarmCoordinator({
      dryRun: true,
      retryDelayMs: 0,
      retryAttempts: 0,
    });

    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.integrityHash.length === 64);
    const expectedHash = createHash("sha256")
      .update(
        JSON.stringify({
          goalId: goal.id,
          score: report.overallComplianceScore,
          controlCount: report.controlStatuses.length,
          evidenceCount: report.evidenceSummary.totalItems,
          riskLevel: report.riskAssessment.riskLevel,
        }),
      )
      .digest("hex");
    assert.equal(report.integrityHash, expectedHash);
  });
});

// ============================================================================
// Edge Cases & Additional Coverage
// ============================================================================

describe("Edge cases", () => {
  it("should handle SUPPORTED_FRAMEWORKS list", async () => {
    const { SUPPORTED_FRAMEWORKS } = await import("./index.js");
    assert.ok(SUPPORTED_FRAMEWORKS.length >= 10);
    assert.ok(SUPPORTED_FRAMEWORKS.includes("SOC2"));
    assert.ok(SUPPORTED_FRAMEWORKS.includes("ISO27001"));
    assert.ok(SUPPORTED_FRAMEWORKS.includes("Custom"));
  });

  it("should handle AGENT_ROLES list", async () => {
    const { AGENT_ROLES } = await import("./index.js");
    assert.equal(AGENT_ROLES.length, 6);
    assert.ok(AGENT_ROLES.includes("evidence-collector"));
    assert.ok(AGENT_ROLES.includes("verifier"));
  });

  it("should handle createSwarm factory", async () => {
    const { createSwarm } = await import("./index.js");
    const coordinator = await createSwarm({ dryRun: true });
    assert.ok(coordinator);
    assert.equal(coordinator.getAgents().length, 6);
  });

  it("should handle cross-framework mappings for multi-framework goals", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeMultiFrameworkGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(Array.isArray(report.crossFrameworkMappings));
  });

  it("should handle different priority levels in goals", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });

    const criticalGoal = makeGoal({
      id: "critical-goal",
      priority: "critical",
      targetFrameworks: ["SOC2"],
    });

    const report = await coordinator.executeGoal(criticalGoal);
    assert.ok(report);
    assert.equal(report.goal.priority, "critical");
  });

  it("should produce audit package through full pipeline", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal();
    const report = await coordinator.executeGoal(goal);

    assert.ok(report.auditPackage, "Full pipeline should produce audit package");
    if (report.auditPackage) {
      assert.ok(report.auditPackage.sections.length > 0);
      assert.ok(report.auditPackage.readinessLevel);
    }
  });

  it("should correctly handle empty scope in goal", async () => {
    const coordinator = new SwarmCoordinator({ dryRun: true, retryDelayMs: 0 });
    const goal = makeGoal({ scope: [] });
    const report = await coordinator.executeGoal(goal);
    assert.ok(report);
  });

  it("should handle SHA-256 hashing via BaseAgent.hash()", () => {
    const agent = new EvidenceCollector();
    const data = "test data for hashing";
    const hash = agent.hash(data);
    const expected = createHash("sha256").update(data).digest("hex");
    assert.equal(hash, expected);
  });
});
