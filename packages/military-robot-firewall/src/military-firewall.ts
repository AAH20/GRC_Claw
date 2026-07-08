import { createHash, randomBytes } from 'node:crypto';
import type {
  RobotAction,
  FirewallDecision,
  PolicyRule,
  EngagementAuthority,
  HumanInLoopRequirement,
  MilitaryFirewallConfig,
  ClassificationLevel,
  EngagementResult,
} from './types';
import { EngagementAuthorityEnforcer } from './engagement-authority';
import { HumanInLoopEnforcer } from './human-in-loop';
import { ClassificationEnforcer } from './classification-enforcer';
import { MilitaryAuditLogger } from './audit-logger';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

function generateReceiptId(prefix: string): string {
  return `${prefix}:${randomBytes(16).toString('hex').slice(0, 16)}`;
}

const DEFAULT_CONFIG: MilitaryFirewallConfig = {
  defaultClassification: 'UNCLASSIFIED',
  maxCollateralDamageThreshold: 10,
  hitlTimeoutSeconds: 30,
  requirePIDForAllEngagements: true,
  enforceDistinction: true,
  enforceProportionality: true,
  classificationBoundaryEnforcement: true,
  engagementAuthorityRequired: true,
  auditRetentionDays: 365,
};

export class MilitaryRobotFirewall {
  private config: MilitaryFirewallConfig;
  private policyRules: PolicyRule[];
  private engagementAuthorities: Map<string, EngagementAuthority> = new Map();
  private hitlRequirements: Map<string, HumanInLoopRequirement> = new Map();
  private pendingApprovals: Map<string, { action: RobotAction; timestamp: number }> = new Map();
  private engagementEnforcer: EngagementAuthorityEnforcer;
  private hitlEnforcer: HumanInLoopEnforcer;
  private classificationEnforcer: ClassificationEnforcer;
  private auditLogger: MilitaryAuditLogger;

  constructor(config?: Partial<MilitaryFirewallConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.policyRules = [];
    this.engagementEnforcer = new EngagementAuthorityEnforcer();
    this.hitlEnforcer = new HumanInLoopEnforcer(this.config.hitlTimeoutSeconds);
    this.classificationEnforcer = new ClassificationEnforcer();
    this.auditLogger = new MilitaryAuditLogger();
    this.loadDefaultRules();
    this.loadDefaultHitlRequirements();
  }

  private loadDefaultRules(): void {
    this.policyRules = [
      {
        id: 'rule_001',
        name: 'PID Required for Lethal Engagement',
        conditions: {
          actionTypes: ['lethal_engagement'],
          requiresPID: true,
          requiresCommandAuthorization: true,
          minAuthorizationLevel: 'company_commander',
        },
        action: 'require_human_approval',
        priority: 1,
        classification: 'SECRET',
      },
      {
        id: 'rule_002',
        name: 'Collateral Damage Limit',
        conditions: {
          actionTypes: ['lethal_engagement', 'non_lethal_engagement'],
          maxCollateralDamage: 15,
        },
        action: 'require_human_approval',
        priority: 2,
        classification: 'UNCLASSIFIED',
      },
      {
        id: 'rule_003',
        name: 'Protected Target Prohibition',
        conditions: {
          prohibitedTargets: ['hospital', 'school', 'religious_site', 'cultural_heritage', 'civilian_infrastructure'],
        },
        action: 'deny',
        priority: 0,
        classification: 'UNCLASSIFIED',
      },
      {
        id: 'rule_004',
        name: 'Cyber Action Authorization',
        conditions: {
          actionTypes: ['cyber_action'],
          requiresCommandAuthorization: true,
          minAuthorizationLevel: 'battalion_commander',
        },
        action: 'require_human_approval',
        priority: 3,
        classification: 'TOP_SECRET',
      },
      {
        id: 'rule_005',
        name: 'SCI Data Boundary',
        conditions: {
          classificationBoundaries: ['SCI'],
        },
        action: 'require_human_approval',
        priority: 1,
        classification: 'SCI',
      },
    ];
  }

  private loadDefaultHitlRequirements(): void {
    const defaults: HumanInLoopRequirement[] = [
      {
        action: 'lethal_engagement',
        requirement: 'mandatory',
        timeout: 30,
        fallback: 'abort',
        escalationPath: ['company_commander', 'battalion_commander', 'brigade_commander'],
        maxWaitTime: 120,
      },
      {
        action: 'non_lethal_engagement',
        requirement: 'conditional',
        timeout: 15,
        fallback: 'hold_position',
        escalationPath: ['platoon_leader', 'company_commander'],
        maxWaitTime: 60,
      },
      {
        action: 'cyber_action',
        requirement: 'mandatory',
        timeout: 60,
        fallback: 'abort',
        escalationPath: ['battalion_commander', 'brigade_commander', 'division_commander'],
        maxWaitTime: 300,
      },
      {
        action: 'target_acquisition',
        requirement: 'conditional',
        timeout: 10,
        fallback: 'hold_position',
        escalationPath: ['squad_leader', 'platoon_leader'],
        maxWaitTime: 30,
      },
      {
        action: 'electronic_warfare',
        requirement: 'mandatory',
        timeout: 45,
        fallback: 'abort',
        escalationPath: ['battalion_commander', 'brigade_commander'],
        maxWaitTime: 180,
      },
    ];

    for (const req of defaults) {
      this.hitlRequirements.set(req.action, req);
    }
  }

