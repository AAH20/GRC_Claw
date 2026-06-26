import type { randomUUID } from "node:crypto";

export type EvidenceCategory =
  | "mfa"
  | "encryption"
  | "access_control"
  | "logging"
  | "patch_management"
  | "network_security"
  | "backup";

export type ComplianceFramework = "SOC2" | "ISO27001" | "NIST_CSF";

export type CollectorStatus = "idle" | "collecting" | "completed" | "error";

export interface EvidenceItem {
  id: string;
  category: EvidenceCategory;
  controlId: string;
  framework: ComplianceFramework;
  source: string;
  timestamp: string;
  hash: string;
  data: Record<string, unknown>;
  status: "compliant" | "non_compliant" | "partial" | "unknown";
}

export interface SystemAdapter {
  /** Query MFA enforcement status */
  queryMFA(): Promise<MFAEvidence>;
  /** Query encryption at rest status */
  queryEncryptionAtRest(): Promise<EncryptionEvidence>;
  /** Query encryption in transit status */
  queryEncryptionInTransit(): Promise<EncryptionEvidence>;
  /** Query access control policies */
  queryAccessControl(): Promise<AccessControlEvidence>;
  /** Query logging configuration */
  queryLogging(): Promise<LoggingEvidence>;
  /** Query patch management status */
  queryPatchManagement(): Promise<PatchEvidence>;
  /** Query network security rules */
  queryNetworkSecurity(): Promise<NetworkSecurityEvidence>;
  /** Query backup configuration */
  queryBackup(): Promise<BackupEvidence>;
}

export interface MFAEvidence {
  enforced: boolean;
  totalUsers: number;
  mfaEnabledUsers: number;
  methods: string[];
  lastEnforcedAt?: string;
}

export interface EncryptionEvidence {
  enabled: boolean;
  algorithm?: string;
  keyRotationDays?: number;
  lastRotatedAt?: string;
  details: Record<string, unknown>;
}

export interface AccessControlEvidence {
  leastPrivilege: boolean;
  totalRoles: number;
  excessiveRoles: number;
  lastAuditAt?: string;
  details: Record<string, unknown>;
}

export interface LoggingEvidence {
  enabled: boolean;
  logTypes: string[];
  retentionDays: number;
  alertingEnabled: boolean;
  lastConfiguredAt?: string;
}

export interface PatchEvidence {
  lastPatchDate: string;
  pendingPatches: number;
  criticalPatches: number;
  autoUpdateEnabled: boolean;
  details: Record<string, unknown>;
}

export interface NetworkSecurityEvidence {
  firewallEnabled: boolean;
  segmentationEnabled: boolean;
  totalRules: number;
  openPorts: number;
  lastAuditAt?: string;
}

export interface BackupEvidence {
  configured: boolean;
  frequency: string;
  lastBackupAt?: string;
  retentionDays: number;
  testedAt?: string;
  testPassed: boolean;
}
