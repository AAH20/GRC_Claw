import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { FAIRCalculator } from "./fair/FAIRCalculator.js";
import { BreachCostCalculator } from "./calculators/BreachCostCalculator.js";
import { ROICalculator } from "./calculators/ROICalculator.js";

describe("FAIRCalculator", () => {
  it("should calculate annualized loss exposure", () => {
    const calc = new FAIRCalculator(1000);
    const result = calc.calculate({ threatEventFrequency: 10, probableLossMagnitude: 50000, vulnerability: 0.3, threatCapability: 0.5 });
    assert.ok(result.expectedAnnualLoss > 0);
    assert.ok(["minimal", "low", "medium", "high", "critical"].includes(result.riskRating));
  });
});

describe("BreachCostCalculator", () => {
  it("should calculate breach cost for healthcare", () => {
    const calc = new BreachCostCalculator();
    const result = calc.calculate({ recordCount: 10000, framework: "hipaa", industry: "healthcare", detectionTime: 24, responseTime: 72, hasInsurance: true });
    assert.ok(result.totalCost > 0);
    assert.ok(result.perRecordCost > 0);
    assert.ok(result.breakdown.detection > 0);
  });
});

describe("ROICalculator", () => {
  it("should calculate compliance ROI", () => {
    const calc = new ROICalculator();
    const result = calc.calculate({ annualComplianceCost: 200000, frameworkCount: 3, employeeCount: 100, annualRevenue: 10000000, currentScore: 65, targetScore: 90 });
    assert.ok(result.annualSavings > 0);
    assert.ok(result.paybackPeriodMonths > 0);
    assert.ok(result.threeYearROI > 0);
  });
});
