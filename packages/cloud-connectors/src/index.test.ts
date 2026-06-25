import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { CloudConnectorRegistry } from "./index.js";

describe("CloudConnectorRegistry", () => {
  it("should register and retrieve connectors", () => {
    const registry = new CloudConnectorRegistry();
    const mockConnector = {
      provider: "aws" as const,
      async health() { return { provider: "aws" as const, status: "connected" as const, findingCount: 0, errorCount: 0 }; },
      async fetchFindings() { return []; },
      async testConnection() { return true; },
    };

    registry.register(mockConnector);
    assert.ok(registry.get("aws"));
    assert.equal(registry.list().length, 1);
  });

  it("should fetch all findings from registered connectors", async () => {
    const registry = new CloudConnectorRegistry();
    const mockConnector = {
      provider: "aws" as const,
      async health() { return { provider: "aws" as const, status: "connected" as const, findingCount: 1, errorCount: 0 }; },
      async fetchFindings() {
        return [{ id: "test-1", provider: "aws" as const, service: "ec2", severity: "high" as const, title: "Test", description: "Test", resourceId: "arn:test", resourceType: "instance", region: "us-east-1", detectedAt: new Date().toISOString(), metadata: {} }];
      },
      async testConnection() { return true; },
    };

    registry.register(mockConnector);
    const findings = await registry.fetchAllFindings();
    assert.equal(findings.length, 1);
    assert.equal(findings[0].provider, "aws");
  });

  it("should generate health report", async () => {
    const registry = new CloudConnectorRegistry();
    const mockConnector = {
      provider: "azure" as const,
      async health() { return { provider: "azure" as const, status: "connected" as const, findingCount: 5, errorCount: 0 }; },
      async fetchFindings() { return []; },
      async testConnection() { return true; },
    };

    registry.register(mockConnector);
    const report = await registry.getHealthReport();
    assert.equal(report.length, 1);
    assert.equal(report[0].provider, "azure");
  });
});
