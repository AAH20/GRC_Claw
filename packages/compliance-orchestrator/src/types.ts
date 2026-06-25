export type FrameworkCode =
  | 'iso27001' | 'nist-csf' | 'soc2' | 'iso42001' | 'eu-ai-act'
  | 'dora' | 'nis2' | 'hipaa' | 'pci-dss' | 'fedramp' | 'cmmc'
  | 'gdpr' | 'lgpd' | 'pipl' | 'tisax' | 'popia';

export interface ControlNode {
  id: string;
  framework: FrameworkCode;
  code: string;
  title: string;
  description: string;
  family: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  dependencies: string[];
  evidenceRequirements: EvidenceRequirement[];
  testLogic?: TestLogic;
  remediation?: RemediationTemplate;
}

export interface EvidenceRequirement {
  type: 'screenshot' | 'log' | 'config' | 'certificate' | 'policy' | 'attestation' | 'scan' | 'automated';
  source: string;
  freshness: string;
  cryptographic?: boolean;
}

export interface TestLogic {
  type: 'rego' | 'sql' | 'typescript' | 'yaml' | 'external';
  code: string;
  inputs: Record<string, string>;
  expectedOutput: unknown;
}

export interface RemediationTemplate {
  type: 'terraform' | 'aws-cli' | 'azure-cli' | 'gcp-cli' | 'kubernetes' | 'manual' | 'script';
  code: string;
  rollbackCode?: string;
  estimatedTime: string;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface CrosswalkEntry {
  sourceFramework: FrameworkCode;
  sourceControl: string;
  targetFramework: FrameworkCode;
  targetControl: string;
  relationship: 'equivalent' | 'stronger' | 'weaker' | 'subset' | 'superset';
  confidence: number;
}

export interface RegulationAST {
  id: string;
  framework: FrameworkCode;
  version: string;
  compiledAt: string;
  controls: ASTControlNode[];
  crosswalks: CrosswalkEntry[];
  metadata: RegulationMetadata;
}

export interface ASTControlNode {
  id: string;
  code: string;
  title: string;
  ast: PolicyAST;
  crossRefs: string[];
  evidenceChain: EvidenceChain;
}

export interface PolicyAST {
  type: 'conjunction' | 'disjunction' | 'implication' | 'negation' | 'atom';
  operator?: string;
  children?: PolicyAST[];
  atom?: PolicyAtom;
}

export interface PolicyAtom {
  subject: string;
  predicate: string;
  object: string;
  constraints: Record<string, unknown>;
}

export interface EvidenceChain {
  required: EvidenceRequirement[];
  collected: CollectedEvidence[];
  validUntil: string;
}

export interface CollectedEvidence {
  id: string;
  controlId: string;
  type: string;
  source: string;
  hash: string;
  timestamp: string;
  valid: boolean;
  verifiedBy?: string;
}

export interface RegulationMetadata {
  title: string;
  issuer: string;
  publishedAt: string;
  effectiveAt: string;
  totalControls: number;
  families: string[];
}

export interface ComplianceState {
  orgId: string;
  timestamp: string;
  framework: FrameworkCode;
  overallScore: number;
  controlStatuses: ControlStatus[];
  drift: DriftEvent[];
  risks: RiskAssessment[];
}

export interface ControlStatus {
  controlId: string;
  status: 'compliant' | 'non-compliant' | 'partial' | 'not-applicable' | 'not-tested';
  lastVerified: string;
  evidenceCount: number;
  score: number;
  issues: ControlIssue[];
}

export interface ControlIssue {
  id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  detectedAt: string;
  remediation?: RemediationTemplate;
}

export interface DriftEvent {
  id: string;
  controlId: string;
  detectedAt: string;
  type: 'configuration' | 'policy' | 'evidence' | 'access' | 'network';
  before: unknown;
  after: unknown;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  autoRemediated: boolean;
  remediationId?: string;
}

export interface RiskAssessment {
  controlId: string;
  riskScore: number;
  blastRadius: number;
  likelihood: number;
  impact: number;
  factors: string[];
}

export interface CompliancePlan {
  id: string;
  orgId: string;
  framework: FrameworkCode;
  createdAt: string;
  actions: PlanAction[];
  estimatedCost: number;
  estimatedDuration: string;
}

export interface PlanAction {
  id: string;
  controlId: string;
  action: 'create' | 'update' | 'delete' | 'verify' | 'remediate';
  resource: string;
  before?: unknown;
  after?: unknown;
  evidenceRequired: string[];
  sla: string;
  owner?: string;
}

export interface ComplianceAudit {
  id: string;
  orgId: string;
  framework: FrameworkCode;
  startedAt: string;
  completedAt?: string;
  controls: AuditControlResult[];
  summary: AuditSummary;
}

export interface AuditControlResult {
  controlId: string;
  status: 'pass' | 'fail' | 'skip' | 'error';
  evidence: CollectedEvidence[];
  issues: ControlIssue[];
  duration: number;
}

export interface AuditSummary {
  totalControls: number;
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
  complianceScore: number;
  criticalFindings: number;
  highFindings: number;
}
