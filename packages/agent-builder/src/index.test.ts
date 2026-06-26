import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  AgentBuilder,
  ScanControlsExecutor,
  CheckEvidenceExecutor,
  AnalyzeRiskExecutor,
  GenerateReportExecutor,
  CreateFindingExecutor,
  SendNotificationExecutor,
  CreateTicketExecutor,
  UpdateStatusExecutor,
  PREBUILT_AGENTS,
} from "./index.js";
import type { AgentDefinition, Task, Action } from "./types.js";

// ─── Test Helpers ─────────────────────────────────────────────────────

function makeTestAgent(overrides: Partial<AgentDefinition> = {}): AgentDefinition {
  return {
    id: "test-agent",
    name: "Test Agent",
    description: "A test agent",
    version: "1.0.0",
    trigger: { type: "manual", config: { enabled: true } },
    tasks: [
      { id: "t1", type: "scan_controls", label: "Scan", params: {} },
      { id: "t2", type: "check_evidence", label: "Check", params: {}, dependsOn: ["t1"] },
    ],
    actions: [
      { id: "a1", type: "create_finding", label: "Find", params: { severity: "low" } },
    ],
    tags: ["test"],
    enabled: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

// ─── Tests ────────────────────────────────────────────────────────────

describe("AgentBuilder", () => {
  describe("createAgent", () => {
    it("should create an agent with a generated ID", () => {
      const builder = new AgentBuilder();
      const agent = builder.createAgent(makeTestAgent({ id: "" }));

      assert.ok(agent.id.startsWith("agent-"));
      assert.equal(agent.name, "Test Agent");
    });

    it("should preserve provided ID", () => {
      const builder = new AgentBuilder();
      const agent = builder.createAgent(makeTestAgent({ id: "my-agent" }));

      assert.equal(agent.id, "my-agent");
    });

    it("should reject agent without name", () => {
      const builder = new AgentBuilder();
      assert.throws(
        () => builder.createAgent(makeTestAgent({ name: "" })),
        /must have a name/
      );
    });

    it("should reject agent without trigger", () => {
      const builder = new AgentBuilder();
      assert.throws(
        () => builder.createAgent(makeTestAgent({ trigger: undefined as any })),
        /must have a trigger/
      );
    });

    it("should reject agent with invalid task dependency", () => {
      const builder = new AgentBuilder();
      assert.throws(
        () =>
          builder.createAgent(
            makeTestAgent({
              tasks: [{ id: "t1", type: "scan_controls", label: "Scan", params: {}, dependsOn: ["nonexistent"] }],
            })
          ),
        /depends on unknown task/
      );
    });

    it("should reject agent with invalid action dependency", () => {
      const builder = new AgentBuilder();
      assert.throws(
        () =>
          builder.createAgent(
            makeTestAgent({
              actions: [{ id: "a1", type: "create_finding", label: "Find", params: {}, dependsOn: ["nonexistent"] }],
            })
          ),
        /depends on unknown action/
      );
    });
  });

  describe("listAgents", () => {
    it("should return pre-built agents by default", () => {
      const builder = new AgentBuilder();
      const agents = builder.listAgents();

      assert.ok(agents.length >= 4);
      const names = agents.map((a) => a.name);
      assert.ok(names.includes("Policy Guardian"));
      assert.ok(names.includes("Control Assessment"));
      assert.ok(names.includes("Evidence Analyzer"));
      assert.ok(names.includes("Audit Readiness"));
    });

    it("should include custom agents", () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "custom-1", name: "Custom Agent" }));

      const agents = builder.listAgents();
      assert.ok(agents.some((a) => a.id === "custom-1"));
    });
  });

  describe("getAgent", () => {
    it("should return agent by ID", () => {
      const builder = new AgentBuilder();
      const agent = builder.createAgent(makeTestAgent({ id: "get-test" }));

      const found = builder.getAgent("get-test");
      assert.equal(found?.id, "get-test");
      assert.equal(found?.name, "Test Agent");
    });

    it("should return undefined for unknown ID", () => {
      const builder = new AgentBuilder();
      assert.equal(builder.getAgent("nonexistent"), undefined);
    });

    it("should return pre-built agents", () => {
      const builder = new AgentBuilder();
      const policyGuardian = builder.getAgent("agent-policy-guardian");

      assert.ok(policyGuardian);
      assert.equal(policyGuardian.name, "Policy Guardian");
      assert.equal(policyGuardian.trigger.type, "schedule");
    });
  });

  describe("deleteAgent", () => {
    it("should delete an existing agent", () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "to-delete" }));

      assert.equal(builder.deleteAgent("to-delete"), true);
      assert.equal(builder.getAgent("to-delete"), undefined);
    });

    it("should return false for unknown ID", () => {
      const builder = new AgentBuilder();
      assert.equal(builder.deleteAgent("nonexistent"), false);
    });
  });

  describe("triggerAgent", () => {
    it("should trigger a manual agent and complete", async () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "run-test" }));

      const run = await builder.triggerAgent("run-test", { tenantId: "t1" });

      assert.equal(run.status, "completed");
      assert.equal(run.agentId, "run-test");
      assert.ok(run.id.startsWith("run-"));
      assert.ok(run.summary.includes("completed"));
    });

    it("should execute tasks and actions in order", async () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "order-test" }));

      const run = await builder.triggerAgent("order-test");
      const workflow = builder.getWorkflow(run.workflowId);

      assert.ok(workflow);
      assert.equal(workflow.taskResults.length, 2);
      assert.equal(workflow.actionResults.length, 1);
      assert.equal(workflow.status, "completed");

      // Verify order: t1 completed before t2
      const t1Result = workflow.taskResults.find((r) => r.taskId === "t1");
      const t2Result = workflow.taskResults.find((r) => r.taskId === "t2");
      assert.equal(t1Result?.status, "completed");
      assert.equal(t2Result?.status, "completed");
    });

    it("should throw for unknown agent", async () => {
      const builder = new AgentBuilder();
      await assert.rejects(
        () => builder.triggerAgent("nonexistent"),
        /Agent not found/
      );
    });

    it("should throw for disabled agent", async () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "disabled", enabled: false }));

      await assert.rejects(
        () => builder.triggerAgent("disabled"),
        /Agent is disabled/
      );
    });

    it("should track run history", async () => {
      const builder = new AgentBuilder();
      builder.createAgent(makeTestAgent({ id: "history-test" }));

      await builder.triggerAgent("history-test");
      await builder.triggerAgent("history-test");

      const runs = builder.getAgentRuns("history-test");
      assert.equal(runs.length, 2);
    });
  });

  describe("Pre-built Agents", () => {
    it("Policy Guardian should have schedule trigger", () => {
      const agent = PREBUILT_AGENTS.find((a) => a.id === "agent-policy-guardian");
      assert.ok(agent);
      assert.equal(agent.trigger.type, "schedule");
      assert.ok(agent.tasks.length >= 3);
      assert.ok(agent.actions.length >= 2);
    });

    it("Control Assessment should have multiple frameworks", () => {
      const agent = PREBUILT_AGENTS.find((a) => a.id === "agent-control-assessment");
      assert.ok(agent);
      assert.deepEqual(agent.tasks[0].params.frameworks, ["iso27001", "soc2", "nist-csf"]);
    });

    it("Evidence Analyzer should have event trigger", () => {
      const agent = PREBUILT_AGENTS.find((a) => a.id === "agent-evidence-analyzer");
      assert.ok(agent);
      assert.equal(agent.trigger.type, "event");
      assert.equal(agent.trigger.config.eventName, "evidence.collected");
    });

    it("Audit Readiness should have manual trigger", () => {
      const agent = PREBUILT_AGENTS.find((a) => a.id === "agent-audit-readiness");
      assert.ok(agent);
      assert.equal(agent.trigger.type, "manual");
      assert.ok(agent.tasks.length >= 4);
    });
  });

  describe("Built-in Executors", () => {
    it("ScanControlsExecutor should return scan results", async () => {
      const executor = new ScanControlsExecutor();
      const result = await executor.execute(
        { id: "t1", type: "scan_controls", label: "Scan", params: { frameworks: "iso27001,soc2" } },
        {}
      );
      assert.ok(result.controlsScanned);
      assert.ok(result.controlsScanned > 0);
      assert.ok(Array.isArray(result.frameworks));
      assert.ok(result.frameworks.length >= 2);
    });

    it("CheckEvidenceExecutor should return evidence analysis", async () => {
      const executor = new CheckEvidenceExecutor();
      const result = await executor.execute(
        { id: "t1", type: "check_evidence", label: "Check", params: { freshnessDays: 30 } },
        {}
      );
      assert.ok(typeof result.completenessScore === "number");
      assert.ok(typeof result.totalEvidence === "number");
    });

    it("AnalyzeRiskExecutor should return risk assessment", async () => {
      const executor = new AnalyzeRiskExecutor();
      const result = await executor.execute(
        { id: "t1", type: "analyze_risk", label: "Risk", params: { model: "test" } },
        {}
      );
      assert.ok(typeof result.overallRisk === "number");
      assert.ok(Array.isArray(result.recommendations));
    });

    it("GenerateReportExecutor should generate report", async () => {
      const executor = new GenerateReportExecutor();
      const result = await executor.execute(
        { id: "t1", type: "generate_report", label: "Report", params: { format: "detailed" } },
        {}
      );
      assert.ok(result.reportId);
      assert.ok(Array.isArray(result.sections));
    });

    it("CreateFindingExecutor should create a finding", async () => {
      const executor = new CreateFindingExecutor();
      const result = await executor.execute(
        { id: "a1", type: "create_finding", label: "Find", params: { severity: "high" } },
        {}
      );
      assert.ok(result.findingId);
      assert.equal(result.severity, "high");
    });

    it("SendNotificationExecutor should send notification", async () => {
      const executor = new SendNotificationExecutor();
      const result = await executor.execute(
        { id: "a1", type: "send_notification", label: "Notify", params: { channel: "#test" } },
        {}
      );
      assert.equal(result.sent, true);
      assert.equal(result.channel, "#test");
    });

    it("CreateTicketExecutor should create ticket", async () => {
      const executor = new CreateTicketExecutor();
      const result = await executor.execute(
        { id: "a1", type: "create_ticket", label: "Ticket", params: { project: "SEC" } },
        {}
      );
      assert.ok(result.ticketKey);
      assert.equal(result.project, "SEC");
    });

    it("UpdateStatusExecutor should update status", async () => {
      const executor = new UpdateStatusExecutor();
      const result = await executor.execute(
        { id: "a1", type: "update_status", label: "Update", params: { field: "status", value: "done" } },
        {}
      );
      assert.ok(result.updatedAt);
    });
  });

  describe("Topological Sort", () => {
    it("should execute tasks in dependency order even when defined out of order", async () => {
      const builder = new AgentBuilder();
      const order: string[] = [];

      builder.registerTaskExecutor("scan_controls", {
        async execute(task) {
          order.push(task.id);
          return {};
        },
      });
      builder.registerTaskExecutor("check_evidence", {
        async execute(task) {
          order.push(task.id);
          return {};
        },
      });

      builder.createAgent({
        id: "sort-test",
        name: "Sort Test",
        description: "Test",
        version: "1.0.0",
        trigger: { type: "manual", config: {} },
        tasks: [
          { id: "t3", type: "check_evidence", label: "3", params: {}, dependsOn: ["t2"] },
          { id: "t1", type: "scan_controls", label: "1", params: {} },
          { id: "t2", type: "check_evidence", label: "2", params: {}, dependsOn: ["t1"] },
        ],
        actions: [],
        tags: [],
        enabled: true,
        createdAt: "",
        updatedAt: "",
      });

      await builder.triggerAgent("sort-test");
      assert.deepEqual(order, ["t1", "t2", "t3"]);
    });
  });
});
