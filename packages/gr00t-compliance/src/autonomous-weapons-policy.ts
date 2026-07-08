import type {
  Gr00tModel,
  MilitaryOperation,
  SecurityClassification,
  ComplianceGap,
  ComplianceRecommendation,
} from './types';

interface AutonomyLevel {
  level: number;
  name: string;
  description: string;
  humanOversight: string;
  lethalAuthority: boolean;
  acceptableUse: string[];
}

const AUTONOMY_LEVELS: AutonomyLevel[] = [
  {
    level: 1,
    name: 'Manual Control',
    description: 'All actions require direct human control',
    humanOversight: 'Continuous human-in-the-loop',
    lethalAuthority: false,
    acceptableUse: ['surveillance', 'reconnaissance', 'logistics'],
  },
  {
    level: 2,
    name: 'Supervised Autonomy',
    description: 'AI operates within defined parameters with human oversight',
    humanOversight: 'Human-on-the-loop monitoring',
    lethalAuthority: false,
    acceptableUse: ['navigation', 'mapping', 'search_and_rescue'],
  },
  {
    level: 3,
    name: 'Conditional Autonomy',
    description: 'AI operates autonomously in specific scenarios',
    humanOversight: 'Human-in-the-loop for critical decisions',
    lethalAuthority: false,
    acceptableUse: ['patrol', 'perimeter_security', 'hazardous_materials'],
  },
  {
    level: 4,
    name: 'Supervised Lethal Autonomy',
    description: 'AI can engage targets with human authorization',
    humanOversight: 'Human-on-the-loop with authorization required',
    lethalAuthority: true,
    acceptableUse: ['authorized_engagement', 'force_protection'],
  },
  {
    level: 5,
    name: 'Full Lethal Autonomy',
    description: 'AI can independently engage targets',
    humanOversight: 'Human-out-of-the-loop',
    lethalAuthority: true,
    acceptableUse: ['NOT_PERMITTED'],
  },
];

interface EngagementAuthority {
  id: string;
  level: string;
  requirements: string[];
  restrictions: string[];
}

const ENGAGEMENT_AUTHORITIES: EngagementAuthority[] = [
  {
    id: 'EA-001',
    level: 'Defensive',
    requirements: ['Immediate threat to friendly forces', 'Proportionality assessment', 'Civilian harm mitigation'],
    restrictions: ['Must be within Rules of Engagement', 'Cannot engage beyond defensive perimeter'],
  },
  {
    id: 'EA-002',
    level: 'Offensive',
    requirements: ['Commander authorization', 'Positive identification of target', 'Proportionality assessment', 'Civilian harm assessment', 'Legal review'],
    restrictions: ['Requires explicit orders', 'Must comply with LOAC', 'Subject to post-engagement review'],
  },
  {
    id: 'EA-003',
    level: 'Anticipatory Self-Defense',
    requirements: ['Imminent threat assessment', 'Commander authorization', 'Legal review', 'Proportionality assessment'],
    restrictions: ['Threat must be imminent', 'Cannot preempt without authorization'],
  },
];

interface HumanInLoopRequirement {
  id: string;
  name: string;
  description: string;
  mandatoryForLethal: boolean;
  verificationMethod: string;
}

const HITL_REQUIREMENTS: HumanInLoopRequirement[] = [
  {
    id: 'HITL-001',
    name: 'Authorization Checkpoint',
    description: 'Human must authorize each engagement action',
    mandatoryForLethal: true,
    verificationMethod: 'Biometric authentication + multi-factor verification',
  },
  {
    id: 'HITL-002',
    name: 'Target Verification',
    description: 'Human must verify target identification before engagement',
    mandatoryForLethal: true,
    verificationMethod: 'Visual/audio confirmation by operator',
  },
  {
    id: 'HITL-003',
    name: 'Proportionality Assessment',
    description: 'Human must assess proportionality of response',
    mandatoryForLethal: true,
    verificationMethod: 'Operator decision log with rationale',
  },
  {
    id: 'HITL-004',
    name: 'Civilian Harm Mitigation',
    description: 'Human must assess and mitigate civilian harm',
    mandatoryForLethal: true,
    verificationMethod: 'Environmental assessment and no-strike list verification',
  },
  {
    id: 'HITL-005',
    name: 'Continuous Monitoring',
    description: 'Human must continuously monitor autonomous operations',
    mandatoryForLethal: false,
    verificationMethod: 'Telemetry and video feed monitoring with alert system',
  },
];

const LETHAL_RESTRICTIONS = [
  'No fully autonomous lethal engagement without human authorization',
  'AI cannot select and engage targets without human approval',
  'Must implement reliable kill switch accessible at all times',
  'Must maintain ability to abort engagement at any time',
  'Must not engage targets that cannot be positively identified',
  'Must comply with Law of Armed Conflict (LOAC) principles',
  'Must maintain engagement logs for post-action review',
];

function assessHumanInLoop(
  model: Gr00tModel,
  operation: MilitaryOperation
): {
  compliant: boolean;
  level: number;
  findings: string[];
  missingRequirements: string[];
} {
  const findings: string[] = [];
  const missingRequirements: string[] = [];
  let compliant = true;

  const isLethal = operation.type.includes('lethal') || operation.type.includes('combat');
  const requiredLevel = isLethal ? 4 : 3;

  const hasHumanOversight = model.capabilities.includes('human-in-the-loop') ||
    model.capabilities.includes('human_oversight') ||
    model.capabilities.includes('supervised');

  if (!hasHumanOversight) {
    compliant = false;
    findings.push('Model does not declare human-in-the-loop capability');
  }

  if (isLethal && !operation.humanOversightRequired) {
    compliant = false;
    findings.push('Lethal operation requires human oversight but it is not required');
  }

  for (const req of HITL_REQUIREMENTS) {
    if (req.mandatoryForLethal && isLethal) {
      const capabilityPresent = model.capabilities.some(cap =>
        cap.toLowerCase().includes(req.name.toLowerCase().split(' ')[0].toLowerCase())
      );
      if (!capabilityPresent) {
        missingRequirements.push(req.id);
        findings.push(`Missing HITL requirement: ${req.name}`);
      }
    }
  }

  return {
    compliant,
    level: requiredLevel,
    findings,
    missingRequirements,
  };
}

