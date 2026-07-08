export type ControlStatus = 'PASS' | 'FAIL' | 'PARTIAL' | 'NOT_APPLICABLE';
export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type FrameworkType = 'ITAR' | 'EAR' | 'DOD_5200_21' | 'NIST_800_171' | 'CMMC_L1' | 'CMMC_L2' | 'CMMC_L3' | 'CJADC2' | 'AUTONOMOUS_WEAPONS_POLICY';
export type MilitaryDomain = 'LAND' | 'AIR' | 'SEA' | 'SPACE' | 'CYBER';
export type SecurityClassification = 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET';
export type EmbodimentTag = 'HUMANOID' | 'QUADRUPED' | 'AERIAL' | 'GROUND' | 'MARITIME' | 'INDUSTRIAL';
export type RobotType = 'MANIPULATOR' | 'MOBILE_BASE' | 'HUMANOID' | 'DRONE' | 'AUV' | 'UGV';
export type Cjadc2Domain = 'SENSE' | 'DECIDE' | 'ACT' | 'COMMUNICATE';

export interface Gr00tModel {
  id: string;
  name: string;
  version: string;
  parameters: number;
  embodimentTag: EmbodimentTag;
  capabilities: string[];
  exportClassification: SecurityClassification;
  trainingDataOrigin: string;
  weights: {
    precision: string;
    sizeBytes: number;
    sha256: string;
  };
}

export interface RobotConfig {
  id: string;
  name: string;
  type: RobotType;
  embodiment: EmbodimentTag;
  location: string;
  network: {
    isolated: boolean;
    vpnRequired: boolean;
    encryptionStandard: string;
    classification: SecurityClassification;
  };
  operators: string[];
  authorizedCountries: string[];
}

export interface ComplianceAssessment {
  framework: FrameworkType;
  timestamp: string;
  modelId: string;
  overallScore: number;
  status: ControlStatus;
  gaps: ComplianceGap[];
  recommendations: ComplianceRecommendation[];
  controlsChecked: number;
  controlsPassed: number;
  controlsFailed: number;
}

export interface ComplianceGap {
  id: string;
  controlId: string;
  framework: FrameworkType;
  description: string;
  riskLevel: RiskLevel;
  remediation: string;
  deadline: string;
}

export interface ComplianceRecommendation {
  id: string;
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  description: string;
  impact: string;
  effort: string;
}

export interface MilitaryOperation {
  id: string;
  name: string;
  type: string;
  domain: MilitaryDomain;
  classification: SecurityClassification;
  permittedEmbodiments: EmbodimentTag[];
  humanOversightRequired: boolean;
  engagementAuthority: string;
  rulesOfEngagement: string;
}

export interface Cjadc2Component {
  id: string;
  name: string;
  type: string;
  domain: Cjadc2Domain;
  securityLevel: SecurityClassification;
  interoperabilityStandard: string;
  protocols: string[];
  dataFormats: string[];
}

export interface DeploymentConfig {
  model: Gr00tModel;
  robot: RobotConfig;
  network: {
    type: string;
    classification: SecurityClassification;
    encryption: string;
    monitoring: boolean;
    intrusionDetection: boolean;
  };
  security: {
    accessControl: string;
    auditLogging: boolean;
    keyManagement: string;
    patchManagement: string;
    incidentResponse: boolean;
  };
  classification: SecurityClassification;
  operation?: MilitaryOperation;
}

export interface ComplianceReport {
  id: string;
  timestamp: string;
  modelId: string;
  robotId: string;
  overallStatus: ControlStatus;
  overallScore: number;
  frameworkResults: ComplianceAssessment[];
  summary: {
    totalControls: number;
    passed: number;
    failed: number;
    partial: number;
    notApplicable: number;
  };
  criticalFindings: ComplianceGap[];
  exportControlStatus: ExportControlStatus;
  CJADC2Readiness: Cjadc2Readiness;
  deploymentRecommendation: string;
}

export interface ExportControlStatus {
  itarCompliant: boolean;
  earCompliant: boolean;
  exportLicenseRequired: boolean;
  restrictedCountries: string[];
  classification: SecurityClassification;
}

export interface Cjadc2Readiness {
  score: number;
  domainScores: Record<Cjadc2Domain, number>;
  interoperabilityLevel: string;
  securityPosture: string;
}

export interface ItarCheckResult {
  compliant: boolean;
  classification: string;
  restrictions: string[];
  licenseRequired: boolean;
  exportClassification: string;
  deploymentLocations: string[];
  findings: string[];
}

export interface DodCheckResult {
  framework: string;
  compliant: boolean;
  controlsAssessed: number;
  controlsPassed: number;
  controlsFailed: number;
  cmmcLevel: number;
  cuiHandling: boolean;
  findings: string[];
}
