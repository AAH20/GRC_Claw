import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { VendorRiskManagement } from "./VendorRiskManagement.js";

describe("VendorRiskManagement", () => {
  const vrm = new VendorRiskManagement();

  it("should create a vendor", () => {
    const vendor = vrm.createVendor({
      name: "Acme Corp",
      domain: "acme.com",
      description: "Cloud services provider",
      categories: ["cloud", "saas"],
    });
    assert.equal(vendor.status, "prospect");
    assert.equal(vendor.name, "Acme Corp");
  });

  it("should onboard a vendor", () => {
    const vendor = vrm.createVendor({
      name: "Vendor Onboard",
      domain: "onboard.com",
      description: "Test",
      categories: ["it"],
    });

    const onboarded = vrm.onboardVendor(vendor.id);
    assert.equal(onboarded.status, "onboarding");
    assert.ok(onboarded.onboardedAt);

    const monitoring = vrm.getMonitoring(vendor.id);
    assert.ok(monitoring);
    assert.equal(monitoring.enabled, true);
  });

  it("should add contacts and documents", () => {
    const vendor = vrm.createVendor({
      name: "Contact Test",
      domain: "contact.com",
      description: "Test",
      categories: ["it"],
    });

    const contact = vrm.addContact(vendor.id, {
      name: "John Doe",
      email: "john@contact.com",
      role: "Security Lead",
      isPrimary: true,
    });
    assert.ok(contact.id);

    const doc = vrm.addDocument(vendor.id, {
      type: "soc2",
      name: "SOC 2 Report 2024",
      url: "https://example.com/soc2.pdf",
      sha256: "abc123",
    });
    assert.ok(doc.id);
    assert.equal(doc.type, "soc2");
  });

  it("should calculate 4-factor risk score", () => {
    const vendor = vrm.createVendor({
      name: "Risk Test Vendor",
      domain: "risk.com",
      description: "Test",
      categories: ["security"],
    });

    const score = vrm.calculateRiskScore(vendor.id, [
      { category: "cybersecurity", name: "Firewall", score: 85, weight: 0.4, evidence: "Verified", details: "Enterprise firewall" },
      { category: "cybersecurity", name: "MFA", score: 90, weight: 0.6, evidence: "Verified", details: "MFA enforced" },
      { category: "compliance", name: "SOC 2", score: 80, weight: 0.5, evidence: "Report", details: "SOC 2 Type II" },
      { category: "compliance", name: "ISO 27001", score: 75, weight: 0.5, evidence: "Cert", details: "Certified" },
      { category: "operational", name: "SLA", score: 70, weight: 1.0, evidence: "Contract", details: "99.9% uptime" },
      { category: "financial", name: "Revenue", score: 85, weight: 1.0, evidence: "Financials", details: "Stable" },
    ]);

    assert.ok(score.overallScore > 0);
    assert.ok(score.overallScore <= 100);
    assert.ok(score.tier);
    assert.equal(score.factors.length, 6);
  });

  it("should have SIG Lite, CAIQ, and Custom templates", () => {
    const templates = vrm.getQuestionnaireTemplates();
    assert.ok(templates.length >= 3);

    const sigLite = vrm.getQuestionnaireByType("sig_lite");
    assert.ok(sigLite.length >= 1);

    const caiq = vrm.getQuestionnaireByType("caiq");
    assert.ok(caiq.length >= 1);

    const custom = vrm.getQuestionnaireByType("custom");
    assert.ok(custom.length >= 1);
  });

  it("should create and complete assessment", () => {
    const vendor = vrm.createVendor({
      name: "Assessment Test",
      domain: "assess.com",
      description: "Test",
      categories: ["it"],
    });

    const templates = vrm.getQuestionnaireTemplates();
    const sigLite = templates.find((t) => t.type === "sig_lite")!;

    const assessment = vrm.createAssessment(vendor.id, sigLite.id);
    assert.equal(assessment.status, "pending");

    const responses: Record<string, string> = {};
    for (const q of sigLite.questions) {
      responses[q.id] = q.type === "boolean" ? "true" : "Test response";
    }

    const completed = vrm.submitAssessmentResponse(assessment.id, responses);
    assert.equal(completed.status, "completed");
    assert.ok(completed.completedAt);
  });

  it("should manage risk register", () => {
    const vendor = vrm.createVendor({
      name: "Register Test",
      domain: "register.com",
      description: "Test",
      categories: ["it"],
    });

    const entry = vrm.addRiskRegisterEntry(vendor.id, {
      description: "Data breach risk",
      category: "cybersecurity",
      likelihood: 3,
      impact: 4,
      mitigations: ["Encryption", "Monitoring"],
      owner: "CISO",
    });

    assert.equal(entry.riskScore, 12);
    assert.equal(entry.status, "open");

    const updated = vrm.updateRiskRegisterEntry(vendor.id, entry.id, { status: "mitigated" });
    assert.equal(updated?.status, "mitigated");

    const register = vrm.getRiskRegister(vendor.id);
    assert.equal(register.length, 1);
  });

  it("should return dashboard data", () => {
    vrm.createVendor({
      name: "Dashboard Vendor",
      domain: "dash.com",
      description: "Test",
      categories: ["it"],
    });

    const dashboard = vrm.getDashboard();
    assert.ok(dashboard.totalVendors > 0);
    assert.ok(typeof dashboard.byTier === "object");
    assert.ok(typeof dashboard.byStatus === "object");
  });

  it("should search vendors", () => {
    vrm.createVendor({
      name: "Searchable Cloud Corp",
      domain: "searchable.com",
      description: "Cloud services",
      categories: ["cloud"],
    });

    const results = vrm.searchVendors({ query: "searchable" });
    assert.ok(results.length >= 1);
    assert.ok(results.some((v) => v.name === "Searchable Cloud Corp"));
  });

  it("should manage alerts", () => {
    const vendor = vrm.createVendor({
      name: "Alert Test",
      domain: "alert.com",
      description: "Test",
      categories: ["it"],
    });

    const alert = vrm.addAlert(vendor.id, "breach_detected", "critical", "Data breach detected");
    assert.equal(alert.acknowledged, false);

    vrm.acknowledgeAlert(alert.id, "admin");
    const activeAlerts = vrm.getActiveAlerts();
    assert.ok(!activeAlerts.some((a) => a.id === alert.id));
  });
});
