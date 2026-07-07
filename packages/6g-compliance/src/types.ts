export interface NetworkComponent {
  id: string;
  name: string;
  type: NetworkComponentType;
  vendor: string;
  version: string;
  location: NetworkLocation;
  interfaces: NetworkInterface[];
  metadata: ComponentMetadata;
}

export type NetworkComponentType =
  | 'ran-node'
  | 'core-network'
  | 'edge-compute'
  | 'transport'
  | 'device'
  | 'orchestrator'
  | 'ai-ml-engine'
  | 'slice-controller'
  | 'security-gateway'
  | 'policy-controller';

export interface NetworkLocation {
  region: string;
  zone: string;
  site?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface NetworkInterface {
  id: string;
  name: string;
  type: 'e1' | 'e2' | 'o1' | 'o2' | 'a1' | 'ric-platform' | 'near-rt-ric' | 'non-rt-ric' | 'f1' | 'n1' | 'n2' | 'n3' | 'x1';
  protocol: string;
  ipAddress?: string;
  port?: number;
  encrypted: boolean;
}

export interface ComponentMetadata {
  deploymentDate: string;
  lastUpdate?: string;
  firmwareVersion?: string;
  certificationLevel?: string;
  owner?: string;
  team?: string;
}

export type ComplianceFramework =
  | '3gpp-ts33501'
  | '3gpp-ts33210'
  | '3gpp-ts33511'
  | '3gpp-ts33512'
  | 'nist-csf'
  | 'nist-800-53'
  | 'iso-27001'
  | 'iso-27002'
  | 'eu-ai-act'
  | 'oran-sds'
  | 'oran-security'
  | 'etsi-nfvi'
  | 'gsma-iris';

export interface ControlMapping {
  id: string;
  framework: ComplianceFramework;
  controlId: string;
  title: string;
  description: string;
  category: string;
  status: ControlStatus;
  evidence: Evidence[];
  assessedDate: string;
  assessor?: string;
  remediation?: RemediationPlan;
  risk: RiskLevel;
}

export type ControlStatus =
  | 'compliant'
  | 'partially-compliant'
  | 'non-compliant'
  | 'not-applicable'
  | 'pending-assessment'
  | 'remediation-in-progress';

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'informational';

export interface Evidence {
  id: string;
  type: EvidenceType;
  description: string;
  filePath?: string;
  url?: string;
  collectedDate: string;
  validUntil?: string;
  hash?: string;
}

export type EvidenceType =
  | 'configuration-file'
  | 'log-excerpt'
  | 'scan-result'
  | 'certificate'
  | 'policy-document'
  | 'audit-trail'
  | 'test-result'
  | 'certificate-of-conformity'
  | 'penetration-test'
  | 'vulnerability-scan';

export interface RemediationPlan {
  id: string;
  description: string;
  steps: RemediationStep[];
  priority: RiskLevel;
  targetDate: string;
  status: 'planned' | 'in-progress' | 'completed' | 'deferred';
  assignee?: string;
}

export interface RemediationStep {
  order: number;
  description: string;
  completed: boolean;
  completedDate?: string;
  notes?: string;
}

export interface SecurityAssessment {
  id: string;
  component: NetworkComponent;
  framework: ComplianceFramework;
  controls: ControlMapping[];
  score: number;
  gaps: SecurityGap[];
  assessedDate: string;
  assessor: string;
  recommendations: Recommendation[];
}

export interface SecurityGap {
  id: string;
  controlId: string;
  description: string;
  severity: RiskLevel;
  impact: string;
  remediation: RemediationPlan;
}

export interface Recommendation {
  id: string;
  priority: RiskLevel;
  title: string;
  description: string;
  affectedControls: string[];
  estimatedEffort: 'low' | 'medium' | 'high';
  estimatedImpact: 'low' | 'medium' | 'high';
}

export interface NetworkComplianceReport {
  id: string;
  generatedAt: string;
  reportPeriod: {
    start: string;
    end: string;
  };
  components: NetworkComponent[];
  assessments: SecurityAssessment[];
  overallScore: number;
  complianceByFramework: Record<ComplianceFramework, FrameworkCompliance>;
  criticalGaps: SecurityGap[];
  recommendations: Recommendation[];
  summary: ReportSummary;
}

export interface FrameworkCompliance {
  framework: ComplianceFramework;
  score: number;
  totalControls: number;
  compliantControls: number;
  nonCompliantControls: number;
  gaps: SecurityGap[];
}

export interface ReportSummary {
  totalComponents: number;
  assessedComponents: number;
  compliantComponents: number;
  partiallyCompliantComponents: number;
  nonCompliantComponents: number;
  criticalGapsCount: number;
  highGapsCount: number;
  mediumGapsCount: number;
  lowGapsCount: number;
  averageScore: number;
}

export interface ContinuousMonitoringConfig {
  enabled: boolean;
  intervalMinutes: number;
  alertsEnabled: boolean;
  thresholdScore: number;
  autoRemediate: boolean;
  notificationChannels: NotificationChannel[];
}

export interface NotificationChannel {
  type: 'email' | 'slack' | 'webhook' | 'pagerduty';
  endpoint: string;
  severityFilter: RiskLevel[];
}

export interface MonitoringResult {
  timestamp: string;
  componentId: string;
  score: number;
  status: ControlStatus;
  alerts: MonitoringAlert[];
  changes: ChangeDetected[];
}

export interface MonitoringAlert {
  id: string;
  severity: RiskLevel;
  message: string;
  controlId?: string;
  detectedAt: string;
}

export interface ChangeDetected {
  type: 'config-change' | 'version-update' | 'interface-change' | 'policy-violation';
  description: string;
  timestamp: string;
  details: Record<string, unknown>;
}
