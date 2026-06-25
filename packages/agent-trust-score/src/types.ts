export type FrameworkCode =
  | "iso27001"
  | "nist-csf"
  | "soc2"
  | "iso42001"
  | "eu-ai-act"
  | "dora"
  | "nis2"
  | "hipaa"
  | "pci-dss"
  | "fedramp"
  | "cmmc"
  | "gdpr"
  | "lgpd"
  | "pipl"
  | "tisax"
  | "popia";

export type TrustScore = number & { readonly __brand: "TrustScore" };
export type RiskLevel = "minimal" | "low" | "medium" | "high" | "critical";
export type AgentStatus = "active" | "suspended" | "revoked" | "probation";
export type CredentialType = "identity" | "capability" | "compliance" | "behavior" | "composite";
export type BehavioralAnomaly = "loop_detected" | "rapid_discovery" | "semantic_thought_loop" | "tool_abuse" | "data_exfiltration" | "privilege_escalation";

export interface TrustScoreDimensions {
  identity: number;
  capability: number;
  compliance: number;
  behavior: number;
  provenance: number;
}

export interface AgentTrustProfile {
  agentDid: string;
  agentName: string;
  tenantId: string;
  status: AgentStatus;
  overallTrustScore: TrustScore;
  dimensions: TrustScoreDimensions;
  riskLevel: RiskLevel;
  riskFactors: RiskFactor[];
  behavioralSignals: BehavioralSignal[];
  compliancePosture: AgentCompliancePosture;
  credentialSummary: CredentialSummary;
  lastScoredAt: string;
  scoreHistory: TrustScoreEntry[];
}

export interface RiskFactor {
  id: string;
  category: string;
  description: string;
  severity: RiskLevel;
  weight: number;
  mitigated: boolean;
  mitigatedAt?: string;
  mitigation?: string;
}

export interface BehavioralSignal {
  type: BehavioralAnomaly | "normal_operation" | "suspicious_pattern";
  timestamp: string;
  confidence: number;
  details: string;
  impact: number;
}

export interface AgentCompliancePosture {
  frameworks: FrameworkCode[];
  overallScore: number;
  controlScores: Map<string, number>;
  lastAuditAt: string;
  openFindings: number;
}

export interface CredentialSummary {
  total: number;
  valid: number;
  expired: number;
  revoked: number;
  lastIssuedAt?: string;
  lastRevokedAt?: string;
}

export interface TrustScoreEntry {
  timestamp: string;
  score: TrustScore;
  dimensions: TrustScoreDimensions;
  trigger: string;
}

export interface TrustScoreConfig {
  identityWeight: number;
  capabilityWeight: number;
  complianceWeight: number;
  behaviorWeight: number;
  provenanceWeight: number;
  decayRate: number;
  minScore: TrustScore;
  maxScore: TrustScore;
}

export interface TrustCredential {
  id: string;
  agentDid: string;
  type: CredentialType;
  claims: Record<string, unknown>;
  issuedAt: string;
  expiresAt: string;
  issuer: string;
  signature: string;
  revoked: boolean;
}

export interface BehavioralAnalysis {
  agentDid: string;
  timespan: number;
  totalActions: number;
  anomalies: BehavioralAnomaly[];
  anomalyCount: number;
  riskScore: number;
  recommendations: string[];
}
