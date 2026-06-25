import type { ROIInput, ROIOutput } from "../types.js";

export class ROICalculator {
  calculate(input: ROIInput): ROIOutput {
    const complianceCostReduction = input.annualComplianceCost * 0.35;
    const riskReductionValue = input.annualRevenue * 0.02 * ((input.targetScore - input.currentScore) / 100);
    const annualSavings = complianceCostReduction + riskReductionValue;
    const paybackPeriodMonths = Math.ceil((input.annualComplianceCost * 0.15) / (annualSavings / 12));
    const threeYearROI = ((annualSavings * 3 - input.annualComplianceCost * 0.15) / (input.annualComplianceCost * 0.15)) * 100;
    const costPerControl = input.annualComplianceCost / (input.frameworkCount * 100);

    return {
      annualSavings: Math.round(annualSavings),
      paybackPeriodMonths,
      threeYearROI: Math.round(threeYearROI),
      costPerControl: Math.round(costPerControl),
      complianceCostReduction: Math.round(complianceCostReduction),
      riskReductionValue: Math.round(riskReductionValue),
    };
  }
}
