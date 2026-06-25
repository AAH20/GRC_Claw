export type FrameworkCode = "iso27001" | "nist-csf" | "soc2" | "iso42001" | "eu-ai-act" | "gdpr" | "hipaa" | "pci-dss" | "fedramp";

export interface FAIRInput {
  threatEventFrequency: number;
  probableLossMagnitude: number;
  vulnerability: number;
  threatCapability: number;
  lossEvents?: number;
}

export interface FAIROutput {
  expectedAnnualLoss: number;
  confidenceInterval: { low: number; high: number };
  riskRating: "minimal" | "low" | "medium" | "high" | "critical";
  annualizedLossExposure: number;
}

export interface BreachCostInput {
  recordCount: number;
  framework: FrameworkCode;
  industry: string;
  detectionTime: number;
  responseTime: number;
  hasInsurance: boolean;
}

export interface BreachCostOutput {
  totalCost: number;
  perRecordCost: number;
  breakdown: {
    detection: number;
    response: number;
    notification: number;
    legal: number;
    regulatory: number;
    reputation: number;
    business: number;
  };
  insuranceCoverage: number;
  netCost: number;
}

export interface ROIInput {
  annualComplianceCost: number;
  frameworkCount: number;
  employeeCount: number;
  annualRevenue: number;
  currentScore: number;
  targetScore: number;
}

export interface ROIOutput {
  annualSavings: number;
  paybackPeriodMonths: number;
  threeYearROI: number;
  costPerControl: number;
  complianceCostReduction: number;
  riskReductionValue: number;
}
