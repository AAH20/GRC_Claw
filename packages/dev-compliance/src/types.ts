export type FrameworkCode = "iso27001" | "nist-csf" | "soc2" | "iso42001" | "eu-ai-act" | "gdpr" | "hipaa" | "pci-dss" | "fedramp";

export interface GitHubAppConfig {
  appId: number;
  privateKey: string;
  webhookSecret: string;
  installationId: number;
}

export interface PRReviewResult {
  prNumber: number;
  repo: string;
  findings: ComplianceFinding[];
  summary: string;
  status: "approved" | "changes_requested" | "commented";
}

export interface ComplianceFinding {
  file: string;
  line: number;
  severity: "critical" | "high" | "medium" | "low";
  rule: string;
  message: string;
  framework: FrameworkCode;
  controlId: string;
  autoFix?: string;
}

export interface CICDGateResult {
  passed: boolean;
  score: number;
  findings: ComplianceFinding[];
  gateName: string;
}

export interface ASTAnalysisResult {
  files: number;
  violations: ComplianceFinding[];
  patterns: DetectedPattern[];
}

export interface DetectedPattern {
  type: "hardcoded_secret" | "weak_encryption" | "sql_injection" | "xss" | "insecure_deserialization" | "missing_mfa" | "insecure_random";
  count: number;
  severity: "critical" | "high" | "medium" | "low";
}
