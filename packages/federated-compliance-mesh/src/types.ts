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

export type MeshTopology = "star" | "ring" | "mesh" | "hierarchical";
export type Jurisdiction = "global" | "eu" | "us" | "uk" | "apac" | "latam" | "mena";
export type OrgRelationship = "parent" | "subsidiary" | "partner" | "auditor" | "regulator";
export type ReportFormat = "json" | "csv" | "pdf" | "xlsx";
export type ComplianceLevel = "full" | "partial" | "minimal";

export interface FederatedOrganization {
  id: string;
  name: string;
  jurisdictions: Jurisdiction[];
  frameworks: FrameworkCode[];
  parentId?: string;
  relationships: OrgRelationship[];
  trustLevel: number;
  lastSyncAt?: string;
  status: "active" | "inactive" | "suspended";
}

export interface CrossOrgComplianceRequest {
  id: string;
  fromOrgId: string;
  toOrgId: string;
  frameworkCode: FrameworkCode;
  controls: string[];
  purpose: string;
  expiresAt: string;
  status: "pending" | "approved" | "denied" | "expired";
}

export interface ComplianceSharingAgreement {
  id: string;
  orgIds: string[];
  frameworkCode: FrameworkCode;
  sharedControls: string[];
  jurisdiction: Jurisdiction;
  validFrom: string;
  validTo: string;
  trustLevel: number;
}

export interface FederatedComplianceState {
  orgId: string;
  frameworkCode: FrameworkCode;
  overallScore: number;
  controlScores: Map<string, number>;
  lastUpdated: string;
  evidenceHashes: Map<string, string>;
}

export interface RegulatoryReport {
  id: string;
  orgId: string;
  jurisdiction: Jurisdiction;
  frameworkCode: FrameworkCode;
  reportType: "compliance" | "incident" | "audit" | "gap_analysis";
  format: ReportFormat;
  generatedAt: string;
  content: string;
  metadata: ReportMetadata;
}

export interface ReportMetadata {
  period: { from: string; to: string };
  controlCount: number;
  complianceLevel: ComplianceLevel;
  auditor?: string;
  certificationBody?: string;
}

export interface CrossJurisdictionMapping {
  sourceFramework: FrameworkCode;
  sourceControl: string;
  targetFramework: FrameworkCode;
  targetControl: string;
  relationship: "equivalent" | "subset" | "superset" | "related";
  confidence: number;
  jurisdiction: Jurisdiction;
}

export interface MeshSyncEvent {
  id: string;
  type: "compliance_update" | "evidence_share" | "control_change" | "org_status_change";
  orgId: string;
  timestamp: string;
  payload: Record<string, unknown>;
  propagatedTo: string[];
}

export interface ComplianceAggregate {
  orgIds: string[];
  frameworkCode: FrameworkCode;
  aggregateScore: number;
  orgScores: Map<string, number>;
  calculatedAt: string;
  minimumScore: number;
  maximumScore: number;
}
