export type RiskTier = 'minimal' | 'limited' | 'high' | 'unacceptable';

export type ComplianceFramework = 'EU_AI_ACT' | 'NIST_AI_RMF' | 'ISO_42001';

export type NistFunction = 'GOVERN' | 'MAP' | 'MEASURE' | 'MANAGE';

export interface NemotronModel {
  id: string;
  name: string;
  version: string;
  parameters: number;
  capabilities: string[];
  license: string;
  trainingDataSources: string[];
  architecture: string;
  contextWindow: number;
  modality: 'text' | 'multimodal';
}

export interface ComplianceGap {
  controlId: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  remediation: string;
}

export interface ComplianceAssessment {
  framework: ComplianceFramework;
  score: number;
  gaps: ComplianceGap[];
  recommendations: string[];
  assessedAt: string;
}

export interface AiBomEntry {
  modelId: string;
  modelName: string;
  version: string;
  trainingData: TrainingDataRecord[];
  license: string;
  vulnerabilities: VulnerabilityRecord[];
  sbomHash: string;
  generatedAt: string;
}

export interface TrainingDataRecord {
  source: string;
  domain: string;
  sizeBytes: number;
  license: string;
  piiFlagged: boolean;
}

export interface VulnerabilityRecord {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  mitigation: string;
  cve?: string;
}

export interface NemotronDeploymentConfig {
  model: NemotronModel;
  hardware: HardwareConfig;
  network: NetworkConfig;
  security: SecurityConfig;
  environment: 'production' | 'staging' | 'development';
}

export interface HardwareConfig {
  gpus: number;
  gpuMemory: number;
  precision: 'fp16' | 'bf16' | 'fp8' | 'int8' | 'int4';
  quantization: boolean;
  tensorParallelism: number;
}

export interface NetworkConfig {
  exposed: boolean;
  tlsVersion: string;
  rateLimiting: boolean;
  maxRequestsPerMinute: number;
  allowedOrigins: string[];
}

export interface SecurityConfig {
  authRequired: boolean;
  authMethod: 'api_key' | 'oauth2' | 'jwt' | 'mtls';
  inputValidation: boolean;
  outputFiltering: boolean;
  loggingEnabled: boolean;
  auditTrail: boolean;
  dataEncryption: 'at-rest' | 'in-transit' | 'both';
  accessControl: 'rbac' | 'abac' | 'acl';
}

export interface ComplianceReport {
  model: NemotronModel;
  assessments: ComplianceAssessment[];
  aiBom: AiBomEntry;
  riskScore: number;
  riskTier: RiskTier;
  recommendations: string[];
  generatedAt: string;
  reportId: string;
}

export interface AnnexAControl {
  id: string;
  name: string;
  category: string;
  description: string;
  applicable: boolean;
  status: 'compliant' | 'non-compliant' | 'partial' | 'not-applicable';
  evidence?: string;
}

export interface Iso42001Assessment {
  controls: AnnexAControl[];
  overallScore: number;
  gaps: ComplianceGap[];
  recommendations: string[];
}

export interface EuAiActAssessment {
  riskTier: RiskTier;
  articles: ArticleRequirement[];
  conformityAssessment: ConformityAssessment;
  transparencyObligations: TransparencyCheck[];
}

export interface ArticleRequirement {
  article: string;
  title: string;
  required: boolean;
  met: boolean;
  details: string;
}

export interface ConformityAssessment {
  passed: boolean;
  checks: ConformityCheck[];
  timestamp: string;
}

export interface ConformityCheck {
  id: string;
  description: string;
  passed: boolean;
  evidence: string;
}

export interface TransparencyCheck {
  obligation: string;
  met: boolean;
  details: string;
}

export interface NistRmfAssessment {
  functions: NistFunctionAssessment[];
  overallScore: number;
  riskLevel: string;
  accountabilityChecks: AccountabilityCheck[];
}

export interface NistFunctionAssessment {
  function: NistFunction;
  score: number;
  controls: NistControl[];
}

export interface NistControl {
  id: string;
  name: string;
  met: boolean;
  description: string;
}

export interface AccountabilityCheck {
  requirement: string;
  met: boolean;
  responsible: string;
}
