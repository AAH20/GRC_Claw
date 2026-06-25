import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { AutoEvidenceCollector } from "./collectors/AutoEvidenceCollector.js";

describe("AutoEvidenceCollector", () => {
  it("should connect provider and deploy collectors", () => {
    const collector = new AutoEvidenceCollector();
    collector.connectProvider("aws", "123456789012", ["us-east-1", "us-west-2"]);
    const deployed = collector.autoDeployCollectors("aws");
    assert.ok(deployed.length > 0);
    assert.equal(deployed[0].provider, "aws");
  });

  it("should collect evidence", () => {
    const collector = new AutoEvidenceCollector();
    collector.connectProvider("aws", "123456789012", ["us-east-1"]);
    const c = collector.createCollector("aws", "iam", "A.9.2.1", "daily");
    const evidence = collector.collectEvidence(c.id);
    assert.ok(evidence);
    assert.ok(evidence.sha256);
    assert.equal(evidence.type, "configuration");
  });

  it("should get inventory", () => {
    const collector = new AutoEvidenceCollector();
    collector.connectProvider("azure", "sub-1", ["eastus"]);
    collector.autoDeployCollectors("azure");
    const inv = collector.getInventory();
    assert.ok(inv.totalEvidence >= 0);
  });

  it("should list all templates", () => {
    const collector = new AutoEvidenceCollector();
    assert.ok(collector.getTemplates().length >= 15);
  });
});
