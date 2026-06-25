export type FrameworkCode = "iso27001" | "nist-csf" | "soc2" | "iso42001" | "eu-ai-act" | "gdpr" | "hipaa" | "pci-dss" | "fedramp" | "dora" | "nis2";

export type VendorRiskTier = "critical" | "high" | "medium" | "low";
export type VendorStatus = "prospect" | "onboarding" | "active" | "monitoring" | "offboarding" | "terminated";
export type AssessmentStatus = "pending" | "in_progress" | "completed" | "expired";

export interface Vendor {
  id: string;
  name: string;
  domain: string;
  status: VendorStatus;
  riskTier: VendorRiskTier;
  overallScore: number;
  categories: string[];
  frameworks: FrameworkCode[];
  contacts: VendorContact[];
  contracts: VendorContract[];
  assessments: VendorAssessment[];
  documents: VendorDocument[];
  riskFactors: RiskFactor[];
  lastAssessedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VendorContact {
  name: string;
  email: string;
  role: string;
  isPrimary: boolean;
}

export interface VendorContract {
  id: string;
  type: string;
  startDate: string;
  endDate: string;
  value: number;
  slaTerms: Record<string, unknown>;
}

export interface VendorAssessment {
  id: string;
  vendorId: string;
  type: "initial" | "annual" | "triggered" | "questionnaire";
  status: AssessmentStatus;
  framework: FrameworkCode;
  questions: AssessmentQuestion[];
  responses: Record<string, string>;
  score: number;
  findings: AssessmentFinding[];
  completedAt?: string;
  expiresAt?: string;
  createdAt: string;
}

export interface AssessmentQuestion {
  id: string;
  category: string;
  question: string;
  required: boolean;
  type: "text" | "boolean" | "select" | "evidence";
  options?: string[];
}

export interface AssessmentFinding {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  controlId?: string;
  remediation?: string;
}

export interface VendorDocument {
  id: string;
  type: "soc2" | "iso27001" | "penetration_test" | "insurance" | "policy" | "other";
  name: string;
  url: string;
  sha256: string;
  uploadedAt: string;
  expiresAt?: string;
}

export interface RiskFactor {
  category: string;
  score: number;
  weight: number;
  details: string;
}

export interface VendorRiskScore {
  vendorId: string;
  overallScore: number;
  cybersecurityScore: number;
  complianceScore: number;
  operationalScore: number;
  financialScore: number;
  reputationalScore: number;
  riskTier: VendorRiskTier;
  calculatedAt: string;
}

export interface VendorMonitoring {
  vendorId: string;
  lastCheckedAt: string;
  alerts: VendorAlert[];
  continuousScore: number;
  trend: "improving" | "stable" | "degrading";
}

export interface VendorAlert {
  id: string;
  type: "certification_expired" | "risk_change" | "breach_detected" | "sla_violation" | "document_expiring";
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  detectedAt: string;
  acknowledged: boolean;
}
