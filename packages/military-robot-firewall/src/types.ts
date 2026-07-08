export type RobotActionType =
  | 'lethal_engagement'
  | 'non_lethal_engagement'
  | 'surveillance'
  | 'reconnaissance'
  | 'logistics'
  | 'communication'
  | 'cyber_action'
  | 'electronic_warfare'
  | 'target_acquisition'
  | 'force_protection';

export type ClassificationLevel = 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET' | 'SCI';

export type AuthorizationLevel = 'none' | 'squad_leader' | 'platoon_leader' | 'company_commander' | 'battalion_commander' | 'brigade_commander' | 'division_commander' | 'combatant_commander' | 'secdef';

export type EngagementResult = 'approved' | 'denied' | 'pending_human_approval' | 'escalated' | 'timeout_abort' | 'classification_violation' | 'proportionality_violation' | 'distinction_violation';

export type FallbackAction = 'abort' | 'hold_position' | 'escalate' | 'return_to_base' | 'cease_fire';

export type DataHandlingRequirement = 'no_abbreviations' | 'no_foreign_disclosure' | 'no_transfer_outside_scip' | 'originator_control' | 'dissemination_control';

export interface RobotAction {
  id: string;
  type: RobotActionType;
  target: {
    id: string;
    type: string;
    location?: { lat: number; lon: number; alt?: number };
    classification: ClassificationLevel;
    isCombatant: boolean;
    isProtected: boolean;
    positiveIdentification: boolean;
  };
  classification: ClassificationLevel;
  authorization: {
    commanderId: string;
    authorizationLevel: AuthorizationLevel;
    authorizationCode: string;
    timestamp: string;
  };
  weaponSystem?: string;
  collateralDamageEstimate?: number;
  rulesOfEngagement?: string;
  timestamp: string;
  operatorId: string;
  robotId: string;
}

export interface FirewallDecision {
  allowed: boolean;
  reason: string;
  classification: ClassificationLevel;
  requiresHumanApproval: boolean;
  engagementResult: EngagementResult;
  violations: string[];
  receipts: string[];
  timestamp: string;
}

export interface PolicyRule {
  id: string;
  name: string;
  conditions: {
    actionTypes?: RobotActionType[];
    classificationBoundaries?: ClassificationLevel[];
    requiresPID?: boolean;
    maxCollateralDamage?: number;
    requiresCommandAuthorization?: boolean;
    minAuthorizationLevel?: AuthorizationLevel;
    prohibitedTargets?: string[];
    timeRestrictions?: { start: string; end: string };
    geographicRestrictions?: { zones: Array<{ lat: number; lon: number; radius: number }> };
  };
  action: 'allow' | 'deny' | 'require_human_approval' | 'escalate';
  priority: number;
  classification: ClassificationLevel;
}

export interface EngagementAuthority {
  id: string;
  type: 'area' | 'target' | 'weapons_free' | 'weapons_control' | 'cease_fire';
  restrictions: {
    positiveIdentificationRequired: boolean;
    proportionalResponseRequired: boolean;
    distinctionRequired: boolean;
    commandAuthorizationRequired: boolean;
    maxCollateralDamage: number;
    allowedWeaponSystems: string[];
    prohibitedTargets: string[];
    timeWindow?: { start: string; end: string };
  };
  authorizationLevel: AuthorizationLevel;
  issuedBy: string;
  issuedAt: string;
  expiresAt: string;
  classification: ClassificationLevel;
}

export interface HumanInLoopRequirement {
  action: RobotActionType;
  requirement: 'mandatory' | 'conditional' | 'optional';
  timeout: number;
  fallback: FallbackAction;
  escalationPath: AuthorizationLevel[];
  maxWaitTime: number;
}

export interface ClassificationReceipt {
  receiptId: string;
  actionId: string;
  classification: ClassificationLevel;
  handlingRequirements: DataHandlingRequirement[];
  needToKnowVerified: boolean;
  crossDomainSolution?: string;
  timestamp: string;
  signedHash: string;
}

export interface EngagementReceipt {
  receiptId: string;
  actionId: string;
  pidVerified: boolean;
  proportionalResponse: boolean;
  distinctionMaintained: boolean;
  commandAuthorized: boolean;
  engagementAuthorityId: string;
  timestamp: string;
  signedHash: string;
}

export interface HITLReceipt {
  receiptId: string;
  actionId: string;
  humanApprover?: string;
  approvalTimestamp?: string;
  timeoutReached: boolean;
  fallbackAction: FallbackAction;
  escalatedTo?: string;
  timestamp: string;
  signedHash: string;
}

export interface MilitaryFirewallConfig {
  defaultClassification: ClassificationLevel;
  maxCollateralDamageThreshold: number;
  hitlTimeoutSeconds: number;
  requirePIDForAllEngagements: boolean;
  enforceDistinction: boolean;
  enforceProportionality: boolean;
  classificationBoundaryEnforcement: boolean;
  engagementAuthorityRequired: boolean;
  auditRetentionDays: number;
}
