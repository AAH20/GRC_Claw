import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  ACCMEngine,
  JiraTicketExecutor,
  SlackNotificationExecutor,
  ApiEndpointExecutor,
  ControlStatusExecutor,
} from "./index.js";
import type { GapDetector, ControlRecord, FrameworkCode } from "./types.js";

// ─── Mock Gap Detector ────────────────────────────────────────────────

const mockControls: ControlRecord[] = [
  {
    controlId: "ctrl-1",
    controlCode: "A.5.1",
    title: "Policies for information security",
    frameworkCode: "iso27001",
    implemented: false,
    evidenceHashes: [],
    lastVerifiedAt: new Date().toISOString(),
    owner: "security-team",
  },
  {
    controlId: "ctrl-2",
    controlCode: "A.5.2",
    title: "Information security roles",
    frameworkCode: "iso27001",
    implemented: true,
    evidenceHashes: ["hash-abc"],
    lastVerifiedAt: new Date().toISOString(),
    owner: "security-team",
  },
  {
    controlId: "ctrl-3",
    controlCode: "A.5.3",
    title: "Segregation of duties",
    frameworkCode: "iso27001",
    implemented: false,
    evidenceHashes: [],
    lastVerifiedAt: new Date().toISOString(),
  },
  {
    controlId: "ctrl-4",
    controlCode: "A.6.1",
    title: "Screen controls",
    frameworkCode: "iso27001",
    implemented: true,
    evidenceHashes: [],
    lastVerifiedAt: new Date().toISOString(),
    owner: "ops-team",
  },
];

const mockDetector: GapDetector = {
  async getControls(_frameworkCode: FrameworkCode): Promise<ControlRecord[]> {
    return mockControls;
  },
};

const emptyDetector: GapDetector = {
  async getControls(): Promise<ControlRecord[]> {
    return [];
  },
};

// ─── Tests ────────────────────────────────────────────────────────────

