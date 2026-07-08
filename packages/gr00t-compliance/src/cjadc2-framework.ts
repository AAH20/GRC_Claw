import type {
  Gr00tModel,
  Cjadc2Component,
  Cjadc2Domain,
  SecurityClassification,
  ComplianceGap,
  ComplianceRecommendation,
  Cjadc2Readiness,
} from './types';

interface Cjadc2Requirement {
  id: string;
  domain: Cjadc2Domain;
  title: string;
  description: string;
  mandatory: boolean;
  securityLevel: SecurityClassification;
}

const CJADC2_REQUIREMENTS: Cjadc2Requirement[] = [
  { id: 'CJADC2-SENSE-001', domain: 'SENSE', title: 'Sensor Fusion', description: 'Integrate multi-domain sensor data into unified picture', mandatory: true, securityLevel: 'CONFIDENTIAL' },
  { id: 'CJADC2-SENSE-002', domain: 'SENSE', title: 'Data Standardization', description: 'Use NATO STANAG 4586 / STANAG 4607 for sensor data', mandatory: true, securityLevel: 'UNCLASSIFIED' },
  { id: 'CJADC2-SENSE-003', domain: 'SENSE', title: 'Edge Processing', description: 'Process sensor data at the edge for latency requirements', mandatory: true, securityLevel: 'UNCLASSIFIED' },
  { id: 'CJADC2-SENSE-004', domain: 'SENSE', title: 'AI-Enhanced Sensing', description: 'Use AI/ML for sensor data classification and anomaly detection', mandatory: false, securityLevel: 'CONFIDENTIAL' },

  { id: 'CJADC2-DECIDE-001', domain: 'DECIDE', title: 'Decision Support', description: 'Provide AI-augmented decision support to commanders', mandatory: true, securityLevel: 'SECRET' },
  { id: 'CJADC2-DECIDE-002', domain: 'DECIDE', title: 'Human-in-the-Loop', description: 'Maintain human oversight for all lethal decisions', mandatory: true, securityLevel: 'SECRET' },
  { id: 'CJADC2-DECIDE-003', domain: 'DECIDE', title: 'Explainable AI', description: 'Provide explainable decision rationale for AI recommendations', mandatory: true, securityLevel: 'CONFIDENTIAL' },
  { id: 'CJADC2-DECIDE-004', domain: 'DECIDE', title: 'Bias Detection', description: 'Monitor and mitigate AI bias in operational recommendations', mandatory: false, securityLevel: 'UNCLASSIFIED' },

  { id: 'CJADC2-ACT-001', domain: 'ACT', title: 'Autonomous Execution', description: 'Execute approved autonomous actions within defined boundaries', mandatory: true, securityLevel: 'SECRET' },
  { id: 'CJADC2-ACT-002', domain: 'ACT', title: 'Safety Constraints', description: 'Enforce safety constraints and rules of engagement', mandatory: true, securityLevel: 'SECRET' },
  { id: 'CJADC2-ACT-003', domain: 'ACT', title: 'Kill Switch', description: 'Implement reliable emergency shutdown capability', mandatory: true, securityLevel: 'TOP_SECRET' },
  { id: 'CJADC2-ACT-004', domain: 'ACT', title: 'Graceful Degradation', description: 'Maintain safe operation during system failures', mandatory: true, securityLevel: 'CONFIDENTIAL' },

  { id: 'CJADC2-COMM-001', domain: 'COMMUNICATE', title: 'Interoperability', description: 'Support NATO interoperability standards (STANAG 4406/4586)', mandatory: true, securityLevel: 'UNCLASSIFIED' },
  { id: 'CJADC2-COMM-002', domain: 'COMMUNICATE', title: 'Low-Latency Comms', description: 'Maintain sub-100ms latency for time-critical data', mandatory: true, securityLevel: 'UNCLASSIFIED' },
  { id: 'CJADC2-COMM-003', domain: 'COMMUNICATE', title: 'Encrypted Channels', description: 'Use NSA-approved Type 1 encryption for classified data', mandatory: true, securityLevel: 'SECRET' },
  { id: 'CJADC2-COMM-004', domain: 'COMMUNICATE', title: 'Mesh Networking', description: 'Support tactical mesh networking for distributed operations', mandatory: false, securityLevel: 'CONFIDENTIAL' },
];

const STANAG_PROTOCOLS: Record<string, string> = {
  'STANAG_4586': 'NATO Standard for UAV Control',
  'STANAG_4607': 'NATO Standard for GMTI',
  'STANAG_4406': 'NATO Standard for Military Messaging',
  'STANAG_4609': 'NATO Standard for Motion Imagery',
  'STANAG_5500': 'NATO Standard for Information Exchange',
};

function assessComponent(
  component: Cjadc2Component,
  requirements: Cjadc2Requirement[]
): { passed: number; failed: number; passedRequirements: string[]; failedRequirements: string[] } {
  let passed = 0;
  let failed = 0;
  const passedRequirements: string[] = [];
  const failedRequirements: string[] = [];

  const domainRequirements = requirements.filter(r => r.domain === component.domain);

  for (const req of domainRequirements) {
    const hasCapability = component.protocols.some(p =>
      p.toLowerCase().includes(req.title.toLowerCase().split(' ')[0].toLowerCase()) ||
      req.title.toLowerCase().includes(p.toLowerCase().split(' ')[0].toLowerCase())
    );

    const meetsSecurity = getSecurityLevelNumber(component.securityLevel) >= getSecurityLevelNumber(req.securityLevel);

    if (hasCapability && meetsSecurity) {
      passed++;
      passedRequirements.push(req.id);
    } else {
      failed++;
      failedRequirements.push(req.id);
    }
  }

  return { passed, failed, passedRequirements, failedRequirements };
}

