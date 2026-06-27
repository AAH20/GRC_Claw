import { randomUUID } from "node:crypto";

// ─── Vendor Types ─────────────────────────────────────────────────────

export type VendorStatus =
  | "prospect"
  | "onboarding"
  | "active"
  | "monitoring"
  | "offboarding"
  | "terminated";

export type VendorTier = "critical" | "high" | "medium" | "low";

export type QuestionnaireType = "sig_lite" | "caiq" | "custom";

export type AssessmentStatus = "pending" | "in_progress" | "completed" | "expired";

export type RiskTrend = "improving" | "stable" | "degrading";

// ─── Vendor ───────────────────────────────────────────────────────────

export interface Vendor {
  id: string;
  name: string;
  domain: string;
  description: string;
  status: VendorStatus;
  tier: VendorTier;
  overallScore: number;
  categories: string[];
  contacts: VendorContact[];
  contracts: VendorContract[];
  documents: VendorDocument[];
  onboardedAt?: string;
  lastAssessedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VendorContact {
  id: string;
  name: string;
  email: string;
  phone?: string;
  role: string;
  isPrimary: boolean;
}

export interface VendorContract {
  id: string;
  type: string;
  startDate: string;
  endDate: string;
  value: number;
  autoRenew: boolean;
  slaTerms: Record<string, unknown>;
}

export interface VendorDocument {
  id: string;
  type: "soc2" | "iso27001" | "penetration_test" | "insurance" | "policy" | "business_associate_agreement" | "other";
  name: string;
  url: string;
  sha256: string;
  uploadedAt: string;
  expiresAt?: string;
}

// ─── Risk Scoring (4-factor model) ───────────────────────────────────

export interface VendorRiskScore {
  vendorId: string;
  cybersecurityScore: number;
  complianceScore: number;
  operationalScore: number;
  financialScore: number;
  overallScore: number;
  tier: VendorTier;
  calculatedAt: string;
  factors: RiskFactor[];
}

export interface RiskFactor {
  id: string;
  category: "cybersecurity" | "compliance" | "operational" | "financial";
  name: string;
  score: number;
  weight: number;
  evidence: string;
  details: string;
}

// ─── Questionnaire ────────────────────────────────────────────────────

export interface QuestionnaireTemplate {
  id: string;
  name: string;
  type: QuestionnaireType;
  framework: string;
  questions: QuestionnaireQuestion[];
  totalQuestions: number;
  version: number;
  createdAt: string;
}

export interface QuestionnaireQuestion {
  id: string;
  category: string;
  question: string;
  type: "text" | "boolean" | "select" | "evidence" | "rating";
  required: boolean;
  options?: string[];
  controlId?: string;
  framework?: string;
}

export interface VendorAssessment {
  id: string;
  vendorId: string;
  questionnaireId: string;
  questionnaireType: QuestionnaireType;
  status: AssessmentStatus;
  responses: Record<string, string>;
  findings: AssessmentFinding[];
  score: number;
  startedAt?: string;
  completedAt?: string;
  expiresAt?: string;
  createdAt: string;
}

export interface AssessmentFinding {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  questionId: string;
  description: string;
  controlId?: string;
  remediation?: string;
}

// ─── Continuous Monitoring ────────────────────────────────────────────

export interface VendorMonitoring {
  vendorId: string;
  enabled: boolean;
  frequencyDays: number;
  nextCheckAt: string;
  lastCheckedAt?: string;
  alerts: VendorAlert[];
  trend: RiskTrend;
  previousScore?: number;
}

export interface VendorAlert {
  id: string;
  vendorId: string;
  type: "certification_expired" | "risk_change" | "breach_detected" | "sla_violation" | "document_expiring" | "score_degradation";
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  details: Record<string, unknown>;
  detectedAt: string;
  acknowledged: boolean;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
}

// ─── Risk Register ────────────────────────────────────────────────────

export interface VendorRiskRegisterEntry {
  id: string;
  vendorId: string;
  riskId: string;
  description: string;
  category: string;
  likelihood: number;
  impact: number;
  riskScore: number;
  mitigations: string[];
  status: "open" | "mitigated" | "accepted" | "closed";
  owner: string;
  identifiedAt: string;
  lastReviewedAt?: string;
  createdAt: string;
  updatedAt: string;
}

// ─── Dashboard ────────────────────────────────────────────────────────

export interface VendorRiskDashboard {
  totalVendors: number;
  byTier: Record<VendorTier, number>;
  byStatus: Record<VendorStatus, number>;
  averageRiskScore: number;
  highRiskVendors: number;
  pendingAssessments: number;
  overdueAssessments: number;
  activeAlerts: number;
  criticalAlerts: number;
  expiringDocuments30Days: number;
  recentRiskChanges: VendorRiskChange[];
}

export interface VendorRiskChange {
  vendorId: string;
  vendorName: string;
  previousScore: number;
  currentScore: number;
  previousTier: VendorTier;
  currentTier: VendorTier;
  changedAt: string;
}

// ─── Search / Filter ──────────────────────────────────────────────────

export interface VendorSearchFilter {
  query?: string;
  status?: VendorStatus[];
  tier?: VendorTier[];
  categories?: string[];
  minScore?: number;
  maxScore?: number;
  onboardedBefore?: string;
  onboardedAfter?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────

export function newId(): string {
  return randomUUID();
}

export function nowIso(): string {
  return new Date().toISOString();
}

export function computeTier(score: number): VendorTier {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "medium";
  return "low";
}
