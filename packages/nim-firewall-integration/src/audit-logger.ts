import { createHash, createHmac, randomBytes } from 'node:crypto';
import type { AuditEntry, FirewallDecision, NimRequest, NimResponse, TrustReceipt } from './types.js';

export interface AuditLoggerConfig {
  secretKey: string;
  chainEnabled?: boolean;
  maxEntries?: number;
  onEntry?: (entry: AuditEntry) => void;
}

export class AuditLogger {
  private entries: AuditEntry[] = [];
  private chain: TrustReceipt[] = [];
  private secretKey: string;
  private chainEnabled: boolean;
  private maxEntries: number;
  private onEntry?: (entry: AuditEntry) => void;
  private lastReceiptHash = '0000000000000000000000000000000000000000000000000000000000000000';

  constructor(config: AuditLoggerConfig) {
    this.secretKey = config.secretKey;
    this.chainEnabled = config.chainEnabled ?? true;
    this.maxEntries = config.maxEntries ?? 10000;
    this.onEntry = config.onEntry;
  }

  log(
    request: NimRequest,
    decision: FirewallDecision,
    response?: NimResponse
  ): AuditEntry {
    const entry: AuditEntry = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      requestId: request.requestId ?? decision.requestId,
      request,
      response,
      decision,
    };

    this.entries.push(entry);
    this.trimEntries();

    if (this.chainEnabled) {
      const receipt = this.generateReceipt(request, decision);
      this.chain.push(receipt);
      this.lastReceiptHash = receipt.hash;
    }

    this.onEntry?.(entry);
    return entry;
  }

  generateReceipt(request: NimRequest, decision: FirewallDecision): TrustReceipt {
    const requestHash = this.hashObject(request);
    const payload = {
      requestHash,
      decision,
      previousHash: this.lastReceiptHash,
      timestamp: new Date().toISOString(),
      requestId: request.requestId ?? decision.requestId,
    };

    const hash = this.hashObject(payload);
    const signature = this.sign(hash);

    return {
      hash,
      previousHash: this.lastReceiptHash,
      timestamp: payload.timestamp,
      requestId: payload.requestId,
      requestHash,
      decision,
      signature,
    };
  }

  verifyReceipt(receipt: TrustReceipt): boolean {
    const expectedHash = this.hashObject({
      requestHash: receipt.requestHash,
      decision: receipt.decision,
      previousHash: receipt.previousHash,
      timestamp: receipt.timestamp,
      requestId: receipt.requestId,
    });

    if (receipt.hash !== expectedHash) return false;

    const expectedSignature = this.sign(expectedHash);
    return receipt.signature === expectedSignature;
  }

  verifyChain(): { valid: boolean; brokenAt?: number } {
    for (let i = 0; i < this.chain.length; i++) {
      const receipt = this.chain[i];
      if (!this.verifyReceipt(receipt)) {
        return { valid: false, brokenAt: i };
      }

      if (i > 0) {
        const prev = this.chain[i - 1];
        if (receipt.previousHash !== prev.hash) {
          return { valid: false, brokenAt: i };
        }
      }
    }
    return { valid: true };
  }

  getEntries(filters?: {
    requestId?: string;
    allowed?: boolean;
    since?: string;
    until?: string;
  }): AuditEntry[] {
    let result = this.entries;

    if (filters?.requestId) {
      result = result.filter((e) => e.requestId === filters.requestId);
    }
    if (filters?.allowed !== undefined) {
      result = result.filter((e) => e.decision.allowed === filters.allowed);
    }
    if (filters?.since) {
      const since = new Date(filters.since);
      result = result.filter((e) => new Date(e.timestamp) >= since);
    }
    if (filters?.until) {
      const until = new Date(filters.until);
      result = result.filter((e) => new Date(e.timestamp) <= until);
    }

    return result;
  }

  getChain(): TrustReceipt[] {
    return [...this.chain];
  }

  exportForAudit(): {
    entries: AuditEntry[];
    chain: TrustReceipt[];
    chainValid: boolean;
    exportedAt: string;
    totalEntries: number;
    totalReceipts: number;
  } {
    return {
      entries: this.entries,
      chain: this.chain,
      chainValid: this.verifyChain().valid,
      exportedAt: new Date().toISOString(),
      totalEntries: this.entries.length,
      totalReceipts: this.chain.length,
    };
  }

  getStats(): {
    totalRequests: number;
    allowed: number;
    blocked: number;
    sandboxed: number;
    approvalRequired: number;
    avgRiskScore: number;
  } {
    const total = this.entries.length;
    if (total === 0) {
      return { totalRequests: 0, allowed: 0, blocked: 0, sandboxed: 0, approvalRequired: 0, avgRiskScore: 0 };
    }

    let allowed = 0;
    let blocked = 0;
    let sandboxed = 0;
    let approvalRequired = 0;
    let totalRisk = 0;

    for (const entry of this.entries) {
      if (entry.decision.allowed) allowed++;
      else blocked++;
      if (entry.decision.sandbox) sandboxed++;
      if (entry.decision.requiresApproval) approvalRequired++;
      totalRisk += entry.decision.riskScore;
    }

    return {
      totalRequests: total,
      allowed,
      blocked,
      sandboxed,
      approvalRequired,
      avgRiskScore: totalRisk / total,
    };
  }

  private hashObject(obj: unknown): string {
    const serialized = JSON.stringify(obj, Object.keys(obj as Record<string, unknown>).sort());
    return createHash('sha256').update(serialized).digest('hex');
  }

  private sign(data: string): string {
    return createHmac('sha256', this.secretKey).update(data).digest('hex');
  }

  private generateId(): string {
    return `audit_${Date.now()}_${randomBytes(8).toString('hex')}`;
  }

  private trimEntries(): void {
    while (this.entries.length > this.maxEntries) {
      this.entries.shift();
    }
  }
}
