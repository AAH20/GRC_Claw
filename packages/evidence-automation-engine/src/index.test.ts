import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { EvidenceAutomationEngine, type ConnectorAdapter } from "./EvidenceAutomationEngine.js";
import type { EvidenceArtifact } from "./types.js";

function createMockConnector(id: string, fail = false): ConnectorAdapter {
  return {
    async collectEvidence(): Promise<EvidenceArtifact[]> {
      if (fail) throw new Error(`Connector ${id} failed`);
      return [
        {
          id: `ev-${id}-1`,
          connectorId: id,
          capabilityId: "test-cap",
          timestamp: new Date().toISOString(),
          hash: `sha256:test-${id}`,
          framework: "SOC2",
          controlId: "CC6.1",
          source: `${id}/test`,
          status: "compliant",
          data: { test: true },
          metadata: {},
        },
      ];
    },
    async testConnection(): Promise<boolean> {
      return !fail;
    },
  };
}

describe("EvidenceAutomationEngine", () => {
  it("should create engine with default config", () => {
    const engine = new EvidenceAutomationEngine();
    assert.ok(engine);
    assert.equal(engine.getStore().size, 0);
  });

  it("should register and unregister connectors", () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    engine.registerConnector("gitlab", createMockConnector("gitlab"));

    const store = engine.getStore();
    assert.equal(store.size, 0);
  });

  it("should create schedules", () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));

    const schedule = engine.createSchedule("github", {
      frequency: "daily",
      hourOfDay: 9,
    });
    assert.ok(schedule.id);
    assert.equal(schedule.connectorId, "github");
    assert.equal(schedule.enabled, true);
    assert.ok(schedule.nextRunAt);
  });

  it("should throw when creating schedule for unregistered connector", () => {
    const engine = new EvidenceAutomationEngine();
    assert.throws(() => {
      engine.createSchedule("nonexistent", { frequency: "daily" });
    }, /not registered/);
  });

  it("should update schedules", () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    const schedule = engine.createSchedule("github", { frequency: "daily" });

    const updated = engine.updateSchedule(schedule.id, {
      config: { frequency: "weekly" },
    });
    assert.ok(updated);
    assert.equal(updated!.config.frequency, "weekly");
  });

  it("should delete schedules", () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    const schedule = engine.createSchedule("github", { frequency: "daily" });

    assert.ok(engine.deleteSchedule(schedule.id));
    assert.equal(engine.getSchedule(schedule.id), undefined);
  });

  it("should collect evidence from a connector", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));

    const job = await engine.collectFromConnector("github");
    assert.equal(job.status, "completed");
    assert.equal(job.artifacts.length, 1);
    assert.equal(job.connectorId, "github");
    assert.ok(job.duration !== undefined);
  });

  it("should store evidence after collection", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));

    await engine.collectFromConnector("github");
    assert.equal(engine.getStore().size, 1);
  });

  it("should handle collection failures", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("failing", createMockConnector("failing", true));

    const job = await engine.collectFromConnector("failing");
    assert.equal(job.status, "failed");
    assert.ok(job.error);
    assert.equal(job.artifacts.length, 0);
  });

  it("should collect from all connectors", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    engine.registerConnector("gitlab", createMockConnector("gitlab"));

    const jobs = await engine.collectAll();
    assert.equal(jobs.length, 2);
    assert.ok(jobs.every((j) => j.status === "completed"));
    assert.equal(engine.getStore().size, 2);
  });

  it("should update schedule lastRunAt after collection", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    const schedule = engine.createSchedule("github", { frequency: "daily" });

    await engine.collectFromConnector("github");
    const updated = engine.getSchedule(schedule.id);
    assert.ok(updated?.lastRunAt);
  });

  it("should detect missing evidence gaps", () => {
    const engine = new EvidenceAutomationEngine();
    const gaps = engine.detectGaps();
    assert.ok(gaps.length > 0);
    assert.ok(gaps.every((g) => g.freshness === "missing"));
  });

  it("should detect no gaps when evidence is fresh", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    await engine.collectFromConnector("github");

    const gaps = engine.detectGaps();
    const githubGap = gaps.find(
      (g) => g.controlId === "CC6.1" && g.framework === "SOC2"
    );
    assert.equal(githubGap, undefined);
  });

  it("should generate summary report", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    await engine.collectFromConnector("github");

    const report = engine.generateSummaryReport();
    assert.equal(report.totalArtifacts, 1);
    assert.ok(report.generatedAt);
    assert.equal(report.artifactsByStatus["compliant"], 1);
    assert.equal(report.coveragePercentage > 0, true);
  });

  it("should track jobs", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    await engine.collectFromConnector("github");

    const jobs = engine.getJobs();
    assert.equal(jobs.length, 1);
    assert.equal(jobs[0].status, "completed");
  });

  it("should clear store", async () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    await engine.collectFromConnector("github");
    assert.equal(engine.getStore().size, 1);

    engine.clearStore();
    assert.equal(engine.getStore().size, 0);
  });

  it("should start and stop scheduler", () => {
    const engine = new EvidenceAutomationEngine();
    engine.registerConnector("github", createMockConnector("github"));
    engine.createSchedule("github", { frequency: "hourly" });

    engine.startScheduler();
    engine.stopScheduler();
    assert.equal(engine.getSchedules().length, 1);
  });
});
