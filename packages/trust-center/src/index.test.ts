import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { TrustCenter } from "./portal/TrustCenter.js";
import { SecurityQuestionnaireResponder } from "./portal/SecurityQuestionnaireResponder.js";

describe("TrustCenter", () => {
  it("should create and publish trust page", () => {
    const tc = new TrustCenter();
    const page = tc.createPage("acme", "Acme Corp");
    assert.ok(page.id);
    tc.addItem(page.id, { type: "certification", name: "SOC 2 Type II", description: "Certified", status: "active", summary: "SOC 2 certified", order: 1 });
    assert.ok(tc.publishPage(page.id));
    const json = tc.generatePublicJson(page.id);
    assert.ok(json);
    assert.equal((json.trustItems as unknown[]).length, 1);
  });

  it("should update item status", () => {
    const tc = new TrustCenter();
    const page = tc.createPage("t", "Test");
    const item = tc.addItem(page.id, { type: "audit_report", name: "Report", description: "Test", status: "active", summary: "Test", order: 1 });
    assert.ok(item);
    assert.ok(tc.updateItemStatus(page.id, item.id, "expired"));
  });
});

describe("SecurityQuestionnaireResponder", () => {
  it("should answer security questions", () => {
    const responder = new SecurityQuestionnaireResponder();
    const answer = responder.answerQuestion("Do you encrypt data at rest?");
    assert.ok(answer.response.includes("AES-256"));
    assert.ok(answer.autoAnswered);
  });

  it("should bulk answer questions", () => {
    const responder = new SecurityQuestionnaireResponder();
    const answers = responder.bulkAnswer(["Do you use MFA?", "What is your SOC2 status?", "How do you handle logging?"]);
    const stats = responder.getCompletionRate(answers);
    assert.ok(stats.rate > 0);
  });
});
