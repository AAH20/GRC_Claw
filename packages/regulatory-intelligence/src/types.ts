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

export type RegulationSource = "official" | "news" | "analysis" | "guidance" | "comment";
export type ChangeType = "new_regulation" | "amendment" | "guidance_update" | "enforcement_action" | "deadline_change" | "standard_revision";
export type ImpactLevel = "none" | "minimal" | "moderate" | "significant" | "critical";
export type MonitoringStatus = "active" | "paused" | "completed";

export interface RegulatorySource {
  id: string;
  name: string;
  url: string;
  jurisdiction: string;
  framework: FrameworkCode;
  pollingIntervalMs: number;
  lastCheckedAt?: string;
  status: MonitoringStatus;
  selectors?: SourceSelectors;
}

export interface SourceSelectors {
  titleSelector?: string;
  contentSelector?: string;
  dateSelector?: string;
  changeIndicatorSelector?: string;
}

export interface RegulatoryChange {
  id: string;
  sourceId: string;
  title: string;
  summary: string;
  fullText: string;
  detectedAt: string;
  publishedAt?: string;
  changeType: ChangeType;
  jurisdiction: string;
  framework: FrameworkCode;
  affectedControls: string[];
  impactLevel: ImpactLevel;
  impactAnalysis: ImpactAnalysis;
  status: "detected" | "analyzed" | "acknowledged" | "implemented" | "dismissed";
}

export interface ImpactAnalysis {
  affectedControls: AffectedControl[];
  overallImpact: ImpactLevel;
  estimatedRemediationDays: number;
  complianceGapScore: number;
  recommendedActions: string[];
  crossFrameworkImpact: CrossFrameworkImpact[];
}

export interface AffectedControl {
  controlId: string;
  controlCode: string;
  framework: FrameworkCode;
  impact: ImpactLevel;
  gapDescription: string;
  remediation: string;
  estimatedEffort: string;
}

export interface CrossFrameworkImpact {
  framework: FrameworkCode;
  controlId: string;
  relationship: "direct_mapping" | "indirect_mapping" | "related";
  confidence: number;
}

export interface RegulatoryDigest {
  id: string;
  generatedAt: string;
  period: { from: string; to: string };
  jurisdiction: string;
  changes: RegulatoryChange[];
  summary: string;
  priorityActions: string[];
  totalImpactScore: number;
}

export interface MonitoringConfig {
  defaultPollingIntervalMs: number;
  maxConcurrentFetches: number;
  changeDetectionThreshold: number;
  alertOnCritical: boolean;
  digestSchedule: "daily" | "weekly" | "monthly";
}

export interface ChangeDetectionResult {
  hasChange: boolean;
  changeType?: ChangeType;
  confidence: number;
  diffSummary?: string;
}
