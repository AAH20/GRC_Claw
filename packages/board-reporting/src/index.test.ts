import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { BoardReportGenerator } from "./reports/BoardReportGenerator.js";

describe("BoardReportGenerator", () => {
  it("should generate board report", () => {
    const gen = new BoardReportGenerator();
    const report = gen.generateReport("board_summary", "Q1 2026");
    assert.ok(report.id);
    assert.equal(report.type, "board_summary");
    assert.ok(report.sections.length > 0);
    assert.ok(report.riskHeatmap.data.length > 0);
    assert.ok(report.complianceTrend.data.length > 0);
  });

  it("should get executive dashboard", () => {
    const gen = new BoardReportGenerator();
    const dash = gen.getExecutiveDashboard();
    assert.ok(dash.overallRiskScore > 0);
    assert.ok(dash.complianceScore > 0);
  });

  it("should generate recommendations", () => {
    const gen = new BoardReportGenerator();
    const report = gen.generateReport("risk_heatmap", "Q1 2026");
    assert.ok(report.recommendations.length > 0);
  });
});
