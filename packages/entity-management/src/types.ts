export type EntityType = 'parent' | 'subsidiary' | 'division' | 'branch' | 'subsidiary';

export type RelationshipType =
  | 'ownership'
  | 'subsidiary'
  | 'division'
  | 'branch'
  | 'joint_venture'
  | 'franchise';

export type RelationshipStatus = 'active' | 'inactive' | 'pending' | 'dissolved';

export type FrameworkCode =
  | 'iso27001'
  | 'nist-csf'
  | 'soc2'
  | 'iso42001'
  | 'eu-ai-act'
  | 'dora'
  | 'nis2'
  | 'hipaa'
  | 'pci-dss'
  | 'fedramp'
  | 'cmmc'
  | 'gdpr'
  | 'lgpd'
  | 'pipl'
  | 'tisax'
  | 'popia';

export interface Entity {
  id: string;
  name: string;
  type: EntityType;
  jurisdiction: string;
  industry: string;
  parentId?: string;
  metadata: EntityMetadata;
  complianceScore: number;
  riskScore: number;
  createdAt: string;
  updatedAt: string;
}

export interface EntityMetadata {
  employeeCount?: number;
  annualRevenue?: number;
  headquarters?: string;
  fiscalYearEnd?: string;
  industryCode?: string;
  regulatoryScope?: string[];
  tags?: string[];
  [key: string]: unknown;
}

export interface EntityRelationship {
  id: string;
  parentEntityId: string;
  childEntityId: string;
  relationshipType: RelationshipType;
  status: RelationshipStatus;
  createdAt: string;
  updatedAt: string;
}

export interface EntityComplianceStatus {
  entityId: string;
  framework: FrameworkCode;
  totalControls: number;
  compliant: number;
  nonCompliant: number;
  notAssessed: number;
  lastAssessedAt: string;
}

export interface JurisdictionCoverage {
  jurisdiction: string;
  entityIds: string[];
  frameworks: FrameworkCode[];
  complianceScores: Record<string, number>;
}

export interface EntityTreeNode {
  entity: Entity;
  children: EntityTreeNode[];
  complianceStatuses: EntityComplianceStatus[];
}

export interface CrossEntityRisk {
  riskId: string;
  affectedEntityIds: string[];
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  likelihood: number;
  impact: number;
  riskScore: number;
  sharedControlIds: string[];
}

export interface ConsolidatedReport {
  generatedAt: string;
  entities: Entity[];
  overallComplianceScore: number;
  overallRiskScore: number;
  jurisdictionBreakdown: JurisdictionCoverage[];
  frameworkBreakdown: FrameworkComplianceBreakdown[];
  crossEntityRisks: CrossEntityRisk[];
  weakestEntities: WeakestEntitySummary[];
}

export interface FrameworkComplianceBreakdown {
  framework: FrameworkCode;
  totalControls: number;
  compliant: number;
  nonCompliant: number;
  notAssessed: number;
  scorePercent: number;
  entityScores: Record<string, number>;
}

export interface WeakestEntitySummary {
  entityId: string;
  entityName: string;
  complianceScore: number;
  riskScore: number;
  biggestGap: string;
}

export interface WeightedComplianceScore {
  entityId: string;
  entityName: string;
  rawScore: number;
  weight: number;
  weightedScore: number;
}

export interface GroupCompliancePosture {
  totalEntities: number;
  compliantEntities: number;
  partiallyCompliantEntities: number;
  nonCompliantEntities: number;
  unassessedEntities: number;
  weightedComplianceScore: number;
  entityScores: WeightedComplianceScore[];
}

export interface SharedControlMapping {
  controlId: string;
  controlCode: string;
  entityIds: string[];
  status: Record<string, 'compliant' | 'non-compliant' | 'partial' | 'not-applicable' | 'not-tested'>;
  shared: boolean;
}

export interface IndustryFrameworkRecommendation {
  industry: string;
  frameworks: FrameworkCode[];
  rationale: string;
  priority: 'required' | 'recommended' | 'optional';
}
