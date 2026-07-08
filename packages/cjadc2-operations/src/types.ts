/**
 * CJADC2 Operations Framework Type Definitions
 * Combined Joint All-Domain Command and Control
 */

export enum Cjadc2Domain {
  SENSE = 'sense',
  DECIDE = 'decide',
  ACT = 'act',
  COMMUNICATE = 'communicate',
  MOVE = 'move',
  PROTECT = 'protect'
}

export enum ComponentType {
  SENSOR = 'sensor',
  WEAPON = 'weapon',
  PLATFORM = 'platform',
  NETWORK = 'network',
  COMMAND = 'command',
  AI_SYSTEM = 'ai_system',
  DATA_LINK = 'data_link',
  DECISION_AID = 'decision_aid'
}

export enum ComponentStatus {
  OPERATIONAL = 'operational',
  DEGRADED = 'degraded',
  MAINTENANCE = 'maintenance',
  OFFLINE = 'offline',
  UNKNOWN = 'unknown'
}

export enum SecurityClassification {
  UNCLASSIFIED = 'unclassified',
  CONFIDENTIAL = 'confidential',
  SECRET = 'secret',
  TOP_SECRET = 'top_secret',
  SCI = 'sci'
}

export enum OperationStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  ABORTED = 'aborted'
}

export enum InteroperabilityStandard {
  STANAG_4586 = 'STANAG_4586',
  STANAG_5500 = 'STANAG_5500',
  STANAG_6017 = 'STANAG_6017',
  LINK_16 = 'LINK_16',
  LINK_22 = 'LINK_22',
  VMF = 'VMF',
  NCIA = 'NCIA',
  NATO_APP6 = 'NATO_APP6'
}

export enum SecurityControl {
  ENCRYPTION = 'encryption',
  AUTHENTICATION = 'authentication',
  ACCESS_CONTROL = 'access_control',
  AUDIT_LOGGING = 'audit_logging',
  DATA_INTEGRITY = 'data_integrity',
  NETWORK_SEGMENTATION = 'network_segmentation',
  INTRUSION_DETECTION = 'intrusion_detection',
  ZERO_TRUST = 'zero_trust'
}

export enum SecurityLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum Gr00tCapability {
  SENSE_FUSION = 'sense_fusion',
  DECISION_SUPPORT = 'decision_support',
  AUTONOMOUS_ACTION = 'autonomous_action',
  SECURE_COMMS = 'secure_comms',
  NETWORK_RESILIENCE = 'network_resilience',
  THREAT_DETECTION = 'threat_detection',
  DATA_SHARING = 'data_sharing',
  SITUATIONAL_AWARENESS = 'situational_awareness'
}

export interface InteroperabilityRequirement {
  protocol: string;
  standard: InteroperabilityStandard;
  version: string;
  required: boolean;
  maxLatencyMs?: number;
  encryptionRequired?: boolean;
}

export interface SecurityRequirement {
  control: SecurityControl;
  level: SecurityLevel;
  status: 'met' | 'partial' | 'not_met';
  lastAudit?: Date;
  nextAudit?: Date;
  notes?: string;
}

export interface Cjadc2Component {
  id: string;
  name: string;
  type: ComponentType;
  domain: Cjadc2Domain[];
  classification: SecurityClassification;
  status: ComponentStatus;
  capabilities: string[];
  interoperability: InteroperabilityRequirement[];
  security: SecurityRequirement[];
  metadata?: Record<string, unknown>;
}

export interface DomainAssessment {
  domain: Cjadc2Domain;
  score: number;
  maxScore: number;
  status: 'compliant' | 'partial' | 'non_compliant';
  issues: AssessmentIssue[];
  recommendations: string[];
  componentsAssessed: number;
  timestamp: Date;
}

export interface AssessmentIssue {
  severity: 'critical' | 'high' | 'medium' | 'low';
  component?: string;
  description: string;
  standard?: string;
  remediation?: string;
}

export interface InteroperabilityAssessment {
  score: number;
  maxScore: number;
  status: 'compliant' | 'partial' | 'non_compliant';
  protocolIssues: ProtocolIssue[];
  compliance: ProtocolCompliance[];
  timestamp: Date;
}

export interface ProtocolIssue {
  protocol: string;
  component: string;
  issue: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface ProtocolCompliance {
  standard: InteroperabilityStandard;
  compliant: boolean;
  components: string[];
  version: string;
}

export interface SecurityAssessment {
  score: number;
  maxScore: number;
  status: 'compliant' | 'partial' | 'non_compliant';
  controlStatus: ControlStatus[];
  vulnerabilities: Vulnerability[];
  timestamp: Date;
}

export interface ControlStatus {
  control: SecurityControl;
  level: SecurityLevel;
  met: number;
  total: number;
  percentage: number;
}

export interface Vulnerability {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  component: string;
  control: SecurityControl;
  description: string;
  remediation: string;
}

export interface Cjadc2Operation {
  id: string;
  name: string;
  type: string;
  domain: Cjadc2Domain[];
  components: string[];
  status: OperationStatus;
  classification: SecurityClassification;
  startTime?: Date;
  endTime?: Date;
  objectives: string[];
  metadata?: Record<string, unknown>;
}

export interface OperationReport {
  operation: Cjadc2Operation;
  overallScore: number;
  domainScores: DomainAssessment[];
  interoperability: InteroperabilityAssessment;
  security: SecurityAssessment;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
  readinessStatus: 'ready' | 'conditionally_ready' | 'not_ready';
  summary: string;
  generatedAt: Date;
}

export interface Gr00tMapping {
  component: string;
  domain: Cjadc2Domain;
  capabilities: Gr00tCapability[];
  coverageScore: number;
  gaps: string[];
}

export interface Gr00tAssessment {
  mappings: Gr00tMapping[];
  overallCoverage: number;
  capabilityGaps: Gr00tCapability[];
  recommendations: string[];
  timestamp: Date;
}