  evaluateAction(action: RobotAction): FirewallDecision {
    const violations: string[] = [];
    const receipts: string[] = [];
    let engagementResult: EngagementResult = 'approved';
    let requiresHumanApproval = false;

    // 1. Classification enforcement
    if (this.config.classificationBoundaryEnforcement) {
      const classResult = this.classificationEnforcer.enforceClassification(action);
      if (!classResult.allowed) {
        violations.push(...classResult.violations);
        engagementResult = 'classification_violation';
        const receipt = this.classificationEnforcer.generateReceipt(action, classResult);
        receipts.push(receipt.receiptId);
        return this.buildDecision(false, 'classification_violation', action.classification, engagementResult, violations, receipts);
      }
      const classReceipt = this.classificationEnforcer.generateReceipt(action, classResult);
      receipts.push(classReceipt.receiptId);
    }

    // 2. Engagement authority enforcement
    if (this.config.engagementAuthorityRequired) {
      const eaResult = this.engagementEnforcer.enforceEngagementAuthority(action, this.getAuthoritiesForAction(action));
      if (!eaResult.allowed) {
        violations.push(...eaResult.violations);
        engagementResult = eaResult.violations.includes('proportionality_violation') ? 'proportionality_violation'
          : eaResult.violations.includes('distinction_violation') ? 'distinction_violation'
          : 'denied';
        const receipt = this.engagementEnforcer.generateReceipt(action, eaResult);
        receipts.push(receipt.receiptId);
        return this.buildDecision(false, eaResult.reason, action.classification, engagementResult, violations, receipts);
      }
      const eaReceipt = this.engagementEnforcer.generateReceipt(action, eaResult);
      receipts.push(eaReceipt.receiptId);
    }

    // 3. Policy rules evaluation
    const sortedRules = [...this.policyRules].sort((a, b) => a.priority - b.priority);
    for (const rule of sortedRules) {
      const matches = this.evaluateRule(rule, action);
      if (matches) {
        if (rule.action === 'deny') {
          violations.push(`policy_rule_denied:${rule.id}`);
          return this.buildDecision(false, `denied_by_rule:${rule.id}`, action.classification, 'denied', violations, receipts);
        }
        if (rule.action === 'require_human_approval') {
          requiresHumanApproval = true;
          engagementResult = 'pending_human_approval';
        }
        if (rule.action === 'escalate') {
          requiresHumanApproval = true;
          engagementResult = 'escalated';
        }
      }
    }

    // 4. Human-in-the-loop enforcement
    if (requiresHumanApproval || this.hitlEnforcer.requiresHITL(action)) {
      const hitlResult = this.hitlEnforcer.enforceHITL(action);
      if (!hitlResult.allowed) {
        violations.push(...hitlResult.violations);
        engagementResult = hitlResult.timeoutReached ? 'timeout_abort' : 'pending_human_approval';
        const receipt = this.hitlEnforcer.generateReceipt(action, hitlResult);
        receipts.push(receipt.receiptId);
        return this.buildDecision(false, hitlResult.reason, action.classification, engagementResult, violations, receipts);
      }
      const hitlReceipt = this.hitlEnforcer.generateReceipt(action, hitlResult);
      receipts.push(hitlReceipt.receiptId);
    }

    // 5. Authorization level check
    if (this.config.requirePIDForAllEngagements && ['lethal_engagement', 'non_lethal_engagement'].includes(action.type)) {
      if (!action.target.positiveIdentification) {
        violations.push('pid_not_verified');
        return this.buildDecision(false, 'pid_required', action.classification, 'denied', violations, receipts);
      }
    }

    // Log and return
    const decision = this.buildDecision(true, 'approved_by_firewall', action.classification, engagementResult, violations, receipts);
    this.auditLogger.logAction(action, decision);
    return decision;
  }

  enforceEngagementAuthority(action: RobotAction): FirewallDecision {
    const authorities = this.getAuthoritiesForAction(action);
    const result = this.engagementEnforcer.enforceEngagementAuthority(action, authorities);
    const receipt = this.engagementEnforcer.generateReceipt(action, result);
    const decision: FirewallDecision = {
      allowed: result.allowed,
      reason: result.reason,
      classification: action.classification,
      requiresHumanApproval: !result.allowed,
      engagementResult: result.allowed ? 'approved' : 'denied',
      violations: result.violations,
      receipts: [receipt.receiptId],
      timestamp: new Date().toISOString(),
    };
    this.auditLogger.logAction(action, decision);
    return decision;
  }

