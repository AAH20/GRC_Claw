import type {
  Gr00tModel,
  DeploymentConfig,
  SecurityClassification,
  ComplianceGap,
  ComplianceRecommendation,
  DodCheckResult,
  ControlStatus,
} from './types';

interface NistControl {
  id: string;
  title: string;
  family: string;
  description: string;
  applicableToAI: boolean;
  maturityLevel: number;
}

const NIST_800_171_CONTROLS: NistControl[] = [
  { id: '3.1.1', title: 'Access Control Policy', family: 'Access Control', description: 'Establish access control policy', applicableToAI: true, maturityLevel: 1 },
  { id: '3.1.2', title: 'Access Control Enforcement', family: 'Access Control', description: 'Enforce approved authorizations', applicableToAI: true, maturityLevel: 1 },
  { id: '3.1.13', title: 'Controlled Access', family: 'Access Control', description: 'Control access to CUI', applicableToAI: true, maturityLevel: 2 },
  { id: '3.1.20', title: 'Remote Access', family: 'Access Control', description: 'Manage remote access connections', applicableToAI: true, maturityLevel: 2 },
  { id: '3.4.1', title: 'Baseline Configuration', family: 'Config Management', description: 'Develop baseline configuration', applicableToAI: true, maturityLevel: 1 },
  { id: '3.4.2', title: 'Change Control', family: 'Config Management', description: 'Implement change control', applicableToAI: true, maturityLevel: 2 },
  { id: '3.4.6', title: 'Config Settings Audit', family: 'Config Management', description: 'Audit configuration settings', applicableToAI: true, maturityLevel: 2 },
  { id: '3.5.1', title: 'Identity Management', family: 'Identification Auth', description: 'Identify system users and processes', applicableToAI: true, maturityLevel: 1 },
  { id: '3.5.2', title: 'Authentication', family: 'Identification Auth', description: 'Authenticate system users', applicableToAI: true, maturityLevel: 1 },
  { id: '3.8.1', title: 'Audit Events', family: 'Audit Logging', description: 'Define auditable events', applicableToAI: true, maturityLevel: 1 },
  { id: '3.8.7', title: 'Audit Reduction', family: 'Audit Logging', description: 'Audit reduction and analysis', applicableToAI: true, maturityLevel: 2 },
  { id: '3.11.1', title: 'Risk Assessment', family: 'Risk Assessment', description: 'Conduct risk assessments', applicableToAI: true, maturityLevel: 1 },
  { id: '3.11.2', title: 'Vulnerability Scanning', family: 'Risk Assessment', description: 'Scan for vulnerabilities', applicableToAI: true, maturityLevel: 1 },
  { id: '3.12.1', title: 'Security Assessment', family: 'Security Assessment', description: 'Develop security assessment plan', applicableToAI: true, maturityLevel: 1 },
  { id: '3.13.1', title: 'Network Boundary', family: 'System Protection', description: 'Monitor and control communications', applicableToAI: true, maturityLevel: 1 },
  { id: '3.13.5', title: 'Network Segmentation', family: 'System Protection', description: 'Implement subnetworks', applicableToAI: true, maturityLevel: 2 },
];

const CMMC_LEVELS = {
  1: {
    name: 'CMMC Level 1 - Foundational',
    controls: 17,
    description: 'Safeguard FCI with 17 practices',
    aiControls: ['3.1.1', '3.1.2', '3.5.1', '3.5.2'],
  },
  2: {
    name: 'CMMC Level 2 - Advanced',
    controls: 110,
    description: 'Protect CUI with 110 practices',
    aiControls: NIST_800_171_CONTROLS.filter(c => c.maturityLevel <= 2).map(c => c.id),
  },
  3: {
    name: 'CMMC Level 3 - Expert',
    controls: 110,
    description: 'Advanced threat protection with NIST SP 800-172',
    aiControls: NIST_800_171_CONTROLS.map(c => c.id),
  },
};

const DOD_5200_21_REQUIREMENTS = [
  { id: 'DOD-001', title: 'Risk-Based Approach', requirement: 'Implement risk-based approach to cybersecurity' },
  { id: 'DOD-002', title: 'Data Protection', requirement: 'Protect controlled unclassified information' },
  { id: 'DOD-003', title: 'Incident Response', requirement: 'Establish incident response capabilities' },
  { id: 'DOD-004', title: 'Continuous Monitoring', requirement: 'Implement continuous monitoring program' },
  { id: 'DOD-005', title: 'Supply Chain Risk', requirement: 'Manage supply chain risks' },
  { id: 'DOD-006', title: 'AI/ML Security', requirement: 'Secure AI/ML models and training data' },
];

function calculateCmmcLevel(
  passedControls: number,
  totalControls: number,
  classification: SecurityClassification
): number {
  const ratio = passedControls / totalControls;
  if (classification === 'TOP_SECRET' && ratio >= 1.0) return 3;
  if ((classification === 'SECRET' || classification === 'CONFIDENTIAL') && ratio >= 0.95) return 3;
  if (ratio >= 0.95) return 3;
  if (ratio >= 0.85) return 2;
  if (ratio >= 0.5) return 1;
  return 0;
}

