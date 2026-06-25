import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { QuestionnaireKnowledgeBase } from "./automation/KnowledgeBase.js";
import { QuestionnaireAutomation } from "./automation/QuestionnaireAutomation.js";

describe("QuestionnaireKnowledgeBase", () => {
  it("should match questions to knowledge base", () => {
    const kb = new QuestionnaireKnowledgeBase();
    const match = kb.matchQuestion("Do you encrypt data at rest?");
    assert.ok(match);
    assert.ok(match.entry.answer.includes("AES-256"));
  });

  it("should search by category", () => {
    const kb = new QuestionnaireKnowledgeBase();
    const results = kb.search("encryption", []);
    assert.ok(results.length > 0);
  });
});

describe("QuestionnaireAutomation", () => {
  it("should parse CSV and auto-answer", () => {
    const qa = new QuestionnaireAutomation();
    const csv = "Section,Number,Question,Type,Required\nAccess,1,Do you use MFA?,boolean,true\nEncryption,2,Do you encrypt data at rest?,boolean,true\nMonitoring,3,Do you have SIEM monitoring?,boolean,true";
    const q = qa.parseCSVQuestions(csv);
    assert.equal(q.questions.length, 3);

    const response = qa.autoAnswer(q.id);
    assert.ok(response);
    assert.ok(response.overallConfidence > 0);
    assert.ok(response.autoAnsweredCount > 0);
  });
});
