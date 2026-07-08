import { createHash, randomBytes } from 'node:crypto';
import type { RobotAction, EngagementAuthority } from './types';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export interface EngagementCheckResult {
  allowed: boolean;
  reason: string;
  violations: string[];
  pidVerified: boolean;
  proportionalResponse: boolean;
  distinctionMaintained: boolean;
  commandAuthorized: boolean;
  authorityId: string;
}

export class EngagementAuthorityEnforcer {
  enforceEngagementAuthority(action: RobotAction, authorities: EngagementAuthority[]): EngagementCheckResult {
    const violations: string[] = [];
    let pidVerified = false;
    let proportionalResponse = true;
    let distinctionMaintained = true;
    let commandAuthorized = false;
    let authorityId = '';

    // 1. Check for active engagement authority
    const activeAuthority = this.findActiveAuthority(action, authorities);
    if (!activeAuthority) {
      violations.push('no_active_engagement_authority');
      return {
        allowed: false,
        reason: 'no_active_engagement_authority',
        violations,
        pidVerified: false,
        proportionalResponse: false,
        distinctionMaintained: false,
        commandAuthorized: false,
        authorityId: '',
      };
    }
    authorityId = activeAuthority.id;

    // 2. Check positive identification (PID)
    pidVerified = this.checkPositiveIdentification(action, activeAuthority);
    if (!pidVerified) {
      violations.push('pid_not_verified');
    }

    // 3. Verify proportional response
    proportionalResponse = this.verifyProportionalResponse(action, activeAuthority);
    if (!proportionalResponse) {
      violations.push('proportionality_violation');
    }

    // 4. Check distinction between combatants/civilians
    distinctionMaintained = this.checkDistinction(action, activeAuthority);
    if (!distinctionMaintained) {
      violations.push('distinction_violation');
    }

    // 5. Verify command authorization
    commandAuthorized = this.verifyCommandAuthorization(action, activeAuthority);
    if (!commandAuthorized) {
      violations.push('command_authorization_failed');
    }

    // 6. Check prohibited targets
    if (this.isProhibitedTarget(action, activeAuthority)) {
      violations.push('prohibited_target');
    }

    // 7. Check time window restrictions
    if (!this.isWithinTimeWindow(activeAuthority)) {
      violations.push('outside_time_window');
    }

    const allowed = violations.length === 0;

    return {
      allowed,
      reason: allowed ? 'engagement_authorized' : violations.join(';'),
      violations,
      pidVerified,
      proportionalResponse,
      distinctionMaintained,
      commandAuthorized,
      authorityId,
    };
  }

  generateReceipt(action: RobotAction, result: EngagementCheckResult): {
    receiptId: string;
    actionId: string;
    pidVerified: boolean;
    proportionalResponse: boolean;
    distinctionMaintained: boolean;
    commandAuthorized: boolean;
    engagementAuthorityId: string;
    timestamp: string;
    signedHash: string;
  } {
    const receiptId = `ea_receipt:${randomBytes(16).toString('hex').slice(0, 16)}`;
    const timestamp = new Date().toISOString();
    const receiptData = {
      receiptId,
      actionId: action.id,
      pidVerified: result.pidVerified,
      proportionalResponse: result.proportionalResponse,
      distinctionMaintained: result.distinctionMaintained,
      commandAuthorized: result.commandAuthorized,
      engagementAuthorityId: result.authorityId,
      timestamp,
    };
    const signedHash = sha256(receiptData);

    return { ...receiptData, signedHash };
  }

  private findActiveAuthority(action: RobotAction, authorities: EngagementAuthority[]): EngagementAuthority | null {
    const now = new Date();
    for (const auth of authorities) {
      if (new Date(auth.issuedAt) > now) continue;
      if (new Date(auth.expiresAt) < now) continue;
      if (auth.type === 'cease_fire') continue;
      if (auth.type === 'weapons_free' || auth.type === 'weapons_control' || auth.type === 'target' || auth.type === 'area') {
        return auth;
      }
    }
    return null;
  }

  private checkPositiveIdentification(action: RobotAction, authority: EngagementAuthority): boolean {
    if (!authority.restrictions.positiveIdentificationRequired) return true;
    return action.target.positiveIdentification;
  }

  private verifyProportionalResponse(action: RobotAction, authority: EngagementAuthority): boolean {
    if (!authority.restrictions.proportionalResponseRequired) return true;
    if (action.type === 'surveillance' || action.type === 'reconnaissance' || action.type === 'logistics' || action.type === 'communication') {
      return true;
    }
    if (action.collateralDamageEstimate === undefined) return false;
    return action.collateralDamageEstimate <= authority.restrictions.maxCollateralDamage;
  }

  private checkDistinction(action: RobotAction, authority: EngagementAuthority): boolean {
    if (!authority.restrictions.distinctionRequired) return true;
    if (action.target.isCombatant) return true;
    if (action.target.isProtected) return false;
    if (!action.target.positiveIdentification) return false;
    return true;
  }

  private verifyCommandAuthorization(action: RobotAction, authority: EngagementAuthority): boolean {
    if (!authority.restrictions.commandAuthorizationRequired) return true;
    return action.authorization.commanderId !== '' && action.authorization.authorizationCode !== '';
  }

  private isProhibitedTarget(action: RobotAction, authority: EngagementAuthority): boolean {
    return authority.restrictions.prohibitedTargets.includes(action.target.type);
  }

  private isWithinTimeWindow(authority: EngagementAuthority): boolean {
    if (!authority.restrictions.timeWindow) return true;
    const now = new Date();
    const start = new Date(authority.restrictions.timeWindow.start);
    const end = new Date(authority.restrictions.timeWindow.end);
    return now >= start && now <= end;
  }
}
