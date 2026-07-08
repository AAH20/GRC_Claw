import { createHash, randomBytes } from 'node:crypto';
import type { RobotAction, HumanInLoopRequirement, FallbackAction } from './types';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export interface HITLCheckResult {
  allowed: boolean;
  reason: string;
  violations: string[];
  timeoutReached: boolean;
  fallbackAction: FallbackAction;
  humanApprover?: string;
  escalatedTo?: string;
}

const DEFAULT_HITL_REQUIREMENTS: HumanInLoopRequirement[] = [
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

export class HumanInLoopEnforcer {
  private requirements: Map<string, HumanInLoopRequirement>;
  private defaultTimeout: number;
  private pendingApprovals: Map<string, { action: RobotAction; timestamp: number }> = new Map();
  private approvalCallbacks: Map<string, (approved: boolean, approverId?: string) => void> = new Map();

  constructor(defaultTimeout: number = 30) {
    this.defaultTimeout = defaultTimeout;
    this.requirements = new Map();
    for (const req of DEFAULT_HITL_REQUIREMENTS) {
      this.requirements.set(req.action, req);
    }
  }

  requiresHITL(action: RobotAction): boolean {
    const req = this.requirements.get(action.type);
    if (!req) return false;
    if (req.requirement === 'mandatory') return true;
    if (req.requirement === 'conditional') {
      return ['lethal_engagement', 'non_lethal_engagement', 'cyber_action'].includes(action.type);
    }
    return false;
  }

  enforceHITL(action: RobotAction): HITLCheckResult {
    const violations: string[] = [];
    const req = this.requirements.get(action.type);

    if (!req || req.requirement === 'optional') {
      return {
        allowed: true,
        reason: 'hitl_not_required',
        violations: [],
        timeoutReached: false,
        fallbackAction: 'abort',
      };
    }

    // Check if action type strictly requires HITL
    if (req.requirement === 'mandatory') {
      if (!this.hasPendingApproval(action.id)) {
        this.queueForApproval(action);
      }

      const approvalStatus = this.checkApprovalStatus(action.id);

      if (approvalStatus.approved) {
        return {
          allowed: true,
          reason: 'hitl_approved',
          violations: [],
          timeoutReached: false,
          fallbackAction: req.fallback,
          humanApprover: approvalStatus.approverId,
        };
      }

      if (approvalStatus.timeoutReached) {
        violations.push('hitl_timeout_reached');
        return {
          allowed: false,
          reason: `hitl_timeout_fallback_${req.fallback}`,
          violations,
          timeoutReached: true,
          fallbackAction: req.fallback,
          escalatedTo: this.getNextEscalationLevel(action, req),
        };
      }

      violations.push('hitl_pending');
      return {
        allowed: false,
        reason: 'hitl_pending_approval',
        violations,
        timeoutReached: false,
        fallbackAction: req.fallback,
      };
    }

    // Conditional HITL - check collateral damage estimate
    if (req.requirement === 'conditional') {
      if (action.collateralDamageEstimate !== undefined && action.collateralDamageEstimate > 10) {
        if (!this.hasPendingApproval(action.id)) {
          this.queueForApproval(action);
        }

        const approvalStatus = this.checkApprovalStatus(action.id);

        if (approvalStatus.approved) {
          return {
            allowed: true,
            reason: 'conditional_hitl_approved',
            violations: [],
            timeoutReached: false,
            fallbackAction: req.fallback,
            humanApprover: approvalStatus.approverId,
          };
        }

        if (approvalStatus.timeoutReached) {
          violations.push('conditional_hitl_timeout');
          return {
            allowed: false,
            reason: `conditional_hitl_timeout_fallback_${req.fallback}`,
            violations,
            timeoutReached: true,
            fallbackAction: req.fallback,
            escalatedTo: this.getNextEscalationLevel(action, req),
          };
        }
      }
    }

    return {
      allowed: true,
      reason: 'hitl_cleared',
      violations: [],
      timeoutReached: false,
      fallbackAction: req.fallback,
    };
  }

  generateReceipt(action: RobotAction, result: HITLCheckResult): {
    receiptId: string;
    actionId: string;
    humanApprover?: string;
    approvalTimestamp?: string;
    timeoutReached: boolean;
    fallbackAction: FallbackAction;
    escalatedTo?: string;
    timestamp: string;
    signedHash: string;
  } {
    const receiptId = `hitl_receipt:${randomBytes(16).toString('hex').slice(0, 16)}`;
    const timestamp = new Date().toISOString();
    const receiptData = {
      receiptId,
      actionId: action.id,
      humanApprover: result.humanApprover,
      approvalTimestamp: result.humanApprover ? timestamp : undefined,
      timeoutReached: result.timeoutReached,
      fallbackAction: result.fallbackAction,
      escalatedTo: result.escalatedTo,
      timestamp,
    };
    const signedHash = sha256(receiptData);

    return { ...receiptData, signedHash };
  }

  setRequirement(requirement: HumanInLoopRequirement): void {
    this.requirements.set(requirement.action, requirement);
  }

  getRequirement(actionType: string): HumanInLoopRequirement | undefined {
    return this.requirements.get(actionType);
  }

  approveAction(actionId: string, approverId: string): boolean {
    const pending = this.pendingApprovals.get(actionId);
    if (!pending) return false;
    this.approvalCallbacks.get(actionId)?.(true, approverId);
    this.pendingApprovals.delete(actionId);
    return true;
  }

  denyAction(actionId: string, approverId: string): boolean {
    const pending = this.pendingApprovals.get(actionId);
    if (!pending) return false;
    this.approvalCallbacks.get(actionId)?.(false, approverId);
    this.pendingApprovals.delete(actionId);
    return true;
  }

  private queueForApproval(action: RobotAction): void {
    this.pendingApprovals.set(action.id, {
      action,
      timestamp: Date.now(),
    });
  }

  private hasPendingApproval(actionId: string): boolean {
    return this.pendingApprovals.has(actionId);
  }

  private checkApprovalStatus(actionId: string): { approved: boolean; timeoutReached: boolean; approverId?: string } {
    const pending = this.pendingApprovals.get(actionId);
    if (!pending) return { approved: false, timeoutReached: true };

    const req = this.requirements.get(pending.action.type);
    const timeout = req?.timeout ?? this.defaultTimeout;
    const elapsed = (Date.now() - pending.timestamp) / 1000;

    if (elapsed > timeout) {
      return { approved: false, timeoutReached: true };
    }

    return { approved: false, timeoutReached: false };
  }

  private getNextEscalationLevel(action: RobotAction, req: HumanInLoopRequirement): string | undefined {
    const currentLevel = action.authorization.authorizationLevel;
    const currentIdx = req.escalationPath.indexOf(currentLevel);
    if (currentIdx >= 0 && currentIdx < req.escalationPath.length - 1) {
      return req.escalationPath[currentIdx + 1];
    }
    return req.escalationPath[req.escalationPath.length - 1];
  }
}