function assessLethalAutonomy(
  model: Gr00tModel,
  operation: MilitaryOperation
): {
  permitted: boolean;
  level: AutonomyLevel;
  findings: string[];
  restrictions: string[];
} {
  const findings: string[] = [];
  const restrictions: string[] = [];

  const canEngage = model.capabilities.some(c =>
    c.includes('engage') || c.includes('lethal') || c.includes('weapons')
  );

  const isLethalOperation = operation.type.includes('lethal') || operation.type.includes('combat');

  let permittedAutonomyLevel: AutonomyLevel;

  if (isLethalOperation) {
    if (operation.classification === 'TOP_SECRET') {
      permittedAutonomyLevel = AUTONOMY_LEVELS[3];
      findings.push('Top Secret operations limited to supervised lethal autonomy (Level 4)');
    } else {
      permittedAutonomyLevel = AUTONOMY_LEVELS[2];
      findings.push('Standard operations limited to conditional autonomy (Level 3)');
    }

    if (canEngage) {
      findings.push('Model has engagement capabilities - additional safeguards required');
      restrictions.push(...LETHAL_RESTRICTIONS);
    }
  } else {
    permittedAutonomyLevel = AUTONOMY_LEVELS[2];
    findings.push('Non-lethal operations permitted up to conditional autonomy (Level 3)');
  }

  const permitted = !canEngage || isLethalOperation;

  return {
    permitted,
    level: permittedAutonomyLevel,
    findings,
    restrictions,
  };
}

export function assessAutonomousWeaponsCompliance(
  model: Gr00tModel,
  operation: MilitaryOperation
): {
  compliant: boolean;
  hitlCompliance: ReturnType<typeof assessHumanInLoop>;
  lethalAutonomy: ReturnType<typeof assessLethalAutonomy>;
  gaps: ComplianceGap[];
  recommendations: ComplianceRecommendation[];
} {
  const hitlCompliance = assessHumanInLoop(model, operation);
  const lethalAutonomy = assessLethalAutonomy(model, operation);

  const gaps: ComplianceGap[] = [];
  const recommendations: ComplianceRecommendation[] = [];

  if (!hitlCompliance.compliant) {
    gaps.push({
      id: 'WEAP-GAP-001',
      controlId: 'HITL-ALL',
      framework: 'AUTONOMOUS_WEAPONS_POLICY',
      description: 'Human-in-the-loop requirements not fully met',
      riskLevel: 'CRITICAL',
      remediation: 'Implement all mandatory HITL requirements for lethal operations',
      deadline: 'IMMEDIATE',
    });
  }

  for (const missing of hitlCompliance.missingRequirements) {
    gaps.push({
      id: `WEAP-GAP-${missing}`,
      controlId: missing,
      framework: 'AUTONOMOUS_WEAPONS_POLICY',
      description: `Missing HITL requirement: ${missing}`,
      riskLevel: 'CRITICAL',
      remediation: `Implement ${missing} capability before deployment`,
      deadline: '30 days',
    });
  }

  if (!lethalAutonomy.permitted) {
    gaps.push({
      id: 'WEAP-GAP-LETHAL',
      controlId: 'LETHAL-AUTH',
      framework: 'AUTONOMOUS_WEAPONS_POLICY',
      description: 'Lethal autonomy restrictions not met',
      riskLevel: 'CRITICAL',
      remediation: 'Disable lethal capabilities or implement required safeguards',
      deadline: 'IMMEDIATE',
    });
  }

  recommendations.push({
    id: 'WEAP-REC-001',
    priority: 'P0',
    description: 'Implement multi-factor authentication for engagement authorization',
    impact: 'Ensures only authorized personnel can approve lethal actions',
    effort: '2-3 weeks',
  });

  recommendations.push({
    id: 'WEAP-REC-002',
    priority: 'P0',
    description: 'Deploy engagement logging with immutable audit trail',
    impact: 'Provides accountability and post-action review capability',
    effort: '2-4 weeks',
  });

  recommendations.push({
    id: 'WEAP-REC-003',
    priority: 'P1',
    description: 'Implement automatic disengagement on loss of communication',
    impact: 'Ensures graceful degradation when human oversight is lost',
    effort: '1-2 weeks',
  });

  recommendations.push({
    id: 'WEAP-REC-004',
    priority: 'P1',
    description: 'Add positive identification verification for target engagement',
    impact: 'Prevents engagement of unidentified or friendly targets',
    effort: '3-4 weeks',
  });

  return {
    compliant: hitlCompliance.compliant && lethalAutonomy.permitted,
    hitlCompliance,
    lethalAutonomy,
    gaps,
    recommendations,
  };
}

export function getAutonomyLevels(): AutonomyLevel[] {
  return [...AUTONOMY_LEVELS];
}

export function getEngagementAuthorities(): EngagementAuthority[] {
  return [...ENGAGEMENT_AUTHORITIES];
}

export function getHitlRequirements(): HumanInLoopRequirement[] {
  return [...HITL_REQUIREMENTS];
}

export function getLethalRestrictions(): string[] {
  return [...LETHAL_RESTRICTIONS];
}
