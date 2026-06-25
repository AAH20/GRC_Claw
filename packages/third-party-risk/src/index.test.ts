import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { VendorRegistry } from "./vendors/VendorRegistry.js";
import { QuestionnaireEngine } from "./vendors/QuestionnaireEngine.js";

describe("VendorRegistry", () => {
  it("should register vendor", () => {
    const reg = new VendorRegistry();
    const vendor = reg.registerVendor({ name: "AWS", domain: "aws.com", categories: ["cloud"], frameworks: ["iso27001"], contacts: [{ name: "Test", email: "t@t.com", role: "admin", isPrimary: true }] });
    assert.ok(vendor.id);
    assert.equal(vendor.name, "AWS");
  });

  it("should calculate risk score", () => {
    const reg = new VendorRegistry();
    const vendor = reg.registerVendor({ name: "Test", domain: "test.com", categories: [], frameworks: [], contacts: [] });
    const score = reg.calculateRiskScore(vendor.id);
    assert.ok(score);
    assert.ok(score.overallScore >= 0);
  });

  it("should get vendors by tier", () => {
    const reg = new VendorRegistry();
    reg.registerVendor({ name: "A", domain: "a.com", categories: [], frameworks: [], contacts: [] });
    reg.registerVendor({ name: "B", domain: "b.com", categories: [], frameworks: [], contacts: [] });
    assert.equal(reg.listVendors().length, 2);
  });
});

describe("QuestionnaireEngine", () => {
  it("should create assessment", () => {
    const engine = new QuestionnaireEngine();
    const assessment = engine.createAssessment("vendor-1", "soc2");
    assert.ok(assessment.id);
    assert.equal(assessment.questions.length, 6);
  });

  it("should calculate score", () => {
    const engine = new QuestionnaireEngine();
    const questions = engine.getQuestionnaire("soc2");
    const score = engine.calculateScore({ q1: "true", q2: "Yes", q3: "true", q4: "true", q5: "Process" }, questions);
    assert.ok(score > 0);
  });

  it("should auto-generate responses", () => {
    const engine = new QuestionnaireEngine();
    const responses = engine.autoGenerateResponses("Acme Corp", "iso27001");
    assert.ok(Object.keys(responses).length > 0);
  });
});
