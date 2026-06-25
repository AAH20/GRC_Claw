import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ContinuousComplianceEngine } from "./index.js";
import type { EvidenceIntegrityChecker } from "./monitors/RealTimeDriftDetector.js";
import type { RemediationExecutor, RemediationResult } from "./remediation/AutoRemediationEngine.js";
import type { ComplianceBaseline } from "./types.js";

const mockEvidenceChecker: EvidenceIntegrityChecker = {
  async verifyEvidence(): Promise<boolean> { return true; },
  async getCurrentEvidence(): Promise<{ hash: string; uri: string }[]> {
    return [{ hash: "abc123", uri: "s3://evidence/test.pdf" }];
  },
};

const mockRemediationExecutor: RemediationExecutor = {
  async execute(): Promise<RemediationResult> {
    return { success: true, message: "Executed successfully", actionsTaken: ["test_action"] };
  },
};

const testBaseline: ComplianceBaseline = {
  frameworkCode: "iso27001",
  tenantId: "tenant-1",
  controls: [
    {
      controlId: "ctrl-1",
      controlCode: "A.5.1",
      expectedStatus: "implemented",
      evidenceHashes: ["abc123"],
      lastVerifiedAt: new Date().toISOString(),
    },
  ],
  snapshotAt: new Date().toISOString(),
  version: 1,
};

describe("ContinuousComplianceEngine", () => {
  it("should load baseline successfully", async () => {
    const engine = new ContinuousComplianceEngine(mockEvidenceChecker, mockRemediationExecutor);
    await engine.loadBaseline(testBaseline);
    assert.ok(engine.getDriftDetector());
  });

  it("should detect no drift when evidence is valid", async () => {
    const engine = new ContinuousComplianceEngine(mockEvidenceChecker, mockRemediationExecutor);
    await engine.loadBaseline(testBaseline);
    const drifts = await engine.getDriftDetector().detectDrift("tenant-1", "iso27001");
    assert.equal(drifts.length, 0);
  });

  it("should take a compliance snapshot", async () => {
    const engine = new ContinuousComplianceEngine(mockEvidenceChecker, mockRemediationExecutor);
    await engine.loadBaseline(testBaseline);
    const snapshot = await engine.takeSnapshot("tenant-1", "iso27001");
    assert.equal(snapshot.tenantId, "tenant-1");
    assert.equal(snapshot.frameworkCode, "iso27001");
    assert.equal(snapshot.controlCount, 0);
  });

  it("should register and manage monitors", () => {
    const engine = new ContinuousComplianceEngine(mockEvidenceChecker, mockRemediationExecutor);
    engine.registerMonitor({
      id: "monitor-1",
      name: "Test Monitor",
      type: "continuous",
      tenantId: "tenant-1",
      frameworkCodes: ["iso27001"],
      enabled: true,
      alertChannels: ["console"],
      autoRemediate: false,
      maxAutoRemediationSeverity: "medium",
    });
    assert.ok(engine.getDriftDetector());
  });

  it("should provide access to sub-engines", () => {
    const engine = new ContinuousComplianceEngine(mockEvidenceChecker, mockRemediationExecutor);
    assert.ok(engine.getDriftDetector());
    assert.ok(engine.getPostureMonitor());
    assert.ok(engine.getRemediationEngine());
  });
});

describe("AutoRemediationEngine", () => {
  it("should create remediation plan for evidence missing drift", async () => {
    const { AutoRemediationEngine } = await import("./remediation/AutoRemediationEngine.js");
    const remediationEngine = new AutoRemediationEngine(mockRemediationExecutor);

    const drift = {
      id: "drift-1",
      tenantId: "tenant-1",
      frameworkCode: "iso27001" as any,
      controlId: "ctrl-1",
      controlCode: "A.5.1",
      detectedAt: new Date().toISOString(),
      severity: "medium" as any,
      driftType: "evidence_missing" as any,
      description: "Test drift",
      remediable: true,
      resolved: false,
    };

    const plan = remediationEngine.createRemediationPlan(drift);
    assert.equal(plan.driftEventId, "drift-1");
    assert.ok(plan.actions.length > 0);
  });

  it("should determine auto-remediation eligibility", async () => {
    const { AutoRemediationEngine } = await import("./remediation/AutoRemediationEngine.js");
    const remediationEngine = new AutoRemediationEngine(mockRemediationExecutor);

    const lowDrift = { severity: "low" as any, remediable: true };
    const criticalDrift = { severity: "critical" as any, remediable: true };

    assert.ok(remediationEngine.canAutoRemediate(lowDrift as any));
    assert.ok(!remediationEngine.canAutoRemediate(criticalDrift as any));
  });
});

describe("CompliancePostureMonitor", () => {
  it("should calculate posture with healthy controls", async () => {
    const { CompliancePostureMonitor } = await import("./monitors/CompliancePostureMonitor.js");
    const monitor = new CompliancePostureMonitor();

    const controlStatuses = new Map([
      ["ctrl-1", { implemented: true, evidenceValid: true, lastChecked: new Date().toISOString() }],
    ]);

    const posture = monitor.calculatePosture({
      tenantId: "tenant-1",
      frameworkCode: "iso27001",
      controlStatuses,
      driftEvents: [],
    });

    assert.equal(posture.tenantId, "tenant-1");
    assert.ok(posture.overallScore > 0);
  });

  it("should return empty history for new tenant", async () => {
    const { CompliancePostureMonitor } = await import("./monitors/CompliancePostureMonitor.js");
    const monitor = new CompliancePostureMonitor();
    const history = monitor.getPostureHistory("tenant-new", "iso27001");
    assert.equal(history.length, 0);
  });
});
