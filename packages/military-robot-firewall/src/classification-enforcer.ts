import { createHash, randomBytes } from 'node:crypto';
import type { RobotAction, ClassificationLevel, DataHandlingRequirement } from './types';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

const CLASSIFICATION_LEVELS: Record<ClassificationLevel, number> = {
  UNCLASSIFIED: 0,
  CONFIDENTIAL: 1,
  SECRET: 2,
  TOP_SECRET: 3,
  SCI: 4,
};

const HANDLING_REQUIREMENTS: Record<ClassificationLevel, DataHandlingRequirement[]> = {
  UNCLASSIFIED: [],
  CONFIDENTIAL: ['no_foreign_disclosure'],
  SECRET: ['no_foreign_disclosure', 'no_transfer_outside_scip', 'dissemination_control'],
  TOP_SECRET: ['no_foreign_disclosure', 'no_transfer_outside_scip', 'originator_control', 'dissemination_control'],
  SCI: ['no_abbreviations', 'no_foreign_disclosure', 'no_transfer_outside_scip', 'originator_control', 'dissemination_control'],
};

const CROSS_DOMAIN_SOLUTIONS: Record<string, ClassificationLevel[]> = {
  'high_to_low_gw': ['TOP_SECRET', 'SCI'],
  'low_to_high_gw': ['SECRET', 'TOP_SECRET', 'SCI'],
  'sci_to_ts_gw': ['SCI'],
};

export interface ClassificationCheckResult {
  allowed: boolean;
  reason: string;
  violations: string[];
  handlingRequirements: DataHandlingRequirement[];
  needToKnowVerified: boolean;
  crossDomainSolution?: string;
}

export class ClassificationEnforcer {
  private operatorClearances: Map<string, ClassificationLevel> = new Map();
  private needToKnowRegistry: Map<string, ClassificationLevel[]> = new Map();

  constructor() {
    this.loadDefaults();
  }

  private loadDefaults(): void
 {
    // Default cross-domain solutions
    // (already defined in CROSS_DOMAIN_SOLUTIONS constant)
  }

  enforceClassification(action: RobotAction): ClassificationCheckResult {
    const violations: string[] = [];
    const actionLevel = CLASSIFICATION_LEVELS[action.classification];
    const targetLevel = CLASSIFICATION_LEVELS[action.target.classification];

    // 1. Check classification boundary - action cannot exceed target classification
    if (actionLevel > targetLevel) {
      violations.push('classification_boundary_exceeded');
    }

    // 2. Check operator clearance
    const operatorClearance = this.operatorClearances.get(action.operatorId);
    if (operatorClearance) {
      const clearanceLevel = CLASSIFICATION_LEVELS[operatorClearance];
      if (actionLevel > clearanceLevel) {
        violations.push('operator_clearance_insufficient');
      }
    }

    // 3. Check need-to-know
    const needToKnow = this.needToKnowRegistry.get(action.operatorId);
    if (needToKnow && !needToKnow.includes(action.classification)) {
      violations.push('need_to_know_not_established');
    }

    // 4. Check data handling requirements
    const handlingRequirements = HANDLING_REQUIREMENTS[action.classification];

    // 5. Check cross-domain solution requirements for SCI
    let crossDomainSolution: string | undefined;
    if (action.classification === 'SCI' && action.target.classification !== 'SCI') {
      crossDomainSolution = this.checkCrossDomainRequirements(action);
      if (!crossDomainSolution) {
        violations.push('cross_domain_solution_required');
      }
    }

    // 6. Check authorization code classification level
    if (action.authorization.authorizationCode && action.classification !== 'UNCLASSIFIED') {
      if (!action.authorization.authorizationCode.startsWith(action.classification)) {
        violations.push('authorization_code_classification_mismatch');
      }
    }

    const allowed = violations.length === 0;

    return {
      allowed,
      reason: allowed ? 'classification_enforced' : violations.join(';'),
      violations,
      handlingRequirements,
      needToKnowVerified: !violations.includes('need_to_know_not_established'),
      crossDomainSolution,
    };
  }

  generateReceipt(action: RobotAction, result: ClassificationCheckResult): {
    receiptId: string;
    actionId: string;
    classification: ClassificationLevel;
    handlingRequirements: DataHandlingRequirement[];
    needToKnowVerified: boolean;
    crossDomainSolution?: string;
    timestamp: string;
    signedHash: string;
  } {
    const receiptId = `cls_receipt:${randomBytes(16).toString('hex').slice(0, 16)}`;
    const timestamp = new Date().toISOString();
    const receiptData = {
      receiptId,
      actionId: action.id,
      classification: action.classification,
      handlingRequirements: result.handlingRequirements,
      needToKnowVerified: result.needToKnowVerified,
      crossDomainSolution: result.crossDomainSolution,
      timestamp,
    };
    const signedHash = sha256(receiptData);

    return { ...receiptData, signedHash };
  }

  setOperatorClearance(operatorId: string, clearance: ClassificationLevel): void {
    this.operatorClearances.set(operatorId, clearance);
  }

  setNeedToKnow(operatorId: string, classifications: ClassificationLevel[]): void {
    this.needToKnowRegistry.set(operatorId, classifications);
  }

  getHandlingRequirements(classification: ClassificationLevel): DataHandlingRequirement[] {
    return HANDLING_REQUIREMENTS[classification];
  }

  private checkCrossDomainRequirements(action: RobotAction): string | undefined {
    const actionLevel = CLASSIFICATION_LEVELS[action.classification];
    const targetLevel = CLASSIFICATION_LEVELS[action.target.classification];

    if (actionLevel > targetLevel) {
      if (actionLevel === 4 && targetLevel <= 3) {
        return 'sci_to_ts_gw';
      }
      if (actionLevel === 3 && targetLevel <= 2) {
        return 'high_to_low_gw';
      }
      return 'low_to_high_gw';
    }
    return undefined;
  }
}