describe("ACCMEngine", () => {
  describe("detectGaps", () => {
    it("should detect gaps in controls with missing evidence", async () => {
      const engine = new ACCMEngine(mockDetector, { tenantId: "test-tenant" });
      const gaps = await engine.detectGaps("iso27001");

      assert.equal(gaps.length, 3);
      assert.equal(gaps[0].controlCode, "A.5.1");
      assert.equal(gaps[0].severity, "critical");
      assert.ok(gaps[0].id.startsWith("gap-"));
    });

    it("should classify gaps by severity correctly", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");

      const gap1 = gaps.find((g) => g.controlCode === "A.5.1");
      const gap3 = gaps.find((g) => g.controlCode === "A.5.3");
      const gap4 = gaps.find((g) => g.controlCode === "A.6.1");

      assert.equal(gap1?.severity, "critical"); // not implemented, no evidence, has owner
      assert.equal(gap3?.severity, "critical"); // not implemented, no evidence, no owner
      assert.equal(gap4?.severity, "medium"); // implemented, no evidence
    });

    it("should return empty array when all controls are compliant", async () => {
      const engine = new ACCMEngine(emptyDetector);
      const gaps = await engine.detectGaps("iso27001");
      assert.equal(gaps.length, 0);
    });

    it("should mark auto-remediable gaps correctly", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");

      const gapWithOwner = gaps.find((g) => g.controlCode === "A.5.1");
      const gapWithoutOwner = gaps.find((g) => g.controlCode === "A.5.3");

      assert.equal(gapWithOwner?.autoRemediable, true);
      assert.equal(gapWithoutOwner?.autoRemediable, false);
    });
  });

  describe("createRemediationPlan", () => {
    it("should create a workflow with appropriate steps", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);

      assert.ok(workflow.id.startsWith("wf-"));
      assert.equal(workflow.gapId, gaps[0].id);
      assert.equal(workflow.status, "pending");
      assert.ok(workflow.steps.length >= 2);
      assert.equal(workflow.steps[0].action.type, "send_slack_notification");
      assert.equal(workflow.steps[1].action.type, "create_jira_ticket");
    });

    it("should include update_control_status step", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);

      const updateStep = workflow.steps.find((s) => s.action.type === "update_control_status");
      assert.ok(updateStep);
      assert.equal(updateStep.action.params.status, "in_progress");
    });

    it("should not create Jira ticket for low severity gaps", async () => {
      const engine = new ACCMEngine(mockDetector);
      const lowSeverityGap = {
        id: "gap-low",
        tenantId: "test",
        frameworkCode: "iso27001" as FrameworkCode,
        controlId: "ctrl-low",
        controlCode: "A.9.9",
        controlTitle: "Low priority",
        severity: "low" as const,
        detectedAt: new Date().toISOString(),
        description: "Low severity gap",
        missingEvidence: [],
        riskScore: 0.2,
        autoRemediable: true,
        metadata: {},
      };

      const workflow = engine.createRemediationPlan(lowSeverityGap);
      const jiraStep = workflow.steps.find((s) => s.action.type === "create_jira_ticket");
      assert.equal(jiraStep, undefined);
    });

    it("should include API endpoint step when metadata has apiEndpoint", async () => {
      const engine = new ACCMEngine(mockDetector);
      const apiGap = {
        id: "gap-api",
        tenantId: "test",
        frameworkCode: "iso27001" as FrameworkCode,
        controlId: "ctrl-api",
        controlCode: "A.8.1",
        controlTitle: "API control",
        severity: "high" as const,
        detectedAt: new Date().toISOString(),
        description: "Needs API remediation",
        missingEvidence: ["primary_evidence"],
        riskScore: 0.8,
        autoRemediable: true,
        metadata: { apiEndpoint: "https://api.example.com/remediate" },
      };

      const workflow = engine.createRemediationPlan(apiGap);
      const apiStep = workflow.steps.find((s) => s.action.type === "call_api_endpoint");
      assert.ok(apiStep);
      assert.equal(apiStep.action.params.url, "https://api.example.com/remediate");
    });
  });

  describe("executeRemediation", () => {
    it("should execute all steps in a workflow", async () => {
      const engine = new ACCMEngine(mockDetector, { tenantId: "test-tenant" });
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);

      const result = await engine.executeRemediation(workflow);

      assert.equal(result.success, true);
      assert.ok(result.actionsExecuted >= 2);
      assert.equal(result.actionsFailed, 0);
      assert.equal(workflow.status, "completed");
      assert.ok(result.durationMs >= 0);
    });

    it("should handle executor failures gracefully", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);

      // Register a failing executor
      engine.registerExecutor("send_slack_notification", {
        async execute() {
          throw new Error("Slack API down");
        },
      });

      const result = await engine.executeRemediation(workflow);

      assert.equal(result.success, false);
      assert.ok(result.actionsFailed > 0);
    });

    it("should retry actions when retryable", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);

      let attempts = 0;
      engine.registerExecutor("send_slack_notification", {
        async execute() {
          attempts++;
          if (attempts < 2) throw new Error("Temporary failure");
          return { sent: true, attempt: attempts };
        },
      });

      const result = await engine.executeRemediation(workflow);
      assert.equal(result.success, true);
      assert.equal(attempts, 2);
    });
  });

  describe("verifyRemediation", () => {
    it("should report gap_closed when control is now compliant", async () => {
      // Create a detector that returns compliant control on second call
      let callCount = 0;
      const dynamicDetector: GapDetector = {
        async getControls(): Promise<ControlRecord[]> {
          callCount++;
          if (callCount === 1) {
            return [{ ...mockControls[0], implemented: false, evidenceHashes: [] }];
          }
          return [{ ...mockControls[0], implemented: true, evidenceHashes: ["evidence-1"] }];
        },
      };

      const engine = new ACCMEngine(dynamicDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);
      await engine.executeRemediation(workflow);

      const verification = await engine.verifyRemediation(workflow);
      assert.equal(verification.outcome, "gap_closed");
      assert.equal(verification.residualRisk, 0);
      assert.ok(verification.evidencePresent.length > 0);
    });

    it("should report gap_persists when control is still non-compliant", async () => {
      const staticDetector: GapDetector = {
        async getControls(): Promise<ControlRecord[]> {
          return [{ ...mockControls[0], implemented: false, evidenceHashes: [] }];
        },
      };

      const engine = new ACCMEngine(staticDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);
      await engine.executeRemediation(workflow);

      const verification = await engine.verifyRemediation(workflow);
      assert.equal(verification.outcome, "gap_persists");
      assert.ok(verification.residualRisk > 0);
      assert.ok(verification.recommendation.includes("Escalation"));
    });

    it("should track verification history", async () => {
      const engine = new ACCMEngine(mockDetector);
      const gaps = await engine.detectGaps("iso27001");
      const workflow = engine.createRemediationPlan(gaps[0]);
      await engine.executeRemediation(workflow);

      await engine.verifyRemediation(workflow);
      await engine.verifyRemediation(workflow);

      const history = engine.getVerificationResults(gaps[0].id);
      assert.equal(history.length, 2);
    });
  });

  describe("fullCycle", () => {
    it("should run the complete detect-remediate-verify cycle", async () => {
      const engine = new ACCMEngine(mockDetector, { tenantId: "test-tenant" });
      const report = await engine.fullCycle("iso27001");

      assert.ok(report.id.startsWith("report-"));
      assert.equal(report.tenantId, "test-tenant");
      assert.equal(report.frameworkCode, "iso27001");
      assert.equal(report.gapsDetected, 3);
      assert.ok(report.workflowsCreated >= 3);
      assert.ok(report.completedAt >= report.startedAt);
      assert.ok(typeof report.overallResidualRisk === "number");
      assert.ok(report.summary.includes("iso27001"));
    });

    it("should produce empty report when no gaps exist", async () => {
      const engine = new ACCMEngine(emptyDetector);
      const report = await engine.fullCycle("iso27001");

      assert.equal(report.gapsDetected, 0);
      assert.equal(report.workflowsCreated, 0);
      assert.equal(report.overallResidualRisk, 0);
    });

    it("should skip remediation for non-remediable gaps", async () => {
      const nonRemediableDetector: GapDetector = {
        async getControls(): Promise<ControlRecord[]> {
          return [{
            controlId: "ctrl-nr",
            controlCode: "A.9.9",
            title: "Non-remediable",
            frameworkCode: "iso27001",
            implemented: false,
            evidenceHashes: [],
            lastVerifiedAt: new Date().toISOString(),
            // no owner => not auto-remediable
          }];
        },
      };

      const engine = new ACCMEngine(nonRemediableDetector, { autoRemediate: true });
      const report = await engine.fullCycle("iso27001");

      assert.equal(report.gapsDetected, 1);
      assert.equal(report.workflowsFailed, 1);
    });
  });

  describe("Action Executors", () => {
    it("JiraTicketExecutor should create a ticket", async () => {
      const executor = new JiraTicketExecutor();
      const result = await executor.execute(
        { type: "create_jira_ticket", label: "test", params: { project: "SEC" }, retryable: false, maxRetries: 0, timeoutMs: 5000 },
        { controlCode: "A.5.1" }
      );
      assert.ok(result.ticketKey);
      assert.ok(result.url);
    });

    it("SlackNotificationExecutor should send notification", async () => {
      const executor = new SlackNotificationExecutor();
      const result = await executor.execute(
        { type: "send_slack_notification", label: "test", params: { channel: "#test" }, retryable: false, maxRetries: 0, timeoutMs: 5000 },
        { controlCode: "A.5.1" }
      );
      assert.equal(result.sent, true);
      assert.equal(result.channel, "#test");
    });

    it("ApiEndpointExecutor should call API", async () => {
      const executor = new ApiEndpointExecutor();
      const result = await executor.execute(
        { type: "call_api_endpoint", label: "test", params: { url: "https://api.test.com", method: "POST" }, retryable: false, maxRetries: 0, timeoutMs: 5000 },
        {}
      );
      assert.equal(result.statusCode, 200);
    });

    it("ControlStatusExecutor should update status", async () => {
      const executor = new ControlStatusExecutor();
      const result = await executor.execute(
        { type: "update_control_status", label: "test", params: { controlId: "ctrl-1", status: "in_progress" }, retryable: false, maxRetries: 0, timeoutMs: 5000 },
        {}
      );
      assert.equal(result.newStatus, "in_progress");
    });
  });
});
