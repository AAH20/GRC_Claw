import { describe, it, expect, beforeEach } from 'vitest';
import {
  MilitaryRobotFirewall,
  EngagementAuthorityEnforcer,
  HumanInLoopEnforcer,
  ClassificationEnforcer,
  MilitaryAuditLogger,
} from './index';
import type { EngagementCheckResult } from './engagement-authority';
import type { HITLCheckResult } from './human-in-loop';
import type {
  RobotAction,
  EngagementAuthority,
  PolicyRule,
  FirewallDecision,
} from './types';

function makeAction(overrides?: Partial<RobotAction>): RobotAction {
  return {
    id: 'action_001',
    type: 'lethal_engagement',
    target: {
      id: 'target_001',
      type: 'enemy_combatant',
      location: { lat: 34.5, lon: 69.2 },
      classification: 'SECRET',
      isCombatant: true,
      isProtected: false,
      positiveIdentification: true,
    },
    classification: 'SECRET',
    authorization: {
      commanderId: 'cmd_001',
      authorizationLevel: 'company_commander',
      authorizationCode: 'SECRET_AUTH_001',
      timestamp: new Date().toISOString(),
    },
    weaponSystem: 'armed_uav',
    collateralDamageEstimate: 5,
    rulesOfEngagement: 'weapons_free',
    timestamp: new Date().toISOString(),
    operatorId: 'operator_001',
    robotId: 'robot_001',
    ...overrides,
  };
}

function makeAuthority(overrides?: Partial<EngagementAuthority>): EngagementAuthority {
  return {
    id: 'ea_001',
    type: 'weapons_free',
    restrictions: {
      positiveIdentificationRequired: true,
      proportionalResponseRequired: true,
      distinctionRequired: true,
      commandAuthorizationRequired: true,
      maxCollateralDamage: 15,
      allowedWeaponSystems: ['armed_uav', 'armed_ground'],
      prohibitedTargets: ['hospital', 'school'],
    },
    authorizationLevel: 'company_commander',
    issuedBy: 'cmd_001',
    issuedAt: new Date(Date.now() - 3600000).toISOString(),
    expiresAt: new Date(Date.now() + 3600000).toISOString(),
    classification: 'SECRET',
    ...overrides,
  };
}

