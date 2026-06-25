import type { BreachCostInput, BreachCostOutput } from "../types.js";

const PER_RECORD_COSTS: Record<string, number> = {
  healthcare: 173,
  finance: 165,
  technology: 155,
  pharmaceutical: 146,
  energy: 130,
  industrial: 128,
  default: 150,
};

const FRAMEWORK_MULTIPLIERS: Record<string, number> = {
  hipaa: 1.8,
  pci_dss: 1.5,
  gdpr: 1.6,
  soc2: 1.2,
  iso27001: 1.1,
  fedramp: 1.4,
};

export class BreachCostCalculator {
  calculate(input: BreachCostInput): BreachCostOutput {
    const perRecordCost = PER_RECORD_COSTS[input.industry] || PER_RECORD_COSTS.default;
    const frameworkMultiplier = FRAMEWORK_MULTIPLIERS[input.framework] || 1.0;

    const detection = input.detectionTime * 5000;
    const response = input.responseTime * 3000;
    const notification = input.recordCount * 10;
    const legal = input.recordCount * perRecordCost * 0.3;
    const regulatory = input.recordCount * perRecordCost * 0.4 * frameworkMultiplier;
    const reputation = input.recordCount * perRecordCost * 0.2;
    const business = input.recordCount * perRecordCost * 0.1;

    const totalCostBeforeInsurance = detection + response + notification + legal + regulatory + reputation + business;
    const insuranceCoverage = input.hasInsurance ? totalCostBeforeInsurance * 0.4 : 0;
    const netCost = totalCostBeforeInsurance - insuranceCoverage;

    return {
      totalCost: Math.round(totalCostBeforeInsurance),
      perRecordCost: Math.round(perRecordCost * frameworkMultiplier),
      breakdown: {
        detection: Math.round(detection),
        response: Math.round(response),
        notification: Math.round(notification),
        legal: Math.round(legal),
        regulatory: Math.round(regulatory),
        reputation: Math.round(reputation),
        business: Math.round(business),
      },
      insuranceCoverage: Math.round(insuranceCoverage),
      netCost: Math.round(netCost),
    };
  }
}
