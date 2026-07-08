import { createHash, randomBytes } from 'node:crypto';
import type { RobotAction, FirewallDecision, ClassificationLevel } from './types';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export interface AuditLogEntry {
  entryId: string;
  actionId: string;
  robotId: string;
  operatorId: string;
  actionType: string;
  targetId: string;
  targetClassification: string;
  classification: string;
  allowed: boolean;
  reason: string;
  engagementResult: string;
  violations: string[];
  receipts: string[];
  timestamp: string;
  signedHash: string;
  previousHash: string;
}

export interface SignedReceipt {
  receiptId: string;
  actionId: string;
  robotId?: string;
  operatorId?: string;
  actionType?: string;
  targetId?: string;
  classification?: ClassificationLevel;
  allowed?: boolean;
  reason?: string;
  violations?: string[];
  signedHash: string;
  timestamp: string;
}

export class MilitaryAuditLogger {
  private logEntries: AuditLogEntry[] = [];
  private receipts: SignedReceipt[] = [];
  private lastHash: string = '0000000000000000000000000000000000000000000000000000000000000000';

  logAction(action: RobotAction, decision: FirewallDecision): AuditLogEntry {
    const entryId = `audit:${randomBytes(16).toString('hex').slice(0, 16)}`;
    const timestamp = new Date().toISOString();

    const entry: AuditLogEntry = {
      entryId,
      actionId: action.id,
      robotId: action.robotId,
      operatorId: action.operatorId,
      actionType: action.type,
      targetId: action.target.id,
      targetClassification: action.target.classification,
      classification: action.classification,
      allowed: decision.allowed,
      reason: decision.reason,
      engagementResult: decision.engagementResult,
      violations: decision.violations,
      receipts: decision.receipts,
      timestamp,
      signedHash: '',
      previousHash: this.lastHash,
    };

    entry.signedHash = this.hashEntry(entry);
    this.lastHash = entry.signedHash;
    this.logEntries.push(entry);

    return entry;
  }

  writeReceipt(receipt: SignedReceipt): void {
    this.receipts.push(receipt);
  }

  generateSignedReceipt(action: RobotAction, decision: FirewallDecision): SignedReceipt {
    const receiptId = `receipt:${randomBytes(16).toString('hex').slice(0, 16)}`;
    const timestamp = new Date().toISOString();
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
      timestamp,
    };
    const signedHash = sha256(receiptData);

    const receipt: SignedReceipt = { ...receiptData, signedHash };
    this.writeReceipt(receipt);
    return receipt;
  }

  exportForMilitaryAudit(): string {
    const exportData = {
      exportTimestamp: new Date().toISOString(),
      exportId: `export:${randomBytes(16).toString('hex').slice(0, 16)}`,
      totalEntries: this.logEntries.length,
      totalReceipts: this.receipts.length,
      chainIntegrity: this.verifyChainIntegrity(),
      entries: this.logEntries,
      receipts: this.receipts,
    };

    return JSON.stringify(exportData, null, 2);
  }

  verifyChainIntegrity(): boolean {
    for (let i = 1; i < this.logEntries.length; i++) {
      const current = this.logEntries[i];
      const previous = this.logEntries[i - 1];
      if (current.previousHash !== previous.signedHash) {
        return false;
      }
      const { signedHash: _, ...entryWithoutHash } = current;
      const computedHash = this.hashEntry(entryWithoutHash);
      if (computedHash !== current.signedHash) {
        return false;
      }
    }
    return true;
  }

  getLogEntries(): AuditLogEntry[] {
    return [...this.logEntries];
  }

  getReceipts(): SignedReceipt[] {
    return [...this.receipts];
  }

  getEntriesByActionType(actionType: string): AuditLogEntry[] {
    return this.logEntries.filter((e) => e.actionType === actionType);
  }

  getEntriesByRobot(robotId: string): AuditLogEntry[] {
    return this.logEntries.filter((e) => e.robotId === robotId);
  }

  getViolations(): AuditLogEntry[] {
    return this.logEntries.filter((e) => e.violations.length > 0);
  }

  getDeniedActions(): AuditLogEntry[] {
    return this.logEntries.filter((e) => !e.allowed);
  }

  private hashEntry(entry: Omit<AuditLogEntry, 'signedHash'>): string {
    return sha256({
      entryId: entry.entryId,
      actionId: entry.actionId,
      robotId: entry.robotId,
      operatorId: entry.operatorId,
      actionType: entry.actionType,
      allowed: entry.allowed,
      reason: entry.reason,
      timestamp: entry.timestamp,
      previousHash: entry.previousHash,
    });
  }
}