describe('MilitaryRobotFirewall', () => {
  let firewall: MilitaryRobotFirewall;

  beforeEach(() => {
    firewall = new MilitaryRobotFirewall();
  });

  describe('evaluateAction', () => {
    it('allows valid lethal engagement with PID', () => {
      const action = makeAction();
      const decision = firewall.evaluateAction(action);
      expect(decision.allowed).toBe(true);
      expect(decision.engagementResult).toBe('approved');
      expect(decision.violations).toHaveLength(0);
    });

    it('denies action without positive identification', () => {
      const action = makeAction({
        target: {
          ...makeAction().target,
          positiveIdentification: false,
        },
      });
      const decision = firewall.evaluateAction(action);
      expect(decision.allowed).toBe(false);
      expect(decision.violations).toContain('pid_not_verified');
    });

    it('denies action targeting protected entities', () => {
      const action = makeAction({
        target: {
          ...makeAction().target,
          type: 'hospital',
          isProtected: true,
          isCombatant: false,
        },
      });
      const decision = firewall.evaluateAction(action);
      expect(decision.allowed).toBe(false);
    });

    it('denies action exceeding collateral damage threshold', () => {
      const action = makeAction({ collateralDamageEstimate: 25 });
      const decision = firewall.evaluateAction(action);
      expect(decision.allowed).toBe(false);
    });
  });

  describe('enforceEngagementAuthority', () => {
    it('allows action with valid engagement authority', () => {
      const action = makeAction();
      const authority = makeAuthority();
      firewall.addEngagementAuthority(authority);
      const decision = firewall.enforceEngagementAuthority(action);
      expect(decision.allowed).toBe(true);
    });

    it('denies action without engagement authority', () => {
      const action = makeAction();
      const decision = firewall.enforceEngagementAuthority(action);
      expect(decision.allowed).toBe(false);
      expect(decision.violations).toContain('no_active_engagement_authority');
    });

    it('denies action with expired authority', () => {
      const action = makeAction();
      const authority = makeAuthority({
        expiresAt: new Date(Date.now() - 3600000).toISOString(),
      });
      firewall.addEngagementAuthority(authority);
      const decision = firewall.enforceEngagementAuthority(action);
      expect(decision.allowed).toBe(false);
    });
  });

  describe('enforceClassification', () => {
    it('allows action within classification boundary', () => {
      const action = makeAction({ classification: 'SECRET' });
      const decision = firewall.enforceClassification(action);
      expect(decision.allowed).toBe(true);
    });

    it('denies action exceeding classification boundary', () => {
      const action = makeAction({
        classification: 'TOP_SECRET',
        target: {
          ...makeAction().target,
          classification: 'SECRET',
        },
      });
      const decision = firewall.enforceClassification(action);
      expect(decision.allowed).toBe(false);
      expect(decision.violations).toContain('classification_boundary_exceeded');
    });
  });

  describe('audit logging', () => {
    it('logs action and generates receipt', () => {
      const action = makeAction();
      const decision = firewall.evaluateAction(action);
      const receiptId = firewall.generateReceipt(action, decision);
      expect(receiptId).toMatch(/^mrf_receipt:/);
    });

    it('exports audit log', () => {
      const action = makeAction();
      firewall.evaluateAction(action);
      const exportLog = firewall.exportAuditLog();
      const parsed = JSON.parse(exportLog);
      expect(parsed.totalEntries).toBeGreaterThan(0);
      expect(parsed.chainIntegrity).toBe(true);
    });
  });

  describe('policy rules', () => {
    it('adds and removes policy rules', () => {
      const rule: PolicyRule = {
        id: 'custom_rule_001',
        name: 'Custom Rule',
        conditions: { actionTypes: ['surveillance'] },
        action: 'allow',
        priority: 10,
        classification: 'UNCLASSIFIED',
      };
      firewall.addPolicyRule(rule);
      const stats = firewall.getStats();
      expect(stats.policyRules).toBeGreaterThan(5); // defaults + 1

      firewall.removePolicyRule('custom_rule_001');
      const statsAfter = firewall.getStats();
      expect(statsAfter.policyRules).toBe(5); // back to defaults
    });
  });

  describe('stats', () => {
    it('returns correct stats', () => {
      const stats = firewall.getStats();
      expect(stats.policyRules).toBeGreaterThan(0);
      expect(stats.hitlRequirements).toBeGreaterThan(0);
    });
  });
});

describe('EngagementAuthorityEnforcer', () => {
  let enforcer: EngagementAuthorityEnforcer;

  beforeEach(() => {
    enforcer = new EngagementAuthorityEnforcer();
  });

  it('generates receipt with signed hash', () => {
    const action = makeAction();
    const result: EngagementCheckResult = {
      allowed: true,
      reason: 'engagement_authorized',
      violations: [],
      pidVerified: true,
      proportionalResponse: true,
      distinctionMaintained: true,
      commandAuthorized: true,
      authorityId: 'ea_001',
    };
    const receipt = enforcer.generateReceipt(action, result);
    expect(receipt.receiptId).toMatch(/^ea_receipt:/);
    expect(receipt.signedHash).toHaveLength(64);
    expect(receipt.pidVerified).toBe(true);
  });
});