function getSecurityLevelNumber(level: SecurityClassification): number {
  const levels: Record<SecurityClassification, number> = {
    'UNCLASSIFIED': 0,
    'CONFIDENTIAL': 1,
    'SECRET': 2,
    'TOP_SECRET': 3,
  };
  return levels[level];
}

function calculateDomainScore(domain: Cjadc2Domain, components: Cjadc2Component[]): number {
  const domainComponents = components.filter(c => c.domain === domain);
  if (domainComponents.length === 0) return 0;

  const totalRequirements = CJADC2_REQUIREMENTS.filter(r => r.domain === domain).length;
  let totalPassed = 0;

  for (const component of domainComponents) {
    const result = assessComponent(component, CJADC2_REQUIREMENTS);
    totalPassed += result.passed;
  }

  return Math.min(100, Math.round((totalPassed / totalRequirements) * 100));
}

export function assessCjadc2Compliance(
  model: Gr00tModel,
  components: Cjadc2Component[]
): {
  readiness: Cjadc2Readiness;
  gaps: ComplianceGap[];
  recommendations: ComplianceRecommendation[];
  componentResults: Array<{
    component: Cjadc2Component;
    passed: number;
    failed: number;
    passedRequirements: string[];
    failedRequirements: string[];
  }>;
} {
  const gaps: ComplianceGap[] = [];
  const recommendations: ComplianceRecommendation[] = [];
  const componentResults: Array<{
    component: Cjadc2Component;
    passed: number;
    failed: number;
    passedRequirements: string[];
    failedRequirements: string[];
  }> = [];

  for (const component of components) {
    const result = assessComponent(component, CJADC2_REQUIREMENTS);
    componentResults.push({ component, ...result });

    if (result.failed > 0) {
      gaps.push({
        id: `CJADC2-GAP-${component.id}`,
        controlId: result.failedRequirements.join(','),
        framework: 'CJADC2',
        description: `Component ${component.name} fails ${result.failed} CJADC2 requirements in ${component.domain} domain`,
        riskLevel: result.failed > 2 ? 'CRITICAL' : result.failed > 1 ? 'HIGH' : 'MEDIUM',
        remediation: `Implement missing capabilities for ${component.domain} domain compliance`,
        deadline: '90 days',
      });
    }
  }

  const domainScores: Record<Cjadc2Domain, number> = {
    SENSE: calculateDomainScore('SENSE', components),
    DECIDE: calculateDomainScore('DECIDE', components),
    ACT: calculateDomainScore('ACT', components),
    COMMUNICATE: calculateDomainScore('COMMUNICATE', components),
  };

  const overallScore = Math.round(
    (domainScores.SENSE + domainScores.DECIDE + domainScores.ACT + domainScores.COMMUNICATE) / 4
  );

  let interoperabilityLevel = 'Basic';
  if (overallScore >= 90) interoperabilityLevel = 'Full Interoperability';
  else if (overallScore >= 75) interoperabilityLevel = 'Advanced Interoperability';
  else if (overallScore >= 50) interoperabilityLevel = 'Partial Interoperability';

  const hasAllDomains = ['SENSE', 'DECIDE', 'ACT', 'COMMUNICATE'].every(
    d => components.some(c => c.domain === d)
  );

  if (!hasAllDomains) {
    gaps.push({
      id: 'CJADC2-GAP-MISSING-DOMAIN',
      controlId: 'CJADC2-ALL-DOMAINS',
      framework: 'CJADC2',
      description: 'Not all CJADC2 domains are represented in component architecture',
      riskLevel: 'HIGH',
      remediation: 'Ensure GR00T deployment covers Sense, Decide, Act, and Communicate domains',
      deadline: '60 days',
    });
  }

  recommendations.push({
    id: 'CJADC2-REC-001',
    priority: 'P0',
    description: 'Implement STANAG 4586 compliance for all robotic components',
    impact: 'Ensures NATO interoperability for joint operations',
    effort: '4-8 weeks',
  });

  recommendations.push({
    id: 'CJADC2-REC-002',
    priority: 'P1',
    description: 'Deploy low-latency communication channels for time-critical CJADC2 data',
    impact: 'Meets sub-100ms latency requirement for tactical operations',
    effort: '2-4 weeks',
  });

  recommendations.push({
    id: 'CJADC2-REC-003',
    priority: 'P1',
    description: 'Implement explainable AI module for decision support recommendations',
    impact: 'Provides commander transparency for AI-augmented decisions',
    effort: '4-6 weeks',
  });

  return {
    readiness: {
      score: overallScore,
      domainScores,
      interoperabilityLevel,
      securityPosture: overallScore >= 80 ? 'Strong' : overallScore >= 60 ? 'Adequate' : 'Weak',
    },
    gaps,
    recommendations,
    componentResults,
  };
}

export function getCjadc2Requirements(): Cjadc2Requirement[] {
  return [...CJADC2_REQUIREMENTS];
}

export function getStanagProtocols(): Record<string, string> {
  return { ...STANAG_PROTOCOLS };
}

export function getDomainRequirements(domain: Cjadc2Domain): Cjadc2Requirement[] {
  return CJADC2_REQUIREMENTS.filter(r => r.domain === domain);
}
