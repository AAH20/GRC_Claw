import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { GitHubPRReviewer } from "./github/GitHubPRReviewer.js";
import { CICDComplianceGate } from "./cicd/CICDComplianceGate.js";

describe("GitHubPRReviewer", () => {
  it("should detect hardcoded secrets", async () => {
    const reviewer = new GitHubPRReviewer();
    const result = await reviewer.reviewPR({
      number: 1,
      repo: "test/repo",
      title: "Test PR",
      body: "Test",
      files: [{ filename: "config.ts", patch: '+ const apiKey = "sk-1234567890";', additions: 1, deletions: 0 }],
    });
    assert.ok(result.findings.length > 0);
    assert.equal(result.status, "changes_requested");
  });

  it("should approve clean PRs", async () => {
    const reviewer = new GitHubPRReviewer();
    const result = await reviewer.reviewPR({
      number: 2,
      repo: "test/repo",
      title: "Clean PR",
      body: "Test",
      files: [{ filename: "readme.md", patch: "+ # Hello World", additions: 1, deletions: 0 }],
    });
    assert.equal(result.findings.length, 0);
    assert.equal(result.status, "approved");
  });
});

describe("CICDComplianceGate", () => {
  it("should fail on critical findings", async () => {
    const gate = new CICDComplianceGate({ framework: "iso27001", failOnSeverity: "critical", maxScore: 80 });
    const result = await gate.evaluate({
      files: ["config.ts"],
      content: new Map([["config.ts", 'const password = "secret123"']]),
    });
    assert.equal(result.passed, false);
    assert.ok(result.findings.length > 0);
  });

  it("should pass on clean code", async () => {
    const gate = new CICDComplianceGate({ framework: "soc2", failOnSeverity: "critical", maxScore: 80 });
    const result = await gate.evaluate({
      files: ["readme.md"],
      content: new Map([["readme.md", "# Hello World"]]),
    });
    assert.equal(result.passed, true);
    assert.equal(result.score, 100);
  });
});