describe('HumanInLoopEnforcer', () => {
  let enforcer: HumanInLoopEnforcer;

  beforeEach(() => {
    enforcer = new HumanInLoopEnforcer(30);
  });

  it('identifies lethal engagement as requiring HITL', () => {
    const action = makeAction({ type: 'lethal_engagement' });
    expect(enforcer.requiresHITL(action)).toBe(true);
  });

  it('identifies logistics as not requiring HITL', () => {
    const action = makeAction({ type: 'logistics' });
    expect(enforcer.requiresHITL(action)).toBe(false);
  });

  it('enforces HITL and returns pending for mandatory actions', () => {
    const action = makeAction({ type: 'lethal_engagement' });
    const result = enforcer.enforceHITL(action);
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe('hitl_pending_approval');
  });

  it('generates receipt with signed hash', () => {
    const action = makeAction();
    const result: HITLCheckResult = {
      allowed: true,
      reason: 'hitl_approved',
      violations: [],
      timeoutReached: false,
      fallbackAction: 'abort',
      humanApprover: 'approver_001',
    };
    const receipt = enforcer.generateReceipt(action, result);
    expect(receipt.receiptId).toMatch(/^hitl_receipt:/);
    expect(receipt.signedHash).toHaveLength(64);
  });
});

describe('ClassificationEnforcer', () => {
  let enforcer: ClassificationEnforcer;

  beforeEach(() => {
    enforcer = new ClassificationEnforcer();
  });

  it('allows action within classification boundary', () => {
    const action = makeAction({ classification: 'SECRET' });
    const result = enforcer.enforceClassification(action);
    expect(result.allowed).toBe(true);
  });

  it('denies action exceeding classification boundary', () => {
    const action = makeAction({
      classification: 'TOP_SECRET',
      target: { ...makeAction().target, classification: 'SECRET' },
    });
    const result = enforcer.enforceClassification(action);
    expect(result.allowed).toBe(false);
    expect(result.violations).toContain('classification_boundary_exceeded');
  });

  it('generates receipt with signed hash', () => {
    const action = makeAction();
    const result = enforcer.enforceClassification(action);
    const receipt = enforcer.generateReceipt(action, result);
    expect(receipt.receiptId).toMatch(/^cls_receipt:/);
    expect(receipt.signedHash).toHaveLength(64);
  });

  it('returns correct handling requirements', () => {
    expect(enforcer.getHandlingRequirements('UNCLASSIFIED')).toHaveLength(0);
    expect(enforcer.getHandlingRequirements('SECRET')).toContain('no_foreign_disclosure');
    expect(enforcer.getHandlingRequirements('SCI')).toContain('no_abbreviations');
  });
});

describe('MilitaryAuditLogger', () => {
  let logger: MilitaryAuditLogger;

  beforeEach(() => {
    logger = new MilitaryAuditLogger();
  });

  it('logs action and verifies chain integrity', () => {
    const action = makeAction();
    const decision: FirewallDecision = {
      allowed: true,
      reason: 'approved',
      classification: 'SECRET',
      requiresHumanApproval: false,
      engagementResult: 'approved',
      violations: [],
      receipts: [],
      timestamp: new Date().toISOString(),
    };
    logger.logAction(action, decision);
    logger.logAction(action, decision);
    expect(logger.verifyChainIntegrity()).toBe(true);
  });

  it('exports audit log for military audit', () => {
    const action = makeAction();
    const decision: FirewallDecision = {
      allowed: true,
      reason: 'approved',
      classification: 'SECRET',
      requiresHumanApproval: false,
      engagementResult: 'approved',
      violations: [],
      receipts: [],
      timestamp: new Date().toISOString(),
    };
    logger.logAction(action, decision);
    const exportData = JSON.parse(logger.exportForMilitaryAudit());
    expect(exportData.totalEntries).toBe(1);
    expect(exportData.chainIntegrity).toBe(true);
  });

  it('generates signed receipt', () => {
    const action = makeAction();
    const decision: FirewallDecision = {
      allowed: true,
      reason: 'approved',
      classification: 'SECRET',
      requiresHumanApproval: false,
      engagementResult: 'approved',
      violations: [],
      receipts: [],
      timestamp: new Date().toISOString(),
    };
    const receipt = logger.generateSignedReceipt(action, decision);
    expect(receipt.receiptId).toMatch(/^receipt:/);
    expect(receipt.signedHash).toHaveLength(64);
  });
});
