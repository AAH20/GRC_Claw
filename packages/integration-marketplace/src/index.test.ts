import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { IntegrationMarketplace } from "./IntegrationMarketplace.js";
import type { IntegrationConnector, ConnectorConfig, EvidenceArtifact } from "./types.js";

class MockConnector implements IntegrationConnector {
  readonly id: string;
  readonly name: string;
  readonly category = "version_control" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = [
    { id: "test-cap", name: "Test Capability", description: "Test", evidenceCategories: ["test"] },
  ];
  readonly frameworks = ["SOC2" as const];

  private shouldFail = false;

  constructor(id: string, name: string, fail = false) {
    this.id = id;
    this.name = name;
    this.shouldFail = fail;
  }

  async collectEvidence(): Promise<EvidenceArtifact[]> {
    if (this.shouldFail) throw new Error("Mock failure");
    return [
      {
        id: `ev-${this.id}-1`,
        connectorId: this.id,
        capabilityId: "test-cap",
        timestamp: new Date().toISOString(),
        hash: "sha256:abc123",
        framework: "SOC2",
        controlId: "CC6.1",
        source: `mock/${this.id}`,
        status: "compliant",
        data: { test: true },
        metadata: {},
      },
    ];
  }

  async testConnection(): Promise<boolean> {
    return !this.shouldFail;
  }
}

const mockConfig: ConnectorConfig = { apiToken: "test-token" };

describe("IntegrationMarketplace", () => {
  it("should register 25 built-in connectors", () => {
    const marketplace = new IntegrationMarketplace();
    const stats = marketplace.getStats();
    assert.equal(stats.totalConnectors, 25);
    assert.ok(stats.totalCapabilities > 25);
  });

  it("should register a custom connector", () => {
    const marketplace = new IntegrationMarketplace();
    const custom = new MockConnector("custom-1", "Custom Tool");
    marketplace.registerConnector(custom);
    assert.ok(marketplace.getConnector("custom-1"));
  });

  it("should unregister a connector", () => {
    const marketplace = new IntegrationMarketplace();
    const custom = new MockConnector("custom-1", "Custom Tool");
    marketplace.registerConnector(custom);
    assert.ok(marketplace.unregisterConnector("custom-1"));
    assert.equal(marketplace.getConnector("custom-1"), undefined);
  });

  it("should enable/disable connectors", () => {
    const marketplace = new IntegrationMarketplace();
    marketplace.disableConnector("github");
    assert.equal(marketplace.getEnabledConnectors().length, 24);
    marketplace.enableConnector("github");
    assert.equal(marketplace.getEnabledConnectors().length, 25);
  });

  it("should filter connectors by category", () => {
    const marketplace = new IntegrationMarketplace();
    const cloudProviders = marketplace.getConnectorsByCategory("cloud_provider");
    assert.ok(cloudProviders.length >= 4);
    assert.ok(cloudProviders.every((c) => c.category === "cloud_provider"));
  });

  it("should filter connectors by framework", () => {
    const marketplace = new IntegrationMarketplace();
    const hipaaConnectors = marketplace.getConnectorsByFramework("HIPAA");
    assert.ok(hipaaConnectors.length >= 2);
    assert.ok(hipaaConnectors.every((c) => c.frameworks.includes("HIPAA")));
  });

  it("should collect from a custom connector", async () => {
    const marketplace = new IntegrationMarketplace();
    const custom = new MockConnector("custom-1", "Custom Tool");
    marketplace.registerConnector(custom);
    marketplace.setConfig("custom-1", mockConfig);

    const job = await marketplace.collectFromConnector("custom-1");
    assert.equal(job.status, "completed");
    assert.equal(job.artifacts.length, 1);
    assert.equal(job.connectorId, "custom-1");
  });

  it("should handle collection failures gracefully", async () => {
    const marketplace = new IntegrationMarketplace();
    const failing = new MockConnector("fail-1", "Failing Tool", true);
    marketplace.registerConnector(failing);
    marketplace.setConfig("fail-1", mockConfig);

    const job = await marketplace.collectFromConnector("fail-1");
    assert.equal(job.status, "failed");
    assert.ok(job.error);
  });

  it("should return stats correctly", () => {
    const marketplace = new IntegrationMarketplace();
    const stats = marketplace.getStats();
    assert.equal(stats.totalConnectors, 25);
    assert.ok(Object.keys(stats.connectorsByCategory).length > 0);
    assert.ok(stats.frameworksSupported.length > 0);
  });

  it("should track jobs", async () => {
    const marketplace = new IntegrationMarketplace();
    const custom = new MockConnector("custom-1", "Custom Tool");
    marketplace.registerConnector(custom);
    marketplace.setConfig("custom-1", mockConfig);

    await marketplace.collectFromConnector("custom-1");
    const jobs = marketplace.getJobs();
    assert.equal(jobs.length, 1);
    assert.equal(jobs[0].status, "completed");
  });

  it("should throw on collect from missing connector", async () => {
    const marketplace = new IntegrationMarketplace();
    await assert.rejects(
      () => marketplace.collectFromConnector("nonexistent"),
      /Connector not found/
    );
  });

  it("should throw on collect without config", async () => {
    const marketplace = new IntegrationMarketplace();
    const custom = new MockConnector("custom-1", "Custom Tool");
    marketplace.registerConnector(custom);
    await assert.rejects(
      () => marketplace.collectFromConnector("custom-1"),
      /No config/
    );
  });

  it("should test connections for enabled connectors", async () => {
    const marketplace = new IntegrationMarketplace();
    marketplace.registerConnector(new MockConnector("m1", "Mock1"));
    marketplace.registerConnector(new MockConnector("m2", "Mock2", true));
    marketplace.setConfig("m1", mockConfig);
    marketplace.setConfig("m2", mockConfig);

    const results = await marketplace.testAllConnections();
    assert.equal(results.get("m1"), true);
    assert.equal(results.get("m2"), false);
  });
});
