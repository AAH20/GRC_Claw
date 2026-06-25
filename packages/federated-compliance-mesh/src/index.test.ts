import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { FederatedComplianceMesh } from "./index.js";

describe("FederatedComplianceMesh", () => {
  it("should register organization", () => {
    const mesh = new FederatedComplianceMesh();
    mesh.registerOrganization({
      id: "org-1",
      name: "Test Org",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      relationships: ["parent"],
      trustLevel: 0.9,
      status: "active",
    });

    const orgs = mesh.getOrganizations();
    assert.equal(orgs.length, 1);
    assert.equal(orgs[0].id, "org-1");
  });

  it("should get mesh stats", () => {
    const mesh = new FederatedComplianceMesh();
    mesh.registerOrganization({
      id: "org-1",
      name: "Org 1",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      relationships: ["parent"],
      trustLevel: 0.9,
      status: "active",
    });

    mesh.registerOrganization({
      id: "org-2",
      name: "Org 2",
      jurisdictions: ["us"],
      frameworks: ["soc2"],
      parentId: "org-1",
      relationships: ["subsidiary"],
      trustLevel: 0.8,
      status: "active",
    });

    const stats = mesh.getMeshStats();
    assert.equal(stats.totalOrgs, 2);
    assert.equal(stats.activeOrgs, 2);
    assert.equal(stats.totalConnections, 2);
  });

  it("should generate compliance report", () => {
    const mesh = new FederatedComplianceMesh();
    const controlScores = new Map([["A.5.1", 90], ["A.6.1", 75]]);

    const report = mesh.generateRegulatoryReport("org-1", "eu", "iso27001", controlScores);
    assert.equal(report.orgId, "org-1");
    assert.equal(report.jurisdiction, "eu");
    assert.equal(report.frameworkCode, "iso27001");
  });

  it("should generate gap analysis", () => {
    const mesh = new FederatedComplianceMesh();
    const controlScores = new Map([["A.5.1", 90], ["A.6.1", 50]]);

    const gap = mesh.generateGapAnalysis("org-1", "eu", "iso27001", controlScores, 80);
    assert.equal(gap.reportType, "gap_analysis");
  });

  it("should find path between organizations", () => {
    const mesh = new FederatedComplianceMesh();
    mesh.registerOrganization({
      id: "org-1",
      name: "Parent",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      relationships: ["parent"],
      trustLevel: 0.9,
      status: "active",
    });
    mesh.registerOrganization({
      id: "org-2",
      name: "Sub",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      parentId: "org-1",
      relationships: ["subsidiary"],
      trustLevel: 0.8,
      status: "active",
    });

    const path = mesh.findPath("org-1", "org-2");
    assert.ok(path);
    assert.deepEqual(path, ["org-1", "org-2"]);
  });

  it("should return applicable frameworks for jurisdiction", () => {
    const mesh = new FederatedComplianceMesh();
    const frameworks = mesh.getApplicableFrameworks("eu");
    assert.ok(frameworks.includes("iso27001"));
    assert.ok(frameworks.includes("gdpr"));
  });
});

describe("ComplianceMeshNetwork", () => {
  it("should propagate compliance updates", async () => {
    const { ComplianceMeshNetwork } = await import("./mesh/ComplianceMeshNetwork.js");
    const network = new ComplianceMeshNetwork();

    network.registerOrganization({
      id: "org-1",
      name: "Org 1",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      relationships: ["parent"],
      trustLevel: 0.9,
      status: "active",
    });

    network.registerOrganization({
      id: "org-2",
      name: "Org 2",
      jurisdictions: ["eu"],
      frameworks: ["iso27001"],
      parentId: "org-1",
      relationships: ["subsidiary"],
      trustLevel: 0.8,
      status: "active",
    });

    const events = network.propagateComplianceUpdate("org-1", "iso27001", {
      orgId: "org-1",
      frameworkCode: "iso27001",
      overallScore: 85,
      controlScores: new Map(),
      lastUpdated: new Date().toISOString(),
      evidenceHashes: new Map(),
    });

    assert.equal(events.length, 1);
    assert.equal(events[0].propagatedTo.length, 1);
  });
});