  enforceHumanInLoop(action: RobotAction): FirewallDecision {
    const result = this.hitlEnforcer.enforceHITL(action);
    const receipt = this.hitlEnforcer.generateReceipt(action, result);
    const decision: FirewallDecision = {
      allowed: result.allowed,
      reason: result.reason,
      classification: action.classification,
      requiresHumanApproval: !result.allowed,
      engagementResult: result.allowed ? 'approved' : result.timeoutReached ? 'timeout_abort' : 'pending_human_approval',
      violations: result.violations,
      receipts: [receipt.receiptId],
      timestamp: new Date().toISOString(),
    };
    this.auditLogger.logAction(action, decision);
    return decision;
  }

  enforceClassification(action: RobotAction): FirewallDecision {
    const result = this.classificationEnforcer.enforceClassification(action);
    const receipt = this.classificationEnforcer.generateReceipt(action, result);
    const decision: FirewallDecision = {
      allowed: result.allowed,
      reason: result.reason,
      classification: action.classification,
      requiresHumanApproval: false,
      engagementResult: result.allowed ? 'approved' : 'classification_violation',
      violations: result.violations,
      receipts: [receipt.receiptId],
      timestamp: new Date().toISOString(),
    };
    this.auditLogger.logAction(action, decision);
    return decision;
  }

  generateReceipt(action: RobotAction, decision: FirewallDecision): string {
    const receiptId = generateReceiptId('mrf_receipt');
    const receiptData = {
      receiptId,
      actionId: action.id,
      robotId: action.robotId,
      operatorId: action.operatorId,
      actionType: action.type,
      targetId: action.target.id,
      classification: action.classification,
      allowed: decision.allowed,
      reason: decision.reason,
      violations: decision.violations,
      timestamp: new Date().toISOString(),
    };
    const signedHash = sha256(receiptData);
    this.auditLogger.writeReceipt({ ...receiptData, signedHash });
    return receiptId;
  }

  logAction(action: RobotAction, decision: FirewallDecision): void {
    this.auditLogger.logAction(action, decision);
  }

  addPolicyRule(rule: PolicyRule): void {
    this.policyRules.push(rule);
  }

  removePolicyRule(ruleId: string): boolean {
    const idx = this.policyRules.findIndex((r) => r.id === ruleId);
    if (idx >= 0) {
      this.policyRules.splice(idx, 1);
      return true;
    }
    return false;
  }

  addEngagementAuthority(authority: EngagementAuthority): void {
    this.engagementAuthorities.set(authority.id, authority);
  }

  removeEngagementAuthority(authorityId: string): boolean {
    return this.engagementAuthorities.delete(authorityId);
  }

  setHitlRequirement(requirement: HumanInLoopRequirement): void {
    this.hitlRequirements.set(requirement.action, requirement);
  }

  getStats(): {
    policyRules: number;
    engagementAuthorities: number;
    hitlRequirements: number;
    pendingApprovals: number;
  } {
    return {
      policyRules: this.policyRules.length,
      engagementAuthorities: this.engagementAuthorities.size,
      hitlRequirements: this.hitlRequirements.size,
      pendingApprovals: this.pendingApprovals.size,
    };
  }

  exportAuditLog(): string {
    return this.auditLogger.exportForMilitaryAudit();
  }

  private getAuthoritiesForAction(action: RobotAction): EngagementAuthority[] {
    return [...this.engagementAuthorities.values()].filter((a) => {
      if (a.type === 'cease_fire') return false;
      if (new Date(a.expiresAt) < new Date()) return false;
      return true;
    });
  }

  private evaluateRule(rule: PolicyRule, action: RobotAction): boolean {
    if (rule.conditions.actionTypes && !rule.conditions.actionTypes.includes(action.type)) return false;
    if (rule.conditions.requiresPID && !action.target.positiveIdentification) return true;
    if (rule.conditions.maxCollateralDamage !== undefined && action.collateralDamageEstimate !== undefined) {
      if (action.collateralDamageEstimate > rule.conditions.maxCollateralDamage) return true;
    }
    if (rule.conditions.prohibitedTargets && rule.conditions.prohibitedTargets.includes(action.target.type)) return true;
    if (rule.conditions.minAuthorizationLevel) {
      if (!this.meetsAuthorizationLevel(action.authorization.authorizationLevel, rule.conditions.minAuthorizationLevel)) return true;
    }
    if (rule.conditions.classificationBoundaries) {
      if (rule.conditions.classificationBoundaries.includes(action.classification)) return true;
    }
    return false;
  }

  private meetsAuthorizationLevel(actual: string, required: string): boolean {
    const levels = ['none', 'squad_leader', 'platoon_leader', 'company_commander', 'battalion_commander', 'brigade_commander', 'division_commander', 'combatant_commander', 'secdef'];
    const actualIdx = levels.indexOf(actual);
    const requiredIdx = levels.indexOf(required);
    return actualIdx >= requiredIdx;
  }

  private buildDecision(
    allowed: boolean,
    reason: string,
    classification: ClassificationLevel,
    engagementResult: EngagementResult,
    violations: string[],
    receipts: string[],
  ): FirewallDecision {
    return {
      allowed,
      reason,
      classification,
      requiresHumanApproval: !allowed && engagementResult !== 'denied',
      engagementResult,
      violations,
      receipts,
      timestamp: new Date().toISOString(),
    };
  }
}
