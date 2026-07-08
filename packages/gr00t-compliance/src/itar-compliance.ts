import crypto from 'crypto';
import type { Gr00tModel, ItarCheckResult, SecurityClassification, ComplianceGap, ComplianceRecommendation } from './types';

interface ItarCategory {
  category: string;
  description: string;
  restrictions: string[];
  licenseRequired: boolean;
}

const ITAR_CATEGORIES: Record<string, ItarCategory> = {
  'USML_XI': {
    category: 'USML Category XI',
    description: 'Military Electronics and AI/ML Models with defense applications',
    restrictions: ['No export to restricted countries', 'Requires DDTC authorization', 'End-use monitoring required'],
    licenseRequired: true,
  },
  'USML_IX': {
    category: 'USML Category IX',
    description: 'Training equipment and simulation systems',
    restrictions: ['NATO allies only without license', 'Technology transfer controls apply', 'Classified data handling required'],
    licenseRequired: true,
  },
  'USML_IV': {
    category: 'USML Category IV',
    description: 'Launch vehicles, guided missiles, ballistic missiles',
    restrictions: ['Strictly controlled', 'No re-export without authorization', 'End-use certification required'],
    licenseRequired: true,
  },
  'EAR_9A': {
    category: 'EAR ECCN 9A004',
    description: 'Unmanned aerial vehicles and autonomous systems',
    restrictions: ['Technology requires license for certain countries', 'Dual-use controls apply'],
    licenseRequired: false,
  },
};

const RESTRICTED_COUNTRIES = [
  'CN', 'RU', 'IR', 'KP', 'CU', 'SY', 'VE', 'MM', 'BY', 'RU-BY',
];

const EMBODIMENT_ITAR_RISK: Record<string, number> = {
  'HUMANOID': 0.9,
  'QUADRUPED': 0.7,
  'AERIAL': 0.8,
  'GROUND': 0.6,
  'MARITIME': 0.8,
  'INDUSTRIAL': 0.4,
};

export function classifyItarCategory(model: Gr00tModel): ItarCategory {
  const isMilitary = model.exportClassification === 'SECRET' || model.exportClassification === 'TOP_SECRET';
  const hasDefenseCapabilities = model.capabilities.some(c =>
    c.includes('autonomous') || c.includes('lethal') || c.includes('weapons') || c.includes('surveillance')
  );

  if (isMilitary && hasDefenseCapabilities) {
    return ITAR_CATEGORIES['USML_XI'];
  }
  if (isMilitary) {
    return ITAR_CATEGORIES['USML_IX'];
  }
  if (hasDefenseCapabilities) {
    return ITAR_CATEGORIES['USML_IV'];
  }
  return ITAR_CATEGORIES['EAR_9A'];
}

export function checkItarCompliance(model: Gr00tModel, deploymentCountries: string[]): ItarCheckResult {
  const findings: string[] = [];
  let compliant = true;
  const restrictions: string[] = [];

  const itarCategory = classifyItarCategory(model);

  const restrictedInDeployment = deploymentCountries.filter(c => RESTRICTED_COUNTRIES.includes(c));
  if (restrictedInDeployment.length > 0) {
    compliant = false;
    findings.push(`Deployment to restricted countries: ${restrictedInDeployment.join(', ')}`);
    restrictions.push(`Cannot deploy to ITAR-restricted countries: ${restrictedInDeployment.join(', ')}`);
  }

  if (model.exportClassification === 'TOP_SECRET' || model.exportClassification === 'SECRET') {
    findings.push('Model contains classified content - ITAR controls strictly apply');
    restrictions.push('Requires DDTC authorization for any foreign access');
  }

  if (model.parameters > 7_000_000_000) {
    findings.push('Large parameter model may contain sensitive training data patterns');
    restrictions.push('Training data origin must be verified for ITAR compliance');
  }

  const embodimentRisk = EMBODIMENT_ITAR_RISK[model.embodimentTag] ?? 0.5;
  if (embodimentRisk > 0.7) {
    findings.push(`High-risk embodiment type: ${model.embodimentTag}`);
    restrictions.push('Enhanced export controls apply for this embodiment');
  }

  return {
    compliant,
    classification: itarCategory.category,
    restrictions: [...itarCategory.restrictions, ...restrictions],
    licenseRequired: itarCategory.licenseRequired,
    exportClassification: model.exportClassification,
    deploymentLocations: deploymentCountries.filter(c => !RESTRICTED_COUNTRIES.includes(c)),
    findings,
  };
}

export function generateItarComplianceReport(
  model: Gr00tModel,
  deploymentCountries: string[]
): {
  result: ItarCheckResult;
  gaps: ComplianceGap[];
  recommendations: ComplianceRecommendation[];
  complianceHash: string;
} {
  const result = checkItarCompliance(model, deploymentCountries);
  const gaps: ComplianceGap[] = [];
  const recommendations: ComplianceRecommendation[] = [];

  if (!result.compliant) {
    gaps.push({
      id: 'ITAR-GAP-001',
      controlId: 'ITAR-22-CFR-120-125',
      framework: 'ITAR',
      description: 'Model deployment violates ITAR restricted country controls',
      riskLevel: 'CRITICAL',
      remediation: 'Remove restricted countries from deployment scope or obtain DDTC export license',
      deadline: 'IMMEDIATE',
    });
  }

  if (result.licenseRequired && result.exportClassification !== 'UNCLASSIFIED') {
    recommendations.push({
      id: 'ITAR-REC-001',
      priority: 'P0',
      description: 'Obtain DDTC export authorization before any foreign deployment',
      impact: 'Prevents ITAR violations and potential criminal penalties',
      effort: '6-12 weeks for DDTC processing',
    });
  }

  recommendations.push({
    id: 'ITAR-REC-002',
    priority: 'P1',
    description: 'Implement end-use monitoring and reporting for all deployments',
    impact: 'Ensures ongoing compliance and audit readiness',
    effort: '2-4 weeks to implement monitoring',
  });

  recommendations.push({
    id: 'ITAR-REC-003',
    priority: 'P2',
    description: 'Maintain training data provenance documentation',
    impact: 'Demonstrates compliance during audits',
    effort: '1 week to document existing records',
  });

  const complianceData = JSON.stringify({ model: model.id, result, gaps });
  const complianceHash = crypto.createHash('sha256').update(complianceData).digest('hex');

  return { result, gaps, recommendations, complianceHash };
}

export function getItarRestrictions(): Record<string, string> {
  return {
    'RESTRICTED_COUNTRIES': RESTRICTED_COUNTRIES.join(', '),
    'CATEGORIES': Object.values(ITAR_CATEGORIES).map(c => `${c.category}: ${c.description}`).join('; '),
    'PENALTIES': 'Criminal penalties up to $1M and 20 years imprisonment per violation',
    'REPORTING': 'Annual DDTC reporting required for active licenses',
  };
}