function assessNistControl(
  control: NistControl,
  config: DeploymentConfig
): ControlStatus {
  if (!control.applicableToAI) return 'NOT_APPLICABLE';

  switch (control.id) {
    case '3.1.1':
    case '3.1.2':
      return config.security.accessControl ? 'PASS' : 'FAIL';
    case '3.1.13':
      return config.security.accessControl && config.network.classification !== 'UNCLASSIFIED' ? 'PASS' : 'PARTIAL';
    case '3.4.1':
    case '3.4.2':
      return config.security.patchManagement ? 'PASS' : 'FAIL';
    case '3.4.6':
      return config.security.auditLogging ? 'PASS' : 'FAIL';
    case '3.5.1':
    case '3.5.2':
      return config.security.accessControl ? 'PASS' : 'FAIL';
    case '3.8.1':
    case '3.8.7':
      return config.security.auditLogging ? 'PASS' : 'FAIL';
    case '3.11.1':
      return config.security.incidentResponse ? 'PASS' : 'FAIL';
    case '3.11.2':
      return config.security.incidentResponse ? 'PARTIAL' : 'FAIL';
    case '3.12.1':
      return config.security.auditLogging && config.security.incidentResponse ? 'PASS' : 'PARTIAL';
    case '3.13.1':
      return config.network.intrusionDetection ? 'PASS' : 'FAIL';
    case '3.13.5':
      return config.network.classification !== 'UNCLASSIFIED' ? 'PASS' : 'PARTIAL';
    default:
      return 'PARTIAL';
  }
}

export function assessDodCompliance(
  model: Gr00tModel,
  config: DeploymentConfig,
  targetCmmcLevel: number = 2
): DodCheckResult {
  const findings: string[] = [];
  let controlsPassed = 0;
  let controlsFailed = 0;

  const applicableControls = NIST_800_171_CONTROLS.filter(c => c.applicableToAI);
  for (const control of applicableControls) {
    const status = assessNistControl(control, config);
    if (status === 'PASS') {
      controlsPassed++;
    } else if (status === 'FAIL') {
      controlsFailed++;
      findings.push(`NIST 800-171 ${control.id} (${control.title}) - FAILED`);
    }
  }

  for (const req of DOD_5200_21_REQUIREMENTS) {
    const requirementMet = config.security.incidentResponse &&
      config.security.auditLogging &&
      config.security.patchManagement;
    if (!requirementMet) {
      findings.push(`DoD 5200.21 ${req.id} (${req.title}) - ${req.requirement}`);
    }
  }

  const cmmcLevel = calculateCmmcLevel(controlsPassed, applicableControls.length, config.classification);
  const cuiHandling = config.classification !== 'UNCLASSIFIED' && config.network.encryption;

  return {
    framework: 'NIST 800-171 / DoD 5200.21',
    compliant: cmmcLevel >= targetCmmcLevel && controlsFailed === 0,
    controlsAssessed: applicableControls.length,
    controlsPassed,
    controlsFailed,
    cmmcLevel,
    cuiHandling: cuiHandling as boolean,
    findings,
  };
}

export function mapGr00tToDodControls(
  model: Gr00tModel,
  config: DeploymentConfig
): { gaps: ComplianceGap[]; recommendations: ComplianceRecommendation[] } {
  const gaps: ComplianceGap[] = [];
  const recommendations: ComplianceRecommendation[] = [];

  if (!config.security.auditLogging) {
    gaps.push({
      id: 'DOD-GAP-001',
      controlId: '3.8.1',
      framework: 'NIST_800_171',
      description: 'Audit logging not enabled for GR00T model operations',
      riskLevel: 'HIGH',
      remediation: 'Enable comprehensive audit logging for all model inference and training operations',
      deadline: '30 days',
    });
  }

  if (!config.network.intrusionDetection) {
    gaps.push({
      id: 'DOD-GAP-002',
      controlId: '3.13.1',
      framework: 'NIST_800_171',
      description: 'Network intrusion detection not configured',
      riskLevel: 'HIGH',
      remediation: 'Deploy network intrusion detection for robot communication channels',
      deadline: '60 days',
    });
  }

  if (!config.security.incidentResponse) {
    gaps.push({
      id: 'DOD-GAP-003',
      controlId: '3.12.1',
      framework: 'NIST_800_171',
      description: 'Incident response capability not established',
      riskLevel: 'CRITICAL',
      remediation: 'Establish incident response plan for GR00T model security events',
      deadline: '14 days',
    });
  }

  if (model.parameters > 7_000_000_000) {
    recommendations.push({
      id: 'DOD-REC-001',
      priority: 'P1',
      description: 'Implement model integrity verification using cryptographic hashing',
      impact: 'Ensures model tamper detection for DoD deployments',
      effort: '1-2 weeks',
    });
  }

  recommendations.push({
    id: 'DOD-REC-002',
    priority: 'P1',
    description: 'Deploy model in isolated network segment with DMZ',
    impact: 'Prevents lateral movement from compromised GR00T systems',
    effort: '2-4 weeks',
  });

  recommendations.push({
    id: 'DOD-REC-003',
    priority: 'P2',
    description: 'Implement FIPS 140-2 validated encryption for model weights',
    impact: 'Meets DoD cryptographic requirements for classified data',
    effort: '4-6 weeks',
  });

  return { gaps, recommendations };
}

export function getDodControls(): NistControl[] {
  return [...NIST_800_171_CONTROLS];
}

export function getCmmcLevels(): typeof CMMC_LEVELS {
  return { ...CMMC_LEVELS };
}

export function getDod520021Requirements(): typeof DOD_5200_21_REQUIREMENTS {
  return [...DOD_5200_21_REQUIREMENTS];
}
